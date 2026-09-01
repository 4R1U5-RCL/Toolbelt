"""Rendering a Document to markdown (frontmatter), json, text, and chunks."""

import json
import unittest

from helpers import *  # noqa: F401,F403

from scrape.chunk import chunk_markdown
from scrape.render import render_chunks, render_document
from scrape.transform import to_document


def _doc():
    d = to_document(ok_data(markdown="# H\n\nBody text here.\n", title="A Title", links=["https://a"]), "https://u")
    d.chunks = chunk_markdown(d.markdown, max_tokens=2)
    return d


class RenderTests(unittest.TestCase):
    def test_markdown_has_frontmatter(self):
        out = render_document(_doc(), "markdown")
        self.assertTrue(out.startswith("---\n"))
        self.assertIn('url: "https://u"', out)
        self.assertIn('title: "A Title"', out)
        self.assertIn("# H", out)

    def test_json_round_trips(self):
        obj = json.loads(render_document(_doc(), "json"))
        self.assertEqual(obj["url"], "https://u")
        self.assertIn("markdown", obj)
        self.assertIn("chunks", obj)

    def test_text_is_bare_markdown(self):
        doc = _doc()
        self.assertEqual(render_document(doc, "text"), doc.markdown)
        self.assertNotIn("---\nurl:", render_document(doc, "text"))

    def test_unknown_format_raises(self):
        self.assertRaises(ValueError, render_document, _doc(), "pdf")

    def test_render_chunks_json_is_a_list(self):
        doc = _doc()
        arr = json.loads(render_chunks(doc, "json"))
        self.assertEqual(len(arr), len(doc.chunks))
        self.assertEqual(arr[0]["index"], 0)

    def test_render_chunks_markdown_has_headers(self):
        out = render_chunks(_doc(), "markdown")
        self.assertIn("chunk 1/", out)


if __name__ == "__main__":
    unittest.main()
