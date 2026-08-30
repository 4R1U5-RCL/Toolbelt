"""The return path: decoding an untrusted Telegram update."""

import unittest

import helpers  # noqa: F401  (path setup)

from telegram.inbound import CALLBACK, MESSAGE, POLL_ANSWER, UNKNOWN, decode_update

CALLBACK_UPDATE = {
    "callback_query": {
        "id": "cbq-1",
        "from": {"id": 8859170398, "username": "arius"},
        "message": {"chat": {"id": -100123}},
        "data": "att:kaggle:55881637",
    }
}
POLL_UPDATE = {
    "poll_answer": {"poll_id": "p-1", "user": {"id": 8859170398}, "option_ids": [1]}
}


class TestCallback(unittest.TestCase):
    def test_decodes_the_three_parts(self):
        answer = decode_update(CALLBACK_UPDATE)
        self.assertEqual(answer.kind, CALLBACK)
        self.assertEqual((answer.action, answer.entity, answer.ident),
                         ("att", "kaggle", "55881637"))

    def test_carries_the_ids_needed_to_answer_the_callback(self):
        answer = decode_update(CALLBACK_UPDATE)
        self.assertEqual(answer.callback_query_id, "cbq-1")
        self.assertEqual(answer.chat_id, "-100123")
        self.assertEqual(answer.user_id, "8859170398")

    def test_trusted_when_no_allow_list_is_given(self):
        self.assertTrue(decode_update(CALLBACK_UPDATE).trusted)

    def test_empty_action_is_untrusted(self):
        update = {"callback_query": dict(CALLBACK_UPDATE["callback_query"], data="")}
        self.assertFalse(decode_update(update).trusted)


class TestGates(unittest.TestCase):
    """Anyone who finds the bot can send it anything (TG-15)."""

    def test_an_allow_listed_chat_passes(self):
        self.assertTrue(decode_update(CALLBACK_UPDATE, allowed_chats=["-100123"]).trusted)

    def test_a_chat_off_the_allow_list_is_refused(self):
        answer = decode_update(CALLBACK_UPDATE, allowed_chats=["-999"])
        self.assertFalse(answer.trusted)
        self.assertIn("not on the allow-list", answer.note)

    def test_an_undeclared_action_is_refused(self):
        answer = decode_update(CALLBACK_UPDATE, allowed_actions=["ok", "no"])
        self.assertFalse(answer.trusted)
        self.assertIn("not declared by any template", answer.note)

    def test_a_declared_action_passes(self):
        self.assertTrue(decode_update(CALLBACK_UPDATE, allowed_actions=["att"]).trusted)

    def test_both_gates_must_pass(self):
        self.assertFalse(decode_update(CALLBACK_UPDATE, allowed_chats=["-100123"],
                                       allowed_actions=["ok"]).trusted)


class TestPollAnswer(unittest.TestCase):
    def test_decodes_the_vote(self):
        answer = decode_update(POLL_UPDATE)
        self.assertEqual(answer.kind, POLL_ANSWER)
        self.assertEqual(answer.options, [1])
        self.assertEqual(answer.ident, "p-1")

    def test_says_it_carries_no_chat_id(self):
        # Telegram does not send one, so this can only ever be user-gated. Said
        # plainly rather than left for someone to discover.
        self.assertIn("no chat id", decode_update(POLL_UPDATE).note)

    def test_a_chat_allow_list_cannot_admit_a_poll_answer(self):
        # Failing closed: no chat id means the gate cannot be satisfied.
        answer = decode_update(POLL_UPDATE, allowed_chats=["-100123"])
        self.assertFalse(answer.trusted)


class TestMalformed(unittest.TestCase):
    """A receiver that raises on garbage can be taken down by anyone."""

    def test_empty_update(self):
        self.assertEqual(decode_update({}).kind, UNKNOWN)

    def test_non_dict_update(self):
        self.assertEqual(decode_update(None).kind, UNKNOWN)

    def test_callback_with_no_data(self):
        self.assertFalse(decode_update({"callback_query": {}}).trusted)

    def test_plain_message_is_decoded_but_routes_nowhere(self):
        answer = decode_update({"message": {"chat": {"id": 1}, "text": "hello"}})
        self.assertEqual(answer.kind, MESSAGE)
        self.assertEqual(answer.text, "hello")

    def test_a_hostile_callback_data_decodes_without_executing_anything(self):
        update = {"callback_query": dict(CALLBACK_UPDATE["callback_query"],
                                         data="../../etc/passwd:x:y")}
        answer = decode_update(update, allowed_actions=["att"])
        self.assertFalse(answer.trusted)


if __name__ == "__main__":
    unittest.main()
