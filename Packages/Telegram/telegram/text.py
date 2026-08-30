"""Plain-text safety: what actually survives the trip to a Telegram message.

Two hard facts about the live rail shape everything here.

**The delivery node sends `parse_mode: "None"`.** Markdown is not rendered — it
is transmitted. A message built as `*Kaggle settled*` arrives with the asterisks
visible, which looks like a bug in the sender and not in the formatting. So the
package never emits markup: `plain()` converts markup to the text a human meant
(TG-01).

**Telegram caps a message at 4096 UTF-16 code units**, not characters and not
bytes. An emoji outside the BMP is one Python character and *two* units, so a
message of 4000 emoji is over the limit while `len()` says it is comfortably
under. Nothing in the studio chunks at all today — every caller pre-truncates at
some arbitrary number (200, 300, 400, 2500) and accepts the loss (TG-04).
"""

from __future__ import annotations

import re
from typing import List

# Telegram's documented cap for sendMessage text.
TELEGRAM_LIMIT = 4096
# Room for the " (2/3)" continuation marker plus a safety margin, so a chunk can
# never be pushed over the cap by the marker that says it was chunked.
_MARKER_ROOM = 16

_FENCE = re.compile(r"^```.*?$", re.MULTILINE)
_IMAGE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")
_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_QUOTE = re.compile(r"^\s{0,3}>\s?", re.MULTILINE)
_RULE = re.compile(r"^\s{0,3}(?:[-*_]\s*){3,}$", re.MULTILINE)
_BOLD = re.compile(r"(\*\*|__)(?=\S)(.+?)(?<=\S)\1", re.DOTALL)
_ITALIC = re.compile(r"(?<![\w*_])([*_])(?=\S)([^*_]+?)(?<=\S)\1(?![\w*_])")
_CODE = re.compile(r"`([^`]+)`")
_BULLET = re.compile(r"^\s{0,3}[-*+]\s+", re.MULTILINE)
_BLANKS = re.compile(r"\n{3,}")


def tg_len(text: str) -> int:
    """Length as Telegram counts it: UTF-16 code units.

    `len("🟢")` is 1 in Python and 2 to Telegram. Measuring the wrong one is how
    a message that passed every local check gets rejected at the edge.
    """
    return len(text.encode("utf-16-le")) // 2


def plain(text: str) -> str:
    """Convert markdown-ish text to the plain text a reader expects.

    Not an escape and not a sanitiser — a *conversion*. `**done**` becomes
    `done`, not `\\*\\*done\\*\\*`, because the intent was emphasis and the rail
    cannot render emphasis (TG-01). Links keep both halves: the label is what
    the sentence needs, the URL is what the reader may want to open.
    """
    if not text:
        return ""
    out = str(text)
    out = _FENCE.sub("", out)            # fence markers, not the code inside
    out = _IMAGE.sub(r"\1", out)         # images have no meaning here
    out = _LINK.sub(r"\1 (\2)", out)
    out = _HEADING.sub("", out)
    out = _QUOTE.sub("", out)
    out = _RULE.sub("", out)
    out = _BOLD.sub(r"\2", out)
    out = _ITALIC.sub(r"\2", out)
    out = _CODE.sub(r"\1", out)
    out = _BULLET.sub("• ", out)
    out = _BLANKS.sub("\n\n", out)
    return out.strip()


def truncate(text: str, limit: int = TELEGRAM_LIMIT, marker: str = " […]") -> str:
    """Cut `text` to `limit` UTF-16 units, ending with a visible marker.

    The marker is not decoration. Silent truncation is indistinguishable from a
    message that simply had nothing more to say, which is how a caller comes to
    believe it reported something it did not.
    """
    if tg_len(text) <= limit:
        return text
    budget = max(0, limit - tg_len(marker))
    cut = _cut_to(text, budget)
    # Prefer a word boundary, but only if one is close enough that we are not
    # discarding real content to get it.
    space = cut.rfind(" ")
    if space > 0 and tg_len(cut) - tg_len(cut[:space]) < 24:
        cut = cut[:space]
    return cut.rstrip() + marker


def chunk(text: str, limit: int = TELEGRAM_LIMIT) -> List[str]:
    """Split `text` into deliverable messages, each within the cap.

    Splits at the largest boundary that fits — blank line, then newline, then
    space — so a report arrives as paragraphs rather than sliced mid-sentence.
    Multi-part output is numbered, because two messages arriving out of order in
    a busy chat are otherwise unreadable.
    """
    if not text:
        return [""]
    if tg_len(text) <= limit:
        return [text]

    body_limit = max(1, limit - _MARKER_ROOM)
    parts: List[str] = []
    rest = text
    while tg_len(rest) > body_limit:
        head = _cut_to(rest, body_limit)
        split = _last_boundary(head)
        if split <= 0:
            split = len(head)          # no boundary at all: a single long token
        parts.append(rest[:split].rstrip())
        rest = rest[split:].lstrip()
    if rest:
        parts.append(rest)

    total = len(parts)
    return ["{0} ({1}/{2})".format(p, i + 1, total) for i, p in enumerate(parts)]


# -- internals -----------------------------------------------------------------


def _cut_to(text: str, units: int) -> str:
    """Longest prefix of `text` that fits in `units` UTF-16 code units.

    Walks back off a surrogate pair rather than splitting one — half an emoji is
    an encoding error, not a short message.
    """
    if tg_len(text) <= units:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if tg_len(text[:mid]) <= units:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo]


#: A boundary is only worth honouring if it uses a decent share of the window.
#: Without this, text whose single paragraph break sits near the start splits
#: there — emitting a two-line first message followed by a full one, which reads
#: like something went wrong.
_MIN_FILL = 0.5


def _last_boundary(head: str) -> int:
    """Index of the best split point in `head`: paragraph > line > word.

    Coarsest separator first, but only while it still fills the message. A
    paragraph break at 2% of the window loses to a line break at 90%.
    """
    floor = int(len(head) * _MIN_FILL)
    for candidate in ("\n\n", "\n", " "):
        idx = head.rfind(candidate)
        if idx > floor:
            return idx + len(candidate)
    # Nothing fills the window: take the coarsest boundary that exists at all
    # rather than cutting mid-token.
    for candidate in ("\n\n", "\n", " "):
        idx = head.rfind(candidate)
        if idx > 0:
            return idx + len(candidate)
    return -1
