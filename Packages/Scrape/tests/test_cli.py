"""The CLI: arg parsing, output routing, batch, and the honest missing-key path."""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

from helpers import *  # noqa: F401,F403

from scrape import cli


class CliTests(unittest.TestCase):
    def setUp(self):
        self._real_client = cli._client
        self._real_stdin = sys.stdin

    def tearDown(self):
        cli._client = self._real_client
        sys.stdin = self._real_stdin

    def _patch_client(self, *results):
        cli._client = lambda config: FakeBackend(*results)

    def test_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = cli.main(["version"])
        self.assertEqual(rc, 0)
        self.assertIn("scrape", out.getvalue())

    def test_url_writes_markdown_to_file(self):
        self._patch_client(ok_data(title="T"))
        with tempfile.NamedTemporaryFile("r", suffix=".md", delete=False) as fh:
            path = fh.name
        try:
            rc = cli.main(["url", "https://x", "--out", path])
            self.assertEqual(rc, 0)
            with open(path) as fh:
                body = fh.read()
            self.assertIn('url: "https://x"', body)
            self.assertIn("A body paragraph.", body)
        finally:
            os.unlink(path)

    def test_url_json_to_stdout(self):
        self._patch_client(ok_data())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = cli.main(["url", "https://x", "--format", "json"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out.getvalue())["url"], "https://x")

    def test_batch_from_stdin_json(self):
        self._patch_client(ok_data(), ok_data())
        sys.stdin = io.StringIO("https://a\n# a comment\nhttps://b\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = cli.main(["batch", "--format", "json"])
        self.assertEqual(rc, 0)
        rows = json.loads(out.getvalue())
        self.assertEqual([r["url"] for r in rows], ["https://a", "https://b"])

    def test_batch_no_urls_is_fatal(self):
        sys.stdin = io.StringIO("")
        rc = cli.main(["batch"])
        self.assertEqual(rc, 2)

    def test_missing_api_key_is_reported_not_crashed(self):
        # No client patch: exercises the real build_client -> resolve_api_key path.
        rc = cli.main(["url", "https://x", "--api-key-env", "DEFINITELY_UNSET_KEY_XYZ"])
        self.assertEqual(rc, 2)

    def test_bad_format_is_rejected_by_argparse(self):
        with self.assertRaises(SystemExit):
            cli.main(["url", "https://x", "--format", "pdf"])


if __name__ == "__main__":
    unittest.main()
