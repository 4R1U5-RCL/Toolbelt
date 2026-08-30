"""The envelope, the signature, and the fail-soft contract."""

import json
import unittest

import helpers
from helpers import FakeClock, FakeResolver, RecordingClient, ok

from telegram.errors import ConfigError
from telegram.http import HttpFatal, HttpTransient
from telegram.seam import (NOTIFY_SCHEMA, SIG_HEADERS, TS_HEADERS, TOKEN_HEADER,
                           Seam, build_payload, build_request, iso_ms, serialise,
                           sign, verify_response)

WIRED = {"NOTIFY_WEBHOOK_URL": "https://n8n.test/webhook/notification-fanout",
         "NOTIFY_TOKEN": "token-abcdef123456"}
STAMP = 1_756_500_000_123


class TestTimestamp(unittest.TestCase):
    """`sentAt` is inside the signed bytes, so its format is load-bearing."""

    def test_matches_javascript_toisostring(self):
        self.assertEqual(iso_ms(STAMP), "2025-08-29T20:40:00.123Z")

    def test_always_three_fractional_digits(self):
        self.assertTrue(iso_ms(1_756_500_000_000).endswith(".000Z"))

    def test_differs_from_python_default_isoformat(self):
        # Python gives six digits and +00:00; using it would silently break
        # every signature.
        import datetime as dt
        native = dt.datetime.fromtimestamp(STAMP / 1000, tz=dt.timezone.utc).isoformat()
        self.assertNotEqual(native, iso_ms(STAMP))


class TestPayload(unittest.TestCase):
    def test_field_order_matches_client_mjs(self):
        payload = build_payload(source="s", message="m", timestamp_ms=STAMP)
        self.assertEqual(list(payload),
                         ["schema", "source", "kind", "message", "summary",
                          "event", "meta", "sentAt"])

    def test_schema_is_the_shared_one(self):
        self.assertEqual(build_payload("s", "m", timestamp_ms=STAMP)["schema"],
                         NOTIFY_SCHEMA)

    def test_optional_fields_are_absent_unless_given(self):
        # Their absence is what keeps a default send byte-identical to client.mjs.
        payload = build_payload("s", "m", timestamp_ms=STAMP)
        self.assertNotIn("chat_id", payload)
        self.assertNotIn("request_id", payload)

    def test_optional_fields_append_at_the_end(self):
        payload = build_payload("s", "m", timestamp_ms=STAMP,
                                chat_id="99", request_id="abc")
        self.assertEqual(list(payload)[-2:], ["chat_id", "request_id"])

    def test_defaults_match_the_javascript_nullish_fallbacks(self):
        payload = build_payload("s", "", timestamp_ms=STAMP)
        self.assertIsNone(payload["kind"])
        self.assertIsNone(payload["summary"])
        self.assertIsNone(payload["event"])
        self.assertEqual(payload["meta"], {})


class TestSerialise(unittest.TestCase):
    def test_no_whitespace_padding(self):
        body = serialise({"a": 1, "b": {"c": 2}})
        self.assertEqual(body, '{"a":1,"b":{"c":2}}')

    def test_non_ascii_is_not_escaped(self):
        # JSON.stringify emits the character; escaping it changes the bytes and
        # therefore the signature.
        self.assertIn("🟢", serialise({"m": "🟢"}))
        self.assertNotIn("\\ud83d", serialise({"m": "🟢"}))


class TestSignature(unittest.TestCase):
    def test_is_deterministic(self):
        self.assertEqual(sign("1.body", "secret"), sign("1.body", "secret"))

    def test_covers_the_timestamp_as_well_as_the_body(self):
        # Otherwise a captured body could be replayed with a fresh timestamp.
        self.assertNotEqual(sign("1.body", "s"), sign("2.body", "s"))

    def test_known_vector(self):
        self.assertEqual(
            sign("1756500000123.{}", "shared-secret"),
            __import__("hmac").new(b"shared-secret",
                                   b"1756500000123.{}",
                                   __import__("hashlib").sha256).hexdigest())


class TestBuildRequest(unittest.TestCase):
    def setUp(self):
        payload = build_payload("poller", "hello", timestamp_ms=STAMP)
        self.prepared = build_request(payload, token="tok-123456", secret="sec-123456",
                                      timestamp_ms=STAMP)

    def test_sends_both_signature_header_families(self):
        # The studio has both conventions in the wild and the receiver accepts
        # either; sending both is what makes this seam work with all of them.
        for name in SIG_HEADERS:
            self.assertEqual(self.prepared["headers"][name], self.prepared["signature"])

    def test_sends_both_timestamp_header_families(self):
        for name in TS_HEADERS:
            self.assertEqual(self.prepared["headers"][name], str(STAMP))

    def test_content_type_has_no_charset_suffix(self):
        # client.mjs sends exactly "application/json".
        self.assertEqual(self.prepared["headers"]["Content-Type"], "application/json")

    def test_token_header_is_present(self):
        self.assertEqual(self.prepared["headers"][TOKEN_HEADER], "tok-123456")

    def test_secret_falls_back_to_the_token(self):
        payload = build_payload("s", "m", timestamp_ms=STAMP)
        with_secret = build_request(payload, "tok-123456", None, STAMP)
        explicit = build_request(payload, "tok-123456", "tok-123456", STAMP)
        self.assertEqual(with_secret["signature"], explicit["signature"])

    def test_is_pure(self):
        payload = build_payload("s", "m", timestamp_ms=STAMP)
        first = build_request(payload, "t-123456", "s-123456", STAMP)
        second = build_request(payload, "t-123456", "s-123456", STAMP)
        self.assertEqual(first["body"], second["body"])
        self.assertEqual(first["signature"], second["signature"])


