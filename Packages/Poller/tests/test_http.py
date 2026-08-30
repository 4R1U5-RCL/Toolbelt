import email.message
import io
import unittest
import urllib.error

from helpers import *  # noqa: F401,F403
from poller import http as http_module
from poller.http import HttpClient, HttpFatal, HttpTransient


class _FakeResponse(io.BytesIO):
    def __init__(self, body: bytes, status: int = 200):
        super().__init__(body)
        self.status = status
        self.headers = email.message.Message()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _http_error(code: int, body: bytes = b"nope", retry_after=None):
    headers = email.message.Message()
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("https://x/y", code, "err", headers, io.BytesIO(body))


class HttpClientTests(unittest.TestCase):
    def setUp(self):
        self.slept = []
        self.client = HttpClient(
            retries=3, sleep=self.slept.append, rand=lambda: 1.0, backoff_base=1.0, backoff_cap=8.0
        )
        self._real_urlopen = http_module.urllib.request.urlopen

    def tearDown(self):
        http_module.urllib.request.urlopen = self._real_urlopen

    def _responses(self, *sequence):
        queue = list(sequence)

        def fake_urlopen(request, timeout=None):
            step = queue.pop(0) if len(queue) > 1 else queue[0]
            if isinstance(step, Exception):
                raise step
            return _FakeResponse(step)

        http_module.urllib.request.urlopen = fake_urlopen

    def test_parses_json(self):
        self._responses(b'{"a": 1}')
        self.assertEqual(self.client.get_json("https://example.com/x"), {"a": 1})

    def test_retries_transient_then_succeeds(self):
        self._responses(_http_error(503), _http_error(503), b'{"ok": true}')
        self.assertEqual(self.client.get_json("https://example.com/x"), {"ok": True})
        self.assertEqual(len(self.slept), 2)
        # Full-jitter exponential: rand() is pinned to 1.0 so the window is exact.
        self.assertEqual(self.slept, [1.0, 2.0])

    def test_backoff_is_capped(self):
        client = HttpClient(retries=6, sleep=self.slept.append, rand=lambda: 1.0,
                            backoff_base=1.0, backoff_cap=4.0)
        self._responses(_http_error(500))
        with self.assertRaises(HttpTransient):
            client.get_json("https://example.com/x")
        self.assertEqual(max(self.slept), 4.0)

    def test_retry_after_raises_the_floor(self):
        self._responses(_http_error(429, retry_after=30), b"{}")
        self.client.get_json("https://example.com/x")
        self.assertEqual(self.slept, [8.0])  # capped at backoff_cap, not the raw 30

    def test_auth_failure_is_fatal_and_not_retried(self):
        self._responses(_http_error(401))
        with self.assertRaises(HttpFatal):
            self.client.get_json("https://example.com/x")
        self.assertEqual(self.slept, [])  # the whole point: no silent 12-hour retry loop

    def test_not_found_is_fatal(self):
        self._responses(_http_error(404))
        with self.assertRaises(HttpFatal):
            self.client.get_json("https://example.com/x")

    def test_transport_errors_are_transient(self):
        self._responses(urllib.error.URLError("connection reset"))
        with self.assertRaises(HttpTransient):
            self.client.get_json("https://example.com/x")
        self.assertEqual(len(self.slept), 3)

    def test_html_body_with_200_is_fatal_not_silently_ignored(self):
        self._responses(b"<html>login</html>")
        with self.assertRaises(HttpFatal):
            self.client.get_json("https://example.com/x")

    def test_plain_http_is_refused_by_default(self):
        with self.assertRaises(HttpFatal):
            self.client.get_json("http://example.com/x")

    def test_plain_http_allowed_when_explicitly_opted_in(self):
        client = HttpClient(allow_insecure=True, sleep=self.slept.append)
        self._responses(b"{}")
        self.assertEqual(client.get_json("http://example.com/x"), {})

    def test_query_params_are_appended(self):
        captured = {}

        def fake_urlopen(request, timeout=None):
            captured["url"] = request.full_url
            return _FakeResponse(b"{}")

        http_module.urllib.request.urlopen = fake_urlopen
        self.client.get_json("https://example.com/x", params={"a": "1", "b": "2"})
        self.assertEqual(captured["url"], "https://example.com/x?a=1&b=2")


if __name__ == "__main__":
    unittest.main()
