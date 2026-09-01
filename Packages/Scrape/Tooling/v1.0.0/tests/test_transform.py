"""The translate layer: token estimate, markdown cleaning, truncation, mapping."""

import unittest

from helpers import *  # noqa: F401,F403

from scrape.errors import EmptyContentError
from scrape.transform import clean_markdown, estimate_tokens, to_document, truncate_to_max_chars


class TransformTests(unittest.TestCase):
    def test_estimate_tokens(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("abcd"), 1)
        self.assertEqual(estimate_tokens("a" * 400), 100)

    def test_clean_collapses_blanks_and_trailing_space(self):
        dirty = "# H\r\n\r\n\r\n\r\nPara.   \n\n\n\nTail.\t\n"
        clean = clean_markdown(dirty)
        self.assertNotIn("\r", clean)
        self.assertNotIn("\n\n\n", clean)          # never more than one blank line
        self.assertNotIn("   \n", clean)           # no trailing spaces
        self.assertTrue(clean.endswith("\n"))

    def test_truncate(self):
        text, cut, orig = truncate_to_max_chars("abcdef", 4)
        self.assertEqual((text, cut, orig), ("abcd", True, 6))
        text, cut, orig = truncate_to_max_chars("ab", 4)
        self.assertEqual((text, cut, orig), ("ab", False, 2))

    def test_to_document_maps_fields(self):
        doc = to_document(ok_data(title="T", status=201, links=["https://a"]), "https://u")
        self.assertEqual(doc.url, "https://u")
        self.assertEqual(doc.title, "T")
        self.assertEqual(doc.source_status, 201)
        self.assertEqual(doc.links, ["https://a"])
        self.assertFalse(doc.truncated)

    def test_to_document_cleans_by_default_and_can_skip(self):
        raw = ok_data(markdown="# H\n\n\n\nBody.\n")
        cleaned = to_document(dict(raw), "https://u", clean=True)
        self.assertNotIn("\n\n\n", cleaned.markdown)
        uncleaned = to_document(dict(raw), "https://u", clean=False)
        self.assertIn("\n\n\n", uncleaned.markdown)

    def test_to_document_truncates_and_flags(self):
        doc = to_document(ok_data(markdown="x" * 100), "https://u", max_chars=10)
        self.assertTrue(doc.truncated)
        self.assertEqual(doc.original_chars, len("x" * 100 + "\n"))  # clean adds trailing newline
        self.assertEqual(len(doc.markdown), 10)

    def test_empty_markdown_raises(self):
        self.assertRaises(EmptyContentError, to_document, {"markdown": "   "}, "https://u")
        self.assertRaises(EmptyContentError, to_document, {"metadata": {}}, "https://u")


if __name__ == "__main__":
    unittest.main()
