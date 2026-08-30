"""The token-budget chunker: bounds, hard-split, overlap, indices."""

import unittest

from helpers import *  # noqa: F401,F403

from scrape.chunk import chunk_markdown


class ChunkTests(unittest.TestCase):
    def test_empty_returns_no_chunks(self):
        self.assertEqual(chunk_markdown(""), [])
        self.assertEqual(chunk_markdown("   \n\n  "), [])

    def test_small_doc_is_one_chunk(self):
        chunks = chunk_markdown("# Heading\n\nA short paragraph.", max_tokens=1500)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].index, 0)

    def test_multiple_paragraphs_respect_the_budget(self):
        md = "\n\n".join(["para number {0} here".format(i) for i in range(4)])
        chunks = chunk_markdown(md, max_tokens=5)  # ~20 chars/chunk
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(c.tokens <= 5 for c in chunks))
        self.assertEqual([c.index for c in chunks], list(range(len(chunks))))

    def test_oversized_block_is_hard_split(self):
        chunks = chunk_markdown("x" * 100, max_tokens=5)  # step = 20 chars
        self.assertEqual(len(chunks), 5)
        self.assertTrue(all(c.tokens <= 5 for c in chunks))

    def test_overlap_shares_the_previous_tail(self):
        md = "aaaa aaaa aaaa\n\nbbbb bbbb bbbb"
        chunks = chunk_markdown(md, max_tokens=4, overlap=2)
        self.assertGreaterEqual(len(chunks), 2)
        tail = chunks[0].text[-8:]  # overlap*4 chars
        self.assertTrue(chunks[1].text.startswith(tail))


if __name__ == "__main__":
    unittest.main()
