"""Inline keyboards and the one `callback_data` encoding.

This is a deliberate port of `triageKeyboard` in
`/studio/packages/n8n-templates/src/primitives.ts`, not a new scheme. The
studio already has a hardened encoding and it was bought with an incident:
IN-30 records the `dirnotif` sender emitting a two-part `callback_data` while
its receiver matched on a different key, so **every button press silently
no-opped from go-live** until someone thought to check. Nothing about the
message looked wrong. Inventing a third encoding here would re-open exactly
that, so this module speaks the existing one.

The format is always three colon-separated parts:

    <action>:<entity>:<id>

A caller whose key is a single column emits an **empty middle segment**
(`att::55881637`) rather than two parts, so the receiver's fixed three-way split
stays lossless. `id` may itself contain colons — everything after the second
colon is the id — which is why `entity` may not (see `_validate_entity`).

Two different limits apply to a Telegram message and they are measured
differently. Text is capped at 4096 **UTF-16 code units** (`text.tg_len`);
`callback_data` is capped at 64 **UTF-8 bytes**. Using one measure for the other
is a way to ship something that passes locally and fails at the edge.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .errors import KeyboardError

#: Telegram's hard cap on `callback_data`, in UTF-8 bytes.
CALLBACK_DATA_MAX_BYTES = 64


def utf8_len(value: str) -> int:
    """UTF-8 byte length — the unit Telegram measures `callback_data` in."""
    return len(value.encode("utf-8"))


def encode(action: str, entity: str, ident: str) -> str:
    """Build one `callback_data`, or refuse.

    **Refuses rather than truncates** (TG-03). A truncated key still renders a
    perfectly ordinary button; pressing it acts on the wrong row, or on nothing,
    and the failure surfaces weeks later as "the buttons don't work". Failing at
    compose time puts the error in front of the person who can fix it, while
    they are looking at it.
    """
    action = _clean(action, "action")
    entity = _validate_entity(entity)
    ident = "" if ident is None else str(ident)

    data = "{0}:{1}:{2}".format(action, entity, ident)
    size = utf8_len(data)
    if size > CALLBACK_DATA_MAX_BYTES:
        raise KeyboardError(
            "callback_data {0!r} is {1} bytes, over Telegram's {2}-byte limit, for "
            "action {3!r}. The business key cannot round-trip. Shorten the entity or "
            "id, or use a shorter action code — it is never truncated, because a "
            "truncated key acts on the wrong row (TG-03, IN-30).".format(
                data, size, CALLBACK_DATA_MAX_BYTES, action)
        )
    return data


def decode(data: str) -> Dict[str, str]:
    """Split a `callback_data` back into its three parts.

    The mirror of `encode`, and the reason both live in one file: a sender and a
    receiver maintained apart is the IN-30 shape. Anything after the second
    colon belongs to the id.
    """
    text = "" if data is None else str(data)
    parts = text.split(":", 2)
    while len(parts) < 3:
        parts.append("")
    return {"action": parts[0], "entity": parts[1], "id": parts[2], "raw": text}


class Button:
    """One button: a label the human reads and an action the receiver routes on."""

    def __init__(self, label: str, action: str, entity: str = "", ident: str = ""):
        self.label = str(label)
        self.action = str(action)
        self.entity = str(entity or "")
        self.ident = str(ident or "")

    def render(self) -> Dict[str, str]:
        return {"text": self.label, "callback_data": encode(self.action, self.entity, self.ident)}

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "Button({0!r}, {1!r})".format(self.label, self.action)


def keyboard(rows: Sequence[Sequence[Button]]) -> Dict[str, Any]:
    """Render rows of buttons into Telegram's `inline_keyboard` shape.

    The result goes in the notify envelope under `meta.reply_markup`, which the
    live `[TEMPLATE] Notification Fan-out` workflow already knows how to turn
    into a real keyboard — so buttons need no change to any deployed workflow.
    """
    rendered: List[List[Dict[str, str]]] = []
    for row in rows or []:
        cells = [b.render() for b in row]
        if cells:
            rendered.append(cells)
    return {"inline_keyboard": rendered}


def from_spec(spec: Optional[Sequence[Sequence[Dict[str, Any]]]],
              context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Build a keyboard from a template's declared `buttons`, interpolating context.

    Every field is templated, so a catalogue entry can carry
    `{"action": "att", "entity": "poller", "id": "{key}"}` and have the id
    filled from the event being reported. Returns None when there are no
    buttons, so the envelope simply omits `reply_markup`.
    """
    from .render import render  # local import: render imports nothing from here

    if not spec:
        return None
    ctx = context or {}
    rows: List[List[Button]] = []
    for row in spec:
        built = [
            Button(
                label=render(str(cell.get("text", "")), ctx),
                action=render(str(cell.get("action", "")), ctx),
                entity=render(str(cell.get("entity", "")), ctx),
                ident=render(str(cell.get("id", "")), ctx),
            )
            for cell in row or []
        ]
        if built:
            rows.append(built)
    return keyboard(rows) if rows else None


# -- internals -----------------------------------------------------------------


def _clean(value: str, field: str) -> str:
    text = "" if value is None else str(value)
    if not text:
        raise KeyboardError("{0} may not be empty — the receiver routes on it".format(field))
    if ":" in text:
        raise KeyboardError(
            "{0} {1!r} may not contain ':' — it is the field separator, and a colon "
            "here shifts every following segment".format(field, text))
    return text


def _validate_entity(value: str) -> str:
    """Entity may be empty, but never contains a colon.

    An empty entity is the sanctioned single-column form. A colon inside one is
    not caught by the original TypeScript, and it silently corrupts the split:
    the receiver would read the entity's tail as the start of the id.
    """
    text = "" if value is None else str(value)
    if ":" in text:
        raise KeyboardError(
            "entity {0!r} may not contain ':' — everything after the second colon is "
            "read as the id, so a colon here silently corrupts the key".format(text))
    return text
