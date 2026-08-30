"""Parity: the n8n receiver must decode exactly what this package encodes.

The Python decoder and the JavaScript one in `n8n/telegram-receiver.json` are
two implementations of one contract, maintained in different languages, in
different files, by different tools. That is precisely the arrangement that
produced IN-30 — a sender and receiver that disagreed about `callback_data`,
where every button press silently did nothing and the messages looked perfect.

So the JS is executed here, against the same updates, and the two answers are
compared. Skips loudly if `node` is unavailable, because a parity test that
quietly does nothing is how the drift gets back in.
"""

import json
import os
import subprocess
import unittest

import helpers  # noqa: F401  (path setup)

from telegram.inbound import decode_update
from telegram.keyboard import encode

WORKFLOW = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "n8n", "telegram-receiver.json")
INTERACTIVE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "n8n", "telegram-interactive.json")


def _node_available() -> bool:
    try:
        subprocess.run(["node", "--version"], capture_output=True, check=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return False
    return os.path.isfile(WORKFLOW)


def _decode_js(node_name: str, workflow_path: str) -> str:
    with open(workflow_path, "r", encoding="utf-8") as handle:
        workflow = json.load(handle)
    for node in workflow["nodes"]:
        if node["name"] == node_name:
            return node["parameters"]["jsCode"]
    raise AssertionError("node {0!r} not found in {1}".format(node_name, workflow_path))


def run_receiver(update, allowed_chats="", secret="", presented=""):
    """Execute the workflow's Code node against one update, outside n8n."""
    code = _decode_js("Decode + Gate", WORKFLOW)
    harness = """
const $env = {{
  TELEGRAM_WEBHOOK_SECRET: {secret},
  TELEGRAM_ALLOWED_CHATS: {chats},
  TELEGRAM_DEFAULT_CHAT: '1',
}};
const __static = {{}};
const $getWorkflowStaticData = () => __static;
const $input = {{ all: () => [{{ json: {{
  headers: {{ 'x-telegram-bot-api-secret-token': {presented} }},
  body: {update},
}} }}] }};
const run = () => {{ {code} }};
process.stdout.write(JSON.stringify(run().map((i) => i.json)));
""".format(code=code, update=json.dumps(update), chats=json.dumps(allowed_chats),
           secret=json.dumps(secret), presented=json.dumps(presented))
    completed = subprocess.run(["node", "-e", harness],
                               capture_output=True, text=True, timeout=60)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)[0]


def run_receiver_bare(update, allowed_chats="", secret=""):
    """Execute the Code node the way the Telegram Trigger feeds it: no headers."""
    code = _decode_js("Decode + Gate", WORKFLOW)
    harness = """
const $env = {{ TELEGRAM_WEBHOOK_SECRET: {secret}, TELEGRAM_ALLOWED_CHATS: {chats} }};
const __static = {{}};
const $getWorkflowStaticData = () => __static;
const $input = {{ all: () => [{{ json: {update} }}] }};
const run = () => {{ {code} }};
process.stdout.write(JSON.stringify(run().map((i) => i.json)));
""".format(code=code, update=json.dumps(update), chats=json.dumps(allowed_chats),
           secret=json.dumps(secret))
    completed = subprocess.run(["node", "-e", harness],
                               capture_output=True, text=True, timeout=60)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)[0]


CALLBACK = {
    "callback_query": {"id": "cbq-1", "from": {"id": 8859170398, "username": "arius"},
                       "message": {"chat": {"id": -100123}},
                       "data": "att:kaggle:55881637"},
}
#: The deployed receiver fails closed to the owner's chat when the allow-list env
#: is unset (TG-21), which the library deliberately does not do — a library
#: hard-coding a chat id would be wrong. So parity is asserted on DECODING, with
#: the same allow-list handed to both sides; the differing defaults are their own
#: test below.
ALLOW = "-100123"
POLL = {"poll_answer": {"poll_id": "p-1", "user": {"id": 8859170398}, "option_ids": [2]}}


@unittest.skipUnless(_node_available(),
                     "node unavailable — n8n/Python decoder parity NOT PROVEN here")
