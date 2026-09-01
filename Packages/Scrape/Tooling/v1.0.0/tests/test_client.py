"""FirecrawlClient: request shape, auth header, and HTTP->error mapping."""

import unittest

from helpers import *  # noqa: F401,F403

from scrape.client import FirecrawlClient
from scrape.errors import ConfigError, EmptyContentError, FatalFetchError, TransientFetchError
from scrape.http import HttpFatal, HttpResponse, HttpTransient


class ClientTests(unittest.TestCase):
    def _client(self, *outcomes, **kw):
        http = FakeHttp(*outcomes)
        return FirecrawlClient(api_key="secret", http=http, **kw), http

    def test_request_shape_and_auth(self):
        client, http = self._client(json_response({"success": True, "data": ok_data()}))
        data = client.scrape("https://example.com")
        self.assertIn("markdown", data)
        url, payload, headers = http.calls[0]
        self.assertTrue(url.endswith("/scrape"))
        self.assertEqual(payload, {"url": "https://example.com", "formats": ["markdown"]})
        self.assertEqual(headers["Authorization"], "Bearer secret")

    def test_custom_formats_are_sent(self):
        client, http = self._client(json_response({"data": ok_data()}), formats=["markdown", "links"])
        client.scrape("https://example.com")
        self.assertEqual(http.calls[0][1]["formats"], ["markdown", "links"])

    def test_http_fatal_maps_to_fatal_fetch(self):
        client, _ = self._client(HttpFatal("HTTP 401 — bad key"))
        self.assertRaises(FatalFetchError, client.scrape, "https://example.com")

    def test_http_transient_maps_to_transient_fetch(self):
        client, _ = self._client(HttpTransient("HTTP 503"))
        self.assertRaises(TransientFetchError, client.scrape, "https://example.com")

    def test_missing_markdown_is_empty_content(self):
        client, _ = self._client(json_response({"data": {"markdown": "   "}}))
        self.assertRaises(EmptyContentError, client.scrape, "https://example.com")

    def test_no_data_key_is_empty_content(self):
        client, _ = self._client(json_response({"success": False, "error": "blocked"}))
        self.assertRaises(EmptyContentError, client.scrape, "https://example.com")

    def test_non_json_body_maps_to_fatal(self):
        client, _ = self._client(HttpResponse(200, "<html>login</html>"))
        self.assertRaises(FatalFetchError, client.scrape, "https://example.com")

    def test_bad_scheme_is_fatal(self):
        client, _ = self._client()
        self.assertRaises(FatalFetchError, client.scrape, "ftp://example.com/file")

    def test_missing_api_key_is_config_error(self):
        self.assertRaises(ConfigError, FirecrawlClient, api_key="")


if __name__ == "__main__":
    unittest.main()
