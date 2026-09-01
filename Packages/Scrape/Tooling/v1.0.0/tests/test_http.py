"""The retry/backoff policy and the JSON boundary, with urlopen monkeypatched."""

import io
import unittest
import urllib.error

from helpers import *  # noqa: F401,F403

import scrape.http as http_module
from scrape.http import HttpClient, HttpFatal, HttpResponse, HttpTransient


class _FakeResp:
    def __init__(self, status, body, headers=None):
        self.status = status
        self._body = body.encode("utf-8")
        self.headers = headers or {}

    def read(self):
        return self._body

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _http_error(code, body="", retry_after=None):
    hdrs = {}
    if retry_after is not None:
        hdrs["Retry-After"] = str(retry_after)
    return urllib.error.HTTPError("https://x", code, "err", hdrs, io.BytesIO(body.encode("utf-8")))


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.slept = []
        self.client = HttpClient(retries=3, backoff_base=2.0, sleep=self.slept.append, rand=lambda: 1.0)
        self._real_urlopen = http_module.urllib.request.urlopen

    def tearDown(self):
        http_module.urllib.request.urlopen = self._real_urlopen

    def _responses(self, *sequence):
        q = list(sequence)

        def fake(request, timeout=None):
            item = q.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        http_module.urllib.request.urlopen = fake

    def test_success_returns_parsed_response(self):
        self._responses(_FakeResp(200, '{"ok":true}'))
        r = self.client.post_json("https://api/x", {"a": 1})
        self.assertEqual(r.status, 200)
        self.assertEqual(r.json(), {"ok": True})
        self.assertEqual(self.slept, [])

    def test_401_is_fatal_and_never_retried(self):
        self._responses(_http_error(401, '{"error":"bad key"}'))
        with self.assertRaises(HttpFatal):
            self.client.get_json("https://api/x")
        self.assertEqual(self.slept, [])

    def test_429_retries_with_backoff_then_succeeds(self):
        self._responses(_http_error(429), _http_error(429), _FakeResp(200, "{}"))
        r = self.client.get_json("https://api/x")
        self.assertEqual(r.status, 200)
        self.assertEqual(self.slept, [2.0, 4.0])  # base**attempt * rand(=1.0)

    def test_retry_after_header_overrides_backoff(self):
        self._responses(_http_error(429, retry_after=5), _FakeResp(200, "{}"))
        self.client.get_json("https://api/x")
        self.assertEqual(self.slept, [5.0])

    def test_exhausted_retries_raise_transient(self):
        client = HttpClient(retries=2, backoff_base=2.0, sleep=self.slept.append, rand=lambda: 1.0)
        self._responses(_http_error(503), _http_error(503), _http_error(503))
        with self.assertRaises(HttpTransient):
            client.get_json("https://api/x")
        self.assertEqual(len(self.slept), 2)  # two backoffs, then give up

    def test_transport_error_is_transient(self):
        self._responses(urllib.error.URLError("boom"), _FakeResp(200, "{}"))
        self.client.get_json("https://api/x")
        self.assertEqual(len(self.slept), 1)

    def test_non_json_body_raises_fatal_on_parse(self):
        self.assertRaises(HttpFatal, HttpResponse(200, "<html>login</html>").json)

    def test_non_https_is_refused(self):
        with self.assertRaises(HttpFatal):
            self.client.get_json("http://insecure/x")

    def test_allow_insecure_permits_http(self):
        client = HttpClient(allow_insecure=True, sleep=self.slept.append, rand=lambda: 1.0)
        self._responses(_FakeResp(200, "{}"))
        self.assertEqual(client.get_json("http://insecure/x").status, 200)


if __name__ == "__main__":
    unittest.main()
