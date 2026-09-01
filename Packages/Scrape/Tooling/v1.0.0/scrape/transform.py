"""Turn a raw Firecrawl payload into an LLM-ready ``Document``.

Firecrawl already returns markdown, so "translate for an LLM" here means three
conservative jobs, not a rewrite:

* **normalize** the markdown — trim trailing whitespace, drop zero-width cruft,
  and collapse runs of blank lines so the model isn't fed noise (KI-08);
* **bound** it — hard-truncate to ``max_chars`` with a ``truncated`` flag and the
  original length recorded, so one giant page can't silently blow a context
  window (KI-03);
* **map** the fields — pull ``data.markdown`` / ``data.metadata.title`` /
  ``data.metadata.statusCode`` / ``data.links`` into a typed ``Document``, and
  treat a payload with no markdown as an error, not a blank success (KI-02).
"""

from __future__ import annotations

import math
import re
from typing import Any, Mapping

from .config import MAX_CHARS_CAP
from .errors import EmptyContentError
from .model import Document

_ZERO_WIDTH = re.compile(r"[​‌‍﻿]")
_TRAILING_WS = re.compile(r"[ \t]+(\n)")
_MANY_BLANKS = re.compile(r"\n{3,}")


def estimate_tokens(text: str) -> int:
    """Approximate token count with the ~4-chars-per-token rule of thumb.

    This is a heuristic, not a real tokenizer (KI-06) — it exists so chunking can
    stay dependency-free. Leave headroom against a model's true limit.
    """
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def clean_markdown(md: str) -> str:
    """Conservatively normalize markdown for LLM consumption."""
    text = md.replace("\r\n", "\n").replace("\r", "\n")
    text = _ZERO_WIDTH.sub("", text)
    text = _TRAILING_WS.sub(r"\1", text)      # strip trailing spaces before newlines
    text = _MANY_BLANKS.sub("\n\n", text)     # at most one blank line between blocks
    return text.strip() + "\n"


def truncate_to_max_chars(text: str, max_chars: int) -> "tuple[str, bool, int]":
    """Hard-cap ``text`` at ``max_chars``; return (text, truncated, original_len)."""
    original = len(text)
    if original <= max_chars:
        return text, False, original
    return text[:max_chars], True, original


def to_document(
    data: Mapping[str, Any],
    url: str,
    clean: bool = True,
    max_chars: int = MAX_CHARS_CAP,
) -> Document:
    """Build a ``Document`` from a Firecrawl ``data`` object."""
    markdown = data.get("markdown")
    if not isinstance(markdown, str) or not markdown.strip():
        raise EmptyContentError("no markdown in scrape of {0}".format(url))

    metadata = data.get("metadata")
    metadata = dict(metadata) if isinstance(metadata, Mapping) else {}
    links = [str(x) for x in data.get("links", []) if isinstance(x, (str, bytes))]

    body = clean_markdown(markdown) if clean else markdown
    body, truncated, original_chars = truncate_to_max_chars(body, max_chars)

    return Document(
        url=url,
        markdown=body,
        title=metadata.get("title"),
        metadata=metadata,
        links=links,
        source_status=metadata.get("statusCode"),
        truncated=truncated,
        original_chars=original_chars,
    )
