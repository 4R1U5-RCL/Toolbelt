"""Conformance: this envelope must be byte-identical to the ones already in use.

There are now three implementations of the same signed envelope in the studio —
`packages/notify/src/client.mjs` (the canonical one, Node), `Packages/Poller`'s
`notify_webhook` sink (Python), and this package. Three implementations that
agree by inspection will not stay agreeing.

So the agreement is asserted, against the real files, on the real bytes. Both
tests **skip loudly** when their subject is absent rather than passing quietly:
a conformance test that silently does nothing is worse than no conformance test,
because it reports green.
"""

import json
import os
import subprocess
import unittest

import helpers  # noqa: F401  (path setup)

from telegram.seam import build_payload, build_request, serialise

CLIENT_MJS = "/studio/packages/notify/src/client.mjs"
POLLER_SINKS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Poller")

STAMP = 1_756_500_000_123
TOKEN = "conformance-token-000"
SECRET = "conformance-secret-00"

# Deliberately includes an emoji and a non-ASCII separator: those are exactly
# where two JSON serialisers diverge.
CASE = {
    "source": "poller",
    "message": "🟢 kaggle settled — 51.210",
    "kind": "complete",
    "summary": "challenger-2arm · ref 55881637",
    "meta": {"template": "poller.settled", "severity": "info"},
}


def _node_available() -> bool:
    if not os.path.isfile(CLIENT_MJS):
        return False
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return False
    return True


class TestAgainstClientMjs(unittest.TestCase):
    """The canonical Node implementation is the reference."""

    @unittest.skipUnless(_node_available(),
                         "node or packages/notify/src/client.mjs unavailable — "
                         "conformance against the canonical envelope NOT PROVEN here")
    def test_body_and_signature_match(self):
        script = (
            "import {{ buildRequest }} from {0};\n"
            "const out = buildRequest({1}, {2});\n"
            "process.stdout.write(JSON.stringify({{body: out.body, headers: out.headers}}));\n"
        ).format(
            json.dumps(CLIENT_MJS),
            json.dumps(dict(CASE, ts=STAMP)),
            json.dumps({"token": TOKEN, "secret": SECRET}),
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        reference = json.loads(completed.stdout)

        payload = build_payload(timestamp_ms=STAMP, **CASE)
        prepared = build_request(payload, token=TOKEN, secret=SECRET, timestamp_ms=STAMP)

        self.assertEqual(prepared["body"], reference["body"],
                         "envelope bytes diverged from client.mjs")
        self.assertEqual(prepared["signature"], reference["headers"]["x-notify-signature"],
                         "signature diverged from client.mjs")

    @unittest.skipUnless(_node_available(), "node unavailable")
    def test_json_stringify_and_serialise_agree_on_awkward_values(self):
        """The cases where two JSON serialisers actually differ."""
        for value in ({"m": "🟢"}, {"m": "a—b"}, {"m": ""}, {"m": None},
                      {"nested": {"a": [1, 2, {"b": "é"}]}}, {"m": 'quote " and \\ slash'},
                      {"m": "tab\there\nnewline"}):
            completed = subprocess.run(
                ["node", "-e",
                 "process.stdout.write(JSON.stringify({0}))".format(json.dumps(value))],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(serialise(value), completed.stdout,
                             "serialisation diverged for {0!r}".format(value))


class TestAgainstPollerSink(unittest.TestCase):
    """The Poller ships its own copy of this envelope and must stay in step.

    The two packages are deliberately not coupled — the Poller's rule is no
    paths into other packages, so it keeps its own implementation. This test is
    what makes that duplication safe instead of a drift waiting to happen.
    """

    @unittest.skipUnless(os.path.isdir(POLLER_SINKS),
                         "Packages/Poller not present — cross-package conformance "
                         "NOT PROVEN here")
    def test_envelope_bytes_match_the_poller_sink(self):
        import sys
        sys.path.insert(0, POLLER_SINKS)
        try:
            from poller.sinks import NotifyWebhookSink
        finally:
            sys.path.remove(POLLER_SINKS)

        sink = NotifyWebhookSink.__new__(NotifyWebhookSink)
        sink.source_name = CASE["source"]
        body_bytes, headers = sink.build_request(
            title=CASE["message"], summary=CASE["summary"], severity="info",
            meta={"template": "poller.settled"},
            token=TOKEN, secret=SECRET, timestamp_ms=STAMP)

        # The Poller derives `kind` from severity and folds severity into meta;
        # this package takes both explicitly. Build the same logical envelope so
        # the comparison is about *serialisation*, which is the shared contract,
        # not about each package's own field policy.
        payload = build_payload(
            source=CASE["source"], message=CASE["message"], kind="complete",
            summary=CASE["summary"], meta={"template": "poller.settled", "severity": "info"},
            timestamp_ms=STAMP)
        prepared = build_request(payload, token=TOKEN, secret=SECRET, timestamp_ms=STAMP)

        self.assertEqual(prepared["body"], body_bytes.decode("utf-8"))
        self.assertEqual(prepared["headers"]["x-notify-signature"],
                         headers["x-notify-signature"])
        self.assertEqual(prepared["headers"]["Content-Type"], headers["Content-Type"])

    @unittest.skipUnless(os.path.isdir(POLLER_SINKS), "Packages/Poller not present")
    def test_this_package_sends_headers_the_poller_does_not(self):
        """A superset, not a difference — and worth stating explicitly.

        The Poller sends only the `x-notify-*` family. This package also sends
        `x-n8n-*`, because the deployed receiver accepts either and other studio
        callers use the other name. Both are accepted; neither is wrong.
        """
        payload = build_payload(source="s", message="m", timestamp_ms=STAMP)
        headers = build_request(payload, TOKEN, SECRET, STAMP)["headers"]
        self.assertIn("x-notify-signature", headers)
        self.assertIn("x-n8n-signature", headers)
        self.assertEqual(headers["x-notify-signature"], headers["x-n8n-signature"])


if __name__ == "__main__":
    unittest.main()
