import json
import os
import tempfile
import unittest

from helpers import *  # noqa: F401,F403
from poller.envfile import EnvResolver
from poller.errors import ConfigError, FatalSinkError, SinkError
from poller.http import HttpFatal, HttpResponse, HttpTransient
from poller.model import Event, EventReason
from poller.sinks import (CommandSink, FileSink, NotifyWebhookSink, SlackSink, build_sinks,
                          _iso_millis)

# Frozen from the reference implementation (packages/notify/src/client.mjs) via
# `node -e 'buildRequest(...)'`. If this vector ever fails, the Python envelope
# has drifted from the Node one and the n8n workflow will reject the signature.
NODE_VECTOR = {
    "ts": 1756540800123,
    "token": "TESTTOKEN",
    "secret": "TESTSECRET",
    "source": "kaggle-poller",
    "message": "Kaggle settled: 51.210",
    "summary": "ref 55881637 · unicode ✓ · quote \" · backslash \\\\",
    "meta": {"reason": "settled", "key": "55881637"},
    "severity": "info",
    "body": ('{"schema":"studio.notify.v1","source":"kaggle-poller","kind":"complete",'
             '"message":"Kaggle settled: 51.210",'
             '"summary":"ref 55881637 · unicode ✓ · quote \\" · backslash \\\\\\\\",'
             '"event":null,"meta":{"reason":"settled","key":"55881637","severity":"info"},'
             '"sentAt":"2025-08-30T08:00:00.123Z"}'),
    "signature": "020e51f3e46d8369bbe88b201975c5b08ed8ce6a8e84057c3dcb58cde0eeaa42",
}


class StubHttp:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def request(self, method, url, headers=None, body=None, params=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "body": body})
        if self.error:
            raise self.error
        return self.response or HttpResponse(200, b"{}")

    def post_json(self, url, payload, headers=None):
        self.calls.append({"method": "POST", "url": url, "payload": payload,
                           "headers": headers or {}})
        if self.error:
            raise self.error
        return self.response or HttpResponse(200, b'{"ok": true}')


def event(reason=EventReason.SETTLED, title="T", body="B", severity="info"):
    return Event(reason=reason, dedup_key="k:settled", title=title, body=body,
                 severity=severity, item=settled("K1"))


def resolver(**environ):
    return EnvResolver(None, environ=environ)


class NotifyWebhookSinkTests(unittest.TestCase):
    def sink(self, **config):
        return NotifyWebhookSink(dict({"type": "notify_webhook"}, **config),
                                 resolver(NOTIFY_WEBHOOK_URL="https://hooks.example/x",
                                          NOTIFY_TOKEN="tok123456"),
                                 client=StubHttp())

    def test_envelope_is_byte_identical_to_the_node_client(self):
        sink = self.sink(source=NODE_VECTOR["source"])
        body, headers = sink.build_request(
            title=NODE_VECTOR["message"], summary=NODE_VECTOR["summary"],
            severity=NODE_VECTOR["severity"], meta=dict(NODE_VECTOR["meta"]),
            token=NODE_VECTOR["token"], secret=NODE_VECTOR["secret"],
            timestamp_ms=NODE_VECTOR["ts"],
        )
        self.assertEqual(body.decode("utf-8"), NODE_VECTOR["body"])
        self.assertEqual(headers["x-notify-signature"], NODE_VECTOR["signature"])
        self.assertEqual(headers["x-notify-timestamp"], str(NODE_VECTOR["ts"]))
        self.assertEqual(headers["X-Notify-Token"], NODE_VECTOR["token"])

    def test_signature_covers_the_body_so_tampering_is_detectable(self):
        sink = self.sink()
        _, first = sink.build_request("a", "b", "info", {}, "tok", "sec", 1)
        _, second = sink.build_request("a", "b!", "info", {}, "tok", "sec", 1)
        self.assertNotEqual(first["x-notify-signature"], second["x-notify-signature"])

    def test_severity_maps_onto_the_workflow_kinds(self):
        sink = self.sink()
        for severity, kind in (("info", "complete"), ("warn", "attention"), ("error", "alert")):
            body, _ = sink.build_request("t", "s", severity, {}, "tok", "sec", 1)
            self.assertEqual(json.loads(body)["kind"], kind)

    def test_secret_defaults_to_the_token_when_absent(self):
        sink = NotifyWebhookSink({"type": "notify_webhook"},
                                 resolver(NOTIFY_WEBHOOK_URL="https://hooks.example/x",
                                          NOTIFY_TOKEN="tok123456"),
                                 client=StubHttp())
        sink.send("msg", event())  # must not raise for a missing NOTIFY_SECRET

    def test_transport_failures_keep_their_classification(self):
        for error, expected in ((HttpFatal("401"), FatalSinkError), (HttpTransient("timeout"), SinkError)):
            sink = NotifyWebhookSink({"type": "notify_webhook"},
                                     resolver(NOTIFY_WEBHOOK_URL="https://hooks.example/x",
                                              NOTIFY_TOKEN="tok123456"),
                                     client=StubHttp(error=error))
            with self.assertRaises(expected):
                sink.send("msg", event())

    def test_iso_millis_matches_javascript(self):
        self.assertEqual(_iso_millis(1756540800123), "2025-08-30T08:00:00.123Z")
        self.assertEqual(_iso_millis(1756540800000), "2025-08-30T08:00:00.000Z")


