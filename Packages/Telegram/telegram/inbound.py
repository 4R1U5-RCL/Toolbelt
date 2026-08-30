"""The return path: turning a Telegram update back into an answer.

An interactive message is only half a rail. The button press arrives as a
Telegram *update* POSTed to whatever webhook the bot is pointed at, and someone
has to decode it, decide whether to trust it, and route it.

Today every plugin that needed this wrote its own decoder — and the encodings
drifted, which is IN-30: `dirnotif` emitted a two-part `callback_data` against a
receiver expecting a different key, so every press silently no-opped from
go-live. Decoding lives here, next to `keyboard.encode`, so the two halves of
the contract cannot be maintained apart.

## Trust

Telegram updates are **untrusted input** (TG-15). Anyone who finds the bot can
send it a message, and `callback_data` is echoed back from a message the bot
itself sent — but a crafted update can carry anything at all. So:

* `chat_id` is checked against an allow-list before any action is taken;
* the decoded action is checked against the actions the template declared,
  rather than being trusted to name a handler;
* nothing here executes anything. It returns a description of what was pressed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .keyboard import decode as decode_callback

CALLBACK = "callback"
POLL_ANSWER = "poll_answer"
MESSAGE = "message"
UNKNOWN = "unknown"


class Answer:
    """One decoded human response."""

    def __init__(self, kind: str, action: str = "", entity: str = "", ident: str = "",
                 chat_id: str = "", user_id: str = "", username: str = "",
                 callback_query_id: str = "", raw_data: str = "",
                 options: Optional[List[int]] = None, text: str = "",
                 trusted: bool = False, note: str = ""):
        self.kind = kind
        self.action = action
        self.entity = entity
        self.ident = ident
        self.chat_id = chat_id
        self.user_id = user_id
        self.username = username
        self.callback_query_id = callback_query_id
        self.raw_data = raw_data
        self.options = options or []
        self.text = text
        self.trusted = trusted
        self.note = note

    def as_dict(self) -> Dict[str, Any]:
        return {
            "kind": self.kind, "action": self.action, "entity": self.entity,
            "id": self.ident, "chat_id": self.chat_id, "user_id": self.user_id,
            "username": self.username, "callback_query_id": self.callback_query_id,
            "options": self.options, "text": self.text,
            "trusted": self.trusted, "note": self.note,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "Answer({0!r}, action={1!r}, trusted={2})".format(
            self.kind, self.action, self.trusted)


def decode_update(update: Dict[str, Any],
                  allowed_chats: Optional[Sequence[str]] = None,
                  allowed_actions: Optional[Sequence[str]] = None) -> Answer:
    """Decode one Telegram update into an `Answer`.

    Never raises on a malformed update: a receiver that throws on garbage is a
    receiver that can be taken down by anyone who can reach the bot. Unusable
    input comes back as `kind="unknown"` with `trusted=False`.
    """
    update = update if isinstance(update, dict) else {}

    if isinstance(update.get("callback_query"), dict):
        answer = _from_callback(update["callback_query"])
    elif isinstance(update.get("poll_answer"), dict):
        answer = _from_poll_answer(update["poll_answer"])
    elif isinstance(update.get("message"), dict):
        answer = _from_message(update["message"])
    else:
        return Answer(UNKNOWN, note="update carried no callback_query, poll_answer or message")

    return _apply_gates(answer, allowed_chats, allowed_actions)


# -- decoders ------------------------------------------------------------------


def _from_callback(query: Dict[str, Any]) -> Answer:
    parts = decode_callback(str(query.get("data") or ""))
    sender = query.get("from") or {}
    message = query.get("message") or {}
    chat = message.get("chat") or {}
    return Answer(
        kind=CALLBACK,
        action=parts["action"], entity=parts["entity"], ident=parts["id"],
        chat_id=str(chat.get("id") or ""),
        user_id=str(sender.get("id") or ""),
        username=str(sender.get("username") or ""),
        callback_query_id=str(query.get("id") or ""),
        raw_data=parts["raw"],
    )


def _from_poll_answer(payload: Dict[str, Any]) -> Answer:
    """A vote on a native poll.

    A poll answer identifies the *poll*, not the chat — Telegram does not send a
    chat id here. So a poll vote can never be chat-allow-listed, only
    user-allow-listed, and that limitation is stated rather than papered over.
    """
    sender = payload.get("user") or {}
    options = [int(o) for o in (payload.get("option_ids") or []) if isinstance(o, int)]
    return Answer(
        kind=POLL_ANSWER,
        ident=str(payload.get("poll_id") or ""),
        user_id=str(sender.get("id") or ""),
        username=str(sender.get("username") or ""),
        options=options,
        note="poll answers carry no chat id; gate them on user_id",
    )


def _from_message(message: Dict[str, Any]) -> Answer:
    """A plain text reply. Carried for completeness; nothing routes on it yet."""
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    return Answer(
        kind=MESSAGE,
        chat_id=str(chat.get("id") or ""),
        user_id=str(sender.get("id") or ""),
        username=str(sender.get("username") or ""),
        text=str(message.get("text") or ""),
    )


# -- gating --------------------------------------------------------------------


def _apply_gates(answer: Answer, allowed_chats: Optional[Sequence[str]],
                 allowed_actions: Optional[Sequence[str]]) -> Answer:
    """Decide whether this answer may be acted on. Fail closed."""
    chats = [str(c) for c in (allowed_chats or []) if str(c)]
    actions = [str(a) for a in (allowed_actions or []) if str(a)]

    if chats:
        # A poll answer has no chat id at all, so a chat allow-list cannot admit
        # it. Saying that plainly beats admitting it by accident.
        if not answer.chat_id:
            answer.trusted = False
            answer.note = ("no chat id on this update, so the chat allow-list cannot "
                           "admit it" + (" — " + answer.note if answer.note else ""))
            return answer
        if answer.chat_id not in chats:
            answer.trusted = False
            answer.note = "chat {0} is not on the allow-list".format(answer.chat_id)
            return answer

    if actions and answer.kind == CALLBACK and answer.action not in actions:
        answer.trusted = False
        answer.note = ("action {0!r} was not declared by any template — refusing to "
                       "route it (TG-15)".format(answer.action))
        return answer

    if answer.kind == CALLBACK and not answer.action:
        answer.trusted = False
        answer.note = "callback_data carried no action"
        return answer

    answer.trusted = True
    return answer