class TestReceiverParity(unittest.TestCase):

    def test_callback_decodes_identically(self):
        js = run_receiver(CALLBACK, allowed_chats=ALLOW)
        py = decode_update(CALLBACK, allowed_chats=[ALLOW])
        self.assertEqual((js["action"], js["entity"], js["id"]),
                         (py.action, py.entity, py.ident))
        self.assertEqual(js["chat_id"], py.chat_id)
        self.assertEqual(js["callback_query_id"], py.callback_query_id)
        self.assertEqual(js["trusted"], py.trusted)

    def test_an_id_containing_colons_survives_both(self):
        data = encode("ok", "run", "2026-08-30T12:00:00")
        update = {"callback_query": dict(CALLBACK["callback_query"], data=data)}
        js = run_receiver(update, allowed_chats=ALLOW)
        self.assertEqual(js["id"], decode_update(update).ident)
        self.assertEqual(js["id"], "2026-08-30T12:00:00")

    def test_single_column_key_decodes_identically(self):
        update = {"callback_query": dict(CALLBACK["callback_query"],
                                         data=encode("att", "", "55881637"))}
        js = run_receiver(update, allowed_chats=ALLOW)
        py = decode_update(update)
        self.assertEqual((js["entity"], js["id"]), (py.entity, py.ident))
        self.assertEqual(js["entity"], "")

    def test_chat_allow_list_agrees(self):
        self.assertTrue(run_receiver(CALLBACK, allowed_chats="-100123")["trusted"])
        self.assertFalse(run_receiver(CALLBACK, allowed_chats="-999")["trusted"])
        self.assertFalse(decode_update(CALLBACK, allowed_chats=["-999"]).trusted)

    def test_poll_answer_agrees(self):
        js = run_receiver(POLL)
        py = decode_update(POLL)
        self.assertEqual(js["kind"], py.kind)
        self.assertEqual(js["options"], py.options)
        self.assertEqual(js["id"], py.ident)

    def test_poll_answer_cannot_pass_a_chat_allow_list_in_either(self):
        self.assertFalse(run_receiver(POLL, allowed_chats="-100123")["trusted"])
        self.assertFalse(decode_update(POLL, allowed_chats=["-100123"]).trusted)

    def test_empty_action_is_untrusted_in_both(self):
        update = {"callback_query": dict(CALLBACK["callback_query"], data="")}
        self.assertFalse(run_receiver(update, allowed_chats=ALLOW)["trusted"])
        self.assertFalse(decode_update(update).trusted)

    def test_the_deployed_receiver_fails_closed_when_unconfigured(self):
        """The one place the two sides deliberately differ (TG-21).

        With no allow-list env set, the n8n receiver admits only the owner's
        chat — because that endpoint is reachable by anyone who finds the bot and
        its other gate is also skipped when unset. The Python library takes its
        allow-list from the caller and hard-codes nothing, which is right for a
        library and wrong for a deployed endpoint.
        """
        self.assertFalse(run_receiver(CALLBACK)["trusted"])          # chat -100123
        self.assertTrue(decode_update(CALLBACK).trusted)             # no list given
        owner = {"callback_query": dict(CALLBACK["callback_query"],
                                        message={"chat": {"id": 8859170398}})}
        self.assertTrue(run_receiver(owner)["trusted"])

    def test_garbage_update_is_untrusted_in_both(self):
        self.assertFalse(run_receiver({"edited_message": {}}, allowed_chats=ALLOW)["trusted"])
        self.assertFalse(decode_update({"edited_message": {}}).trusted)

    def test_the_webhook_secret_gates_a_generic_webhook_deployment(self):
        """Telegram signs nothing; `setWebhook`'s secret_token is the only gate.

        Only applies on a generic-webhook deployment. Crucially, an ABSENT
        header must fail too — skipping the check merely because the header is
        missing would let anyone bypass it by omitting it.
        """
        self.assertTrue(run_receiver(CALLBACK, allowed_chats=ALLOW,
                                     secret="s3cret", presented="s3cret")["trusted"])
        self.assertFalse(run_receiver(CALLBACK, allowed_chats=ALLOW,
                                      secret="s3cret", presented="wrong")["trusted"])
        self.assertFalse(run_receiver(CALLBACK, allowed_chats=ALLOW,
                                      secret="s3cret", presented="")["trusted"])

    def test_the_trigger_path_carries_no_headers_and_is_not_gated_on_them(self):
        """On the Telegram Trigger n8n owns the endpoint; there are no headers.

        The discriminator is the transport, not the presence of the header — so
        a configured secret cannot be defeated by dropping it on the generic
        path, and cannot lock out the trigger path either.
        """
        answer = run_receiver_bare(CALLBACK, allowed_chats=ALLOW, secret="s3cret")
        self.assertTrue(answer["trusted"])
        self.assertEqual(answer["action"], "att")