class SlackSinkTests(unittest.TestCase):
    def sink(self, response=None, error=None):
        return SlackSink({"type": "slack", "channel": "C123"},
                         resolver(SLACK_BOT_TOKEN="xoxb-123456"),
                         client=StubHttp(response=response, error=error))

    def test_posts_the_rendered_message_to_the_channel(self):
        sink = self.sink()
        sink.deliver(event(title="Settled", body="score 51.210"))
        payload = sink.client.calls[0]["payload"]
        self.assertEqual(payload["channel"], "C123")
        self.assertIn("51.210", payload["text"])

    def test_ok_false_with_a_config_error_is_fatal(self):
        sink = self.sink(response=HttpResponse(200, b'{"ok": false, "error": "invalid_auth"}'))
        with self.assertRaises(FatalSinkError):
            sink.send("m", event())

    def test_ok_false_with_a_rate_limit_is_retryable(self):
        sink = self.sink(response=HttpResponse(200, b'{"ok": false, "error": "ratelimited"}'))
        with self.assertRaises(SinkError):
            sink.send("m", event())

    def test_not_in_channel_is_fatal_because_a_human_must_invite_the_bot(self):
        sink = self.sink(response=HttpResponse(200, b'{"ok": false, "error": "not_in_channel"}'))
        with self.assertRaises(FatalSinkError):
            sink.send("m", event())


class FileSinkTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_writes_and_creates_missing_directories(self):
        path = os.path.join(self.dir, "nested", "out-{key}.md")
        sink = FileSink({"type": "file", "path": path}, resolver())
        sink.deliver(event(title="Settled", body="score 51.210"))
        written = os.path.join(self.dir, "nested", "out-K1.md")
        with open(written, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("51.210", content)
        self.assertIn("settled", content)

    def test_appends_rather_than_overwriting(self):
        path = os.path.join(self.dir, "log.md")
        sink = FileSink({"type": "file", "path": path}, resolver())
        sink.deliver(event(body="first"))
        sink.deliver(event(body="second"))
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("first", content)
        self.assertIn("second", content)

    def test_path_is_required(self):
        with self.assertRaises(ConfigError):
            FileSink({"type": "file"}, resolver())


class CommandSinkTests(unittest.TestCase):
    def test_message_arrives_on_stdin_not_in_argv(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as handle:
            handle.write("#!/bin/sh\ncat > \"$1\"\n")
            script = handle.name
        os.chmod(script, 0o755)
        out = script + ".out"
        sink = CommandSink({"type": "command", "argv": ["/bin/sh", script, out]}, resolver())
        sink.deliver(event(title="Hello", body="world"))
        with open(out, encoding="utf-8") as handle:
            self.assertIn("world", handle.read())

    def test_nonzero_exit_is_retryable(self):
        sink = CommandSink({"type": "command", "argv": ["/bin/sh", "-c", "exit 3"]}, resolver())
        with self.assertRaises(SinkError):
            sink.send("m", event())

    def test_missing_binary_is_fatal(self):
        sink = CommandSink({"type": "command", "argv": ["/nonexistent/binary"]}, resolver())
        with self.assertRaises(FatalSinkError):
            sink.send("m", event())

    def test_argv_is_required(self):
        with self.assertRaises(ConfigError):
            CommandSink({"type": "command"}, resolver())


class SinkPlumbingTests(unittest.TestCase):
    def test_reasons_filter_selects_events(self):
        sink = RecordingSink("r", reasons=[EventReason.FAILED])
        self.assertFalse(sink.accepts(event(reason=EventReason.SETTLED)))
        self.assertTrue(sink.accepts(event(reason=EventReason.FAILED)))

    def test_no_filter_accepts_everything(self):
        self.assertTrue(RecordingSink("r").accepts(event(reason=EventReason.HEARTBEAT)))

    def test_dry_run_renders_but_does_not_send(self):
        sink = RecordingSink("r")
        sink.dry_run = True
        sink.deliver(event())
        self.assertEqual(sink.messages, [])

    def test_build_sinks_makes_names_unique(self):
        sinks = build_sinks([{"type": "stdout"}, {"type": "stdout"}, {"type": "stdout"}], resolver())
        self.assertEqual([s.name for s in sinks], ["stdout", "stdout-2", "stdout-3"])

    def test_build_sinks_rejects_an_empty_list(self):
        with self.assertRaises(ConfigError):
            build_sinks([], resolver())

    def test_build_sinks_rejects_unknown_types(self):
        with self.assertRaises(ConfigError) as ctx:
            build_sinks([{"type": "smoke-signal"}], resolver())
        self.assertIn("slack", str(ctx.exception))

    def test_default_template_carries_title_and_body(self):
        sink = RecordingSink("r")
        sink.deliver(event(title="Settled: x", body="score 1.0"))
        self.assertEqual(sink.messages, ["Settled: x\nscore 1.0"])


if __name__ == "__main__":
    unittest.main()


class FileSinkPathSafetyTests(unittest.TestCase):
    """An item key is whatever the watched API says it is, and it is interpolated
    into a filesystem path."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def test_a_traversing_key_cannot_escape_the_configured_directory(self):
        sink = FileSink({"type": "file", "path": os.path.join(self.dir, "out-{key}.md")},
                        resolver())
        evil = Event(reason=EventReason.SETTLED, dedup_key="x", title="t", body="b",
                     item=item("../../etc/passwd"))
        sink.deliver(evil)
        written = os.listdir(self.dir)
        self.assertEqual(len(written), 1)
        self.assertNotIn("..", written[0])
        self.assertTrue(written[0].startswith("out-"))

    def test_an_empty_key_still_produces_a_usable_filename(self):
        sink = FileSink({"type": "file", "path": os.path.join(self.dir, "{key}.md")}, resolver())
        sink.deliver(Event(reason=EventReason.SETTLED, dedup_key="x", title="t", body="b",
                           item=item("///")))
        self.assertEqual(os.listdir(self.dir), ["unnamed.md"])