class TestSend(unittest.TestCase):
    def _seam(self, responses=None, values=None, **kwargs):
        return Seam(FakeResolver(values if values is not None else WIRED),
                    client=RecordingClient(responses), clock=FakeClock(STAMP), **kwargs)

    def test_accepted_send(self):
        seam = self._seam([ok()])
        result = seam.send("hello")
        self.assertTrue(result.accepted)
        self.assertFalse(result.delivered)  # acceptance is not delivery (TG-02)
        self.assertIn("not yet proof of delivery", result.note)

    def test_body_is_the_signed_bytes(self):
        seam = self._seam([ok()])
        seam.send("hello")
        sent = json.loads(seam.client.last["body"].decode("utf-8"))
        self.assertEqual(sent["message"], "hello")
        self.assertEqual(sent["schema"], NOTIFY_SCHEMA)

    def test_a_transport_error_does_not_raise(self):
        # A notification is not the work: failing to report must never take down
        # the thing that was reporting.
        seam = self._seam([HttpTransient("connection reset")])
        result = seam.send("hello")
        self.assertFalse(result.accepted)
        self.assertIn("unreachable", result.note)

    def test_a_rejection_does_not_raise(self):
        seam = self._seam([HttpFatal("HTTP 401: nope", status=401)])
        result = seam.send("hello")
        self.assertFalse(result.accepted)
        self.assertEqual(result.status, 401)
        self.assertIn("rejected", result.note)

    def test_missing_configuration_is_reported_not_raised(self):
        seam = self._seam([ok()], values={})
        result = seam.send("hello")
        self.assertFalse(result.accepted)
        self.assertIn("NOT WIRED", result.note)

    def test_dry_run_sends_nothing(self):
        seam = self._seam([ok()], dry_run=True)
        result = seam.send("hello")
        self.assertTrue(result.accepted)
        self.assertEqual(seam.client.calls, [])
        self.assertIn("dry run", result.note)

    def test_correlation_id_is_present_by_default(self):
        seam = self._seam([ok()])
        self.assertTrue(seam.send("hello").request_id)

    def test_correlation_can_be_switched_off_for_byte_parity(self):
        seam = self._seam([ok()])
        seam.send("hello", correlate=False)
        self.assertNotIn("request_id", seam.client.last["body"].decode("utf-8"))

    def test_preflight_names_what_is_missing(self):
        seam = self._seam(values={"NOTIFY_TOKEN": "t-123456"})
        with self.assertRaises(ConfigError) as caught:
            seam.preflight()
        self.assertIn("NOTIFY_WEBHOOK_URL", str(caught.exception))

    def test_preflight_reports_names_never_values(self):
        seam = self._seam()
        rendered = json.dumps(seam.preflight())
        self.assertNotIn(WIRED["NOTIFY_TOKEN"], rendered)


class TestResponseSignature(unittest.TestCase):
    def test_valid_signature_verifies(self):
        body = b'{"ok":true,"request_id":"abc"}'
        response = ok(body, headers={"x-n8n-signature": sign(body.decode(), "sec-123456")})
        self.assertTrue(verify_response(response, "sec-123456"))

    def test_wrong_signature_is_reported_false(self):
        response = ok(b'{"ok":true}', headers={"x-n8n-signature": "deadbeef"})
        self.assertFalse(verify_response(response, "sec-123456"))

    def test_unsigned_response_is_none_not_false(self):
        # "Not signed" and "signed wrongly" are different facts.
        self.assertIsNone(verify_response(ok(b'{"ok":true}'), "sec-123456"))

    def test_a_mismatch_does_not_fail_the_send(self):
        # n8n re-serialises its own reply, so a spacing difference is not a
        # security event and must not turn an accepted send into a failure.
        seam = Seam(FakeResolver(WIRED),
                    client=RecordingClient([ok(b'{"ok": true}',
                                               headers={"x-n8n-signature": "nope"})]),
                    clock=FakeClock(STAMP))
        result = seam.send("hello")
        self.assertTrue(result.accepted)
        self.assertFalse(result.response_signature_ok)


if __name__ == "__main__":
    unittest.main()
