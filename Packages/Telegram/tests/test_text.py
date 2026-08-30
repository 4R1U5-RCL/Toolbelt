"""Plain-text safety: the measure, the conversion, and the chunking."""

import unittest

import helpers  # noqa: F401  (path setup)

from telegram.text import TELEGRAM_LIMIT, chunk, plain, tg_len, truncate


class TestLength(unittest.TestCase):
    """Telegram counts UTF-16 code units. Nothing else is the right measure."""

    def test_ascii_matches_len(self):
        self.assertEqual(tg_len("hello"), 5)

    def test_astral_emoji_counts_as_two(self):
        # "🟢" is one Python character and a surrogate pair to Telegram. A
        # message of 3000 of these is over the cap while len() says 3000.
        self.assertEqual(len("🟢"), 1)
        self.assertEqual(tg_len("🟢"), 2)

    def test_bmp_character_counts_as_one(self):
        self.assertEqual(tg_len("·"), 1)

    def test_emoji_heavy_message_is_over_the_limit_while_len_is_under(self):
        text = "🟢" * 2500
        self.assertLess(len(text), TELEGRAM_LIMIT)
        self.assertGreater(tg_len(text), TELEGRAM_LIMIT)
        self.assertGreater(len(chunk(text)), 1)


class TestPlain(unittest.TestCase):
    """The rail sends parse_mode None, so markup must be converted, not escaped."""

    def test_bold_and_italic_lose_their_markers(self):
        self.assertEqual(plain("**done** and *now*"), "done and now")

    def test_underscore_emphasis(self):
        self.assertEqual(plain("_emphasis_"), "emphasis")

    def test_inline_code_keeps_its_content(self):
        self.assertEqual(plain("ref `55881637`"), "ref 55881637")

    def test_link_keeps_label_and_url(self):
        self.assertEqual(plain("[the run](https://x.test/1)"), "the run (https://x.test/1)")

    def test_image_reduces_to_its_alt_text(self):
        self.assertEqual(plain("![chart](https://x.test/c.png)"), "chart")

    def test_heading_marker_is_dropped(self):
        self.assertEqual(plain("## Results"), "Results")

    def test_bullets_become_a_readable_character(self):
        self.assertEqual(plain("- one\n- two"), "• one\n• two")

    def test_blockquote_marker_is_dropped(self):
        self.assertEqual(plain("> quoted"), "quoted")

    def test_runs_of_blank_lines_collapse(self):
        self.assertEqual(plain("a\n\n\n\n\nb"), "a\n\nb")

    def test_an_asterisk_that_is_not_emphasis_survives(self):
        # `2 * 3` is arithmetic, not markup. Stripping it would corrupt content.
        self.assertEqual(plain("2 * 3 = 6"), "2 * 3 = 6")

    def test_empty_input(self):
        self.assertEqual(plain(""), "")


class TestTruncate(unittest.TestCase):
    def test_short_text_is_untouched(self):
        self.assertEqual(truncate("short", 100), "short")

    def test_marker_is_visible(self):
        cut = truncate("x" * 200, 50)
        self.assertTrue(cut.endswith("[…]"))
        self.assertLessEqual(tg_len(cut), 50)

    def test_never_splits_a_surrogate_pair(self):
        # Half an emoji is an encoding error, not a short message.
        cut = truncate("🟢" * 40, 21)
        self.assertLessEqual(tg_len(cut), 21)
        cut.encode("utf-8")  # would raise on a lone surrogate


class TestChunk(unittest.TestCase):
    def test_short_text_is_one_part_with_no_marker(self):
        self.assertEqual(chunk("hello"), ["hello"])

    def test_every_part_is_within_the_cap(self):
        parts = chunk("word " * 3000)
        self.assertGreater(len(parts), 1)
        for part in parts:
            self.assertLessEqual(tg_len(part), TELEGRAM_LIMIT)

    def test_parts_are_numbered(self):
        parts = chunk("word " * 3000)
        self.assertTrue(parts[0].endswith("(1/{0})".format(len(parts))))
        self.assertTrue(parts[-1].endswith("({0}/{0})".format(len(parts))))

    def test_splits_on_a_paragraph_boundary_when_one_fits(self):
        # The boundary must fall inside the first window, or there is nothing
        # to split on and the cut lands mid-token instead.
        parts = chunk(("a" * 3000) + "\n\n" + ("b" * 2000))
        self.assertEqual(len(parts), 2)
        self.assertTrue(parts[0].startswith("a"))
        self.assertTrue(parts[1].startswith("b"))

    def test_no_content_is_lost(self):
        text = "\n".join("line {0}".format(i) for i in range(900))
        rejoined = "".join(p.rsplit(" (", 1)[0] for p in chunk(text))
        # Boundary whitespace is normalised by the split, so compare on content.
        self.assertEqual(rejoined.replace("\n", ""), text.replace("\n", ""))

    def test_a_single_unbroken_token_is_still_split(self):
        # No boundary exists anywhere; refusing to split would exceed the cap.
        parts = chunk("x" * 9000)
        self.assertGreater(len(parts), 1)
        for part in parts:
            self.assertLessEqual(tg_len(part), TELEGRAM_LIMIT)

    def test_empty_text(self):
        self.assertEqual(chunk(""), [""])


if __name__ == "__main__":
    unittest.main()
