"""The callback_data encoding — the half of an interactive message that fails silently.

IN-30 is the reason every assertion here exists: a sender and a receiver that
disagree about the encoding produce buttons that look completely normal and do
nothing at all.
"""

import unittest

import helpers  # noqa: F401  (path setup)

from telegram.errors import KeyboardError
from telegram.keyboard import (CALLBACK_DATA_MAX_BYTES, Button, decode, encode,
                               from_spec, keyboard, utf8_len)


class TestEncode(unittest.TestCase):
    def test_three_part_form(self):
        self.assertEqual(encode("att", "kaggle", "55881637"), "att:kaggle:55881637")

    def test_single_column_key_keeps_an_empty_middle_segment(self):
        # Two parts would break the receiver's fixed three-way split.
        self.assertEqual(encode("att", "", "55881637"), "att::55881637")

    def test_an_id_may_contain_colons(self):
        data = encode("ok", "run", "2026-08-30T12:00:00")
        self.assertEqual(decode(data)["id"], "2026-08-30T12:00:00")

    def test_action_may_not_be_empty(self):
        with self.assertRaises(KeyboardError):
            encode("", "e", "1")

    def test_a_colon_in_the_action_is_refused(self):
        with self.assertRaises(KeyboardError):
            encode("a:b", "e", "1")

    def test_a_colon_in_the_entity_is_refused(self):
        # Not caught by the original TypeScript. A colon here silently shifts
        # the split, so the receiver reads the entity's tail as the id.
        with self.assertRaises(KeyboardError):
            encode("att", "kag:gle", "1")


class TestByteCap(unittest.TestCase):
    """The cap is 64 UTF-8 BYTES — not characters, and not the text limit."""

    def test_exactly_at_the_cap_is_allowed(self):
        ident = "x" * (CALLBACK_DATA_MAX_BYTES - len("att::"))
        data = encode("att", "", ident)
        self.assertEqual(utf8_len(data), CALLBACK_DATA_MAX_BYTES)

    def test_one_byte_over_is_refused(self):
        ident = "x" * (CALLBACK_DATA_MAX_BYTES - len("att::") + 1)
        with self.assertRaises(KeyboardError):
            encode("att", "", ident)

    def test_multibyte_characters_count_as_their_bytes(self):
        # 30 two-byte characters is 60 bytes, which with the prefix is over.
        with self.assertRaises(KeyboardError):
            encode("att", "", "é" * 30)

    def test_the_error_names_the_action_and_says_it_is_never_truncated(self):
        with self.assertRaises(KeyboardError) as caught:
            encode("mute", "entity", "y" * 80)
        message = str(caught.exception)
        self.assertIn("mute", message)
        self.assertIn("truncated", message)
        self.assertIn("IN-30", message)


class TestDecode(unittest.TestCase):
    def test_round_trip(self):
        parts = decode(encode("def", "poller", "abc"))
        self.assertEqual((parts["action"], parts["entity"], parts["id"]),
                         ("def", "poller", "abc"))

    def test_garbage_decodes_to_empty_parts_rather_than_raising(self):
        # A receiver that raises on malformed input can be taken down by anyone
        # who can reach the bot.
        parts = decode("nonsense")
        self.assertEqual(parts["action"], "nonsense")
        self.assertEqual(parts["entity"], "")
        self.assertEqual(parts["id"], "")

    def test_none_is_survivable(self):
        self.assertEqual(decode(None)["raw"], "")


class TestKeyboardRendering(unittest.TestCase):
    def test_rows_are_preserved(self):
        markup = keyboard([[Button("A", "a", "e", "1"), Button("B", "b", "e", "1")],
                           [Button("C", "c", "e", "1")]])
        self.assertEqual(len(markup["inline_keyboard"]), 2)
        self.assertEqual(len(markup["inline_keyboard"][0]), 2)

    def test_empty_rows_are_dropped(self):
        markup = keyboard([[], [Button("A", "a", "e", "1")]])
        self.assertEqual(len(markup["inline_keyboard"]), 1)

    def test_from_spec_interpolates_context(self):
        markup = from_spec(
            [[{"text": "✅ {label}", "action": "ok", "entity": "run", "id": "{key}"}]],
            {"label": "Approve", "key": "412"})
        cell = markup["inline_keyboard"][0][0]
        self.assertEqual(cell["text"], "✅ Approve")
        self.assertEqual(cell["callback_data"], "ok:run:412")

    def test_from_spec_returns_none_without_buttons(self):
        self.assertIsNone(from_spec(None, {}))

    def test_an_interpolated_id_that_is_too_long_fails_at_compose_time(self):
        # The point of failing here: the person who can fix it is looking at it.
        with self.assertRaises(KeyboardError):
            from_spec([[{"text": "x", "action": "ok", "entity": "run", "id": "{key}"}]],
                      {"key": "z" * 100})


if __name__ == "__main__":
    unittest.main()
