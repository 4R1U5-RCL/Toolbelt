"""The orchestration: single scrape, chunking, and batch-survives-a-bad-page."""

import unittest

from helpers import *  # noqa: F401,F403

from scrape.config import Config
from scrape.engine import scrape_many, scrape_url
from scrape.errors import FatalFetchError


class EngineTests(unittest.TestCase):
    def test_scrape_url_returns_document(self):
        doc = scrape_url("https://u", FakeBackend(ok_data(title="T")), Config())
        self.assertEqual(doc.title, "T")
        self.assertTrue(doc.markdown)
        self.assertEqual(doc.chunks, [])

    def test_scrape_url_chunks_when_configured(self):
        big = ok_data(markdown="\n\n".join("paragraph {0}".format(i) for i in range(6)))
        doc = scrape_url("https://u", FakeBackend(big), Config(chunk=True, max_tokens=3))
        self.assertGreater(len(doc.chunks), 1)

    def test_batch_continues_past_a_failure(self):
        backend = FakeBackend(ok_data(), FatalFetchError("404"), ok_data())
        outs = scrape_many(["https://a", "https://b", "https://c"], backend, Config())
        self.assertEqual([o.ok for o in outs], [True, False, True])
        self.assertIsNotNone(outs[1].error)

    def test_batch_stop_halts_on_first_failure(self):
        backend = FakeBackend(ok_data(), FatalFetchError("404"), ok_data())
        outs = scrape_many(["https://a", "https://b", "https://c"], backend, Config(), on_error="stop")
        self.assertEqual(len(outs), 2)
        self.assertFalse(outs[1].ok)

    def test_blank_urls_are_skipped(self):
        outs = scrape_many(["https://a", "", "   ", "https://b"], FakeBackend(ok_data(), ok_data()), Config())
        self.assertEqual([o.url for o in outs], ["https://a", "https://b"])


if __name__ == "__main__":
    unittest.main()