@unittest.skipUnless(_node_available(), "node unavailable")
class TestInteractiveShaping(unittest.TestCase):
    """The sender's Shape node must read what template.py's `meta()` writes."""

    def _shape(self, body):
        code = _decode_js("Shape", INTERACTIVE)
        harness = """
const $env = {{ TELEGRAM_DEFAULT_CHAT: '8859170398' }};
const $input = {{ all: () => [{{ json: {{ body: {body} }} }}] }};
const run = () => {{ {code} }};
process.stdout.write(JSON.stringify(run().map((i) => i.json)));
""".format(code=code, body=json.dumps(body))
        completed = subprocess.run(["node", "-e", harness],
                                   capture_output=True, text=True, timeout=60)
        if completed.returncode != 0:
            raise AssertionError(completed.stderr)
        return json.loads(completed.stdout)[0]

    def test_a_poll_envelope_routes_to_the_poll_branch(self):
        from telegram.template import Catalogue
        message = Catalogue().load().get("poll").render(
            {"question": "Which lane?", "options": ["A", "B", "C"]})
        shaped = self._shape({"message": message.text, "meta": message.meta()})
        self.assertTrue(shaped["__isPoll"])
        self.assertEqual(shaped["__question"], "Which lane?")
        body = json.loads(shaped["__pollBody"])
        self.assertEqual(body["question"], "Which lane?")
        self.assertEqual(body["options"], ["A", "B", "C"])

    def test_a_poll_degrades_to_readable_text_without_a_bot_token(self):
        """n8n has no sendPoll, so a poll is a Bot API call needing a token.

        Absent it, the poll must arrive as a legible numbered list that SAYS it
        was degraded — not vanish, and not fail the execution (TG-22).
        """
        from telegram.template import Catalogue
        message = Catalogue().load().get("poll").render(
            {"question": "Which lane?", "options": ["A", "B", "C"]})
        shaped = self._shape({"message": message.text, "meta": message.meta()})
        self.assertFalse(shaped["__canPoll"])          # no token in the harness env
        self.assertIn("1. A", shaped["__text"])
        self.assertIn("3. C", shaped["__text"])
        self.assertIn("TG-22", shaped["__text"])

    def test_a_button_envelope_routes_to_the_message_branch_with_a_keyboard(self):
        from telegram.template import Catalogue
        message = Catalogue().load().get("approval").render(
            {"title": "Ship it", "id": "run-412", "entity": "deploy"})
        shaped = self._shape({"message": message.text, "meta": message.meta()})
        self.assertFalse(shaped["__isPoll"])
        self.assertTrue(shaped["__hasKb"])
        # Flat leaves, not a nested object: n8n cannot fill a fixedCollection
        # from an expression, so the structure lives in the node (TG-20).
        self.assertEqual(shaped["__btnCount"], 3)
        self.assertEqual(shaped["__b1text"], "✅ Approve")
        self.assertEqual(shaped["__b1data"], "ok:deploy:run-412")
        self.assertEqual(shaped["__b3data"], "def:deploy:run-412")
        self.assertEqual(shaped["__btnDropped"], 0)

    def test_a_plain_report_needs_neither(self):
        from telegram.template import Catalogue
        message = Catalogue().load().get("report").render({"title": "Done"})
        shaped = self._shape({"message": message.text, "meta": message.meta()})
        self.assertFalse(shaped["__isPoll"])
        self.assertFalse(shaped["__hasKb"])

    def test_buttons_beyond_the_third_are_dropped_and_counted(self):
        """The interactive workflow carries one row of three (TG-20).

        Reported rather than silently discarded — a fourth button that never
        appears is a decision the human was never offered.
        """
        meta = {"reply_markup": {"inline_keyboard": [
            [{"text": "a", "callback_data": "a::1"}, {"text": "b", "callback_data": "b::1"}],
            [{"text": "c", "callback_data": "c::1"}, {"text": "d", "callback_data": "d::1"}]]}}
        shaped = self._shape({"message": "x", "meta": meta})
        self.assertEqual(shaped["__btnCount"], 3)
        self.assertEqual(shaped["__btnDropped"], 1)

    def test_a_poll_with_one_option_is_not_treated_as_a_poll(self):
        # Telegram would reject it; falling back to a text message is better
        # than a failed execution with no message at all.
        shaped = self._shape({"message": "x", "meta": {"poll": {"question": "q",
                                                                "options": ["only"]}}})
        self.assertFalse(shaped["__isPoll"])


if __name__ == "__main__":
    unittest.main()
