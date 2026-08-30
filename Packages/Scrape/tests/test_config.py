"""Config loading: defaults, validation, clamping, and honest key resolution."""

import os
import tempfile
import unittest

from helpers import *  # noqa: F401,F403

from scrape.config import MAX_CHARS_CAP, Config, from_dict, load_config, resolve_api_key
from scrape.errors import ConfigError


class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        c = from_dict({})
        self.assertEqual(c.backend, "firecrawl")
        self.assertEqual(c.formats, ["markdown"])
        self.assertTrue(c.clean)
        self.assertEqual(c.out_format, "markdown")
        self.assertEqual(c.max_chars, MAX_CHARS_CAP)

    def test_unknown_key_is_ignored_not_fatal(self):
        c = from_dict({"bogus": 1, "clean": False})
        self.assertFalse(c.clean)
        self.assertFalse(hasattr(c, "bogus"))

    def test_markdown_is_forced_into_formats(self):
        self.assertEqual(from_dict({"formats": ["links"]}).formats, ["markdown", "links"])

    def test_invalid_out_format_raises(self):
        self.assertRaises(ConfigError, from_dict, {"out_format": "pdf"})

    def test_overlap_must_be_under_max_tokens(self):
        self.assertRaises(ConfigError, from_dict, {"overlap": 2000, "max_tokens": 1500})

    def test_max_chars_is_clamped(self):
        self.assertEqual(from_dict({"max_chars": 10 ** 9}).max_chars, MAX_CHARS_CAP)
        self.assertEqual(from_dict({"max_chars": 0}).max_chars, 1)

    def test_overrides_win(self):
        self.assertEqual(load_config(None, {"out_format": "json"}).out_format, "json")

    def test_missing_file_raises(self):
        self.assertRaises(ConfigError, load_config, "/no/such/config.json")

    def test_bad_json_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write("{ not json")
            path = fh.name
        try:
            self.assertRaises(ConfigError, load_config, path)
        finally:
            os.unlink(path)

    def test_non_object_json_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write("[1, 2, 3]")
            path = fh.name
        try:
            self.assertRaises(ConfigError, load_config, path)
        finally:
            os.unlink(path)

    def test_resolve_api_key(self):
        c = Config(api_key_env="MY_KEY")
        self.assertEqual(resolve_api_key(c, env={"MY_KEY": "abc123"}), "abc123")
        self.assertRaises(ConfigError, resolve_api_key, c, {})
        self.assertRaises(ConfigError, resolve_api_key, c, {"MY_KEY": "   "})


if __name__ == "__main__":
    unittest.main()
