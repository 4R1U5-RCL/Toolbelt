"""Emit a ``Document`` in an LLM-friendly shape: markdown (with a small YAML
frontmatter of provenance), plain text, or structured JSON. Chunked output is
rendered separately so a caller can feed one chunk per request.
"""

from __future__ import annotations

import json
from typing import Any, List

from .model import Document

_FM_KEYS = ("url", "title", "source_status", "chars", "original_chars", "truncated")


def render_document(doc: Document, fmt: str = "markdown") -> str:
    if fmt == "json":
        return json.dumps(doc.to_dict(), indent=2, ensure_ascii=False)
    if fmt == "text":
        return doc.markdown
    if fmt == "markdown":
        return _frontmatter(doc) + "\n" + doc.markdown
    raise ValueError("unknown format: {0}".format(fmt))


def render_chunks(doc: Document, fmt: str = "markdown") -> str:
    if fmt == "json":
        return json.dumps([c.to_dict() for c in doc.chunks], indent=2, ensure_ascii=False)
    parts: List[str] = []
    total = len(doc.chunks)
    for c in doc.chunks:
        header = "----- chunk {0}/{1} · ~{2} tokens -----".format(c.index + 1, total, c.tokens)
        parts.append(header + "\n\n" + c.text)
    return "\n\n".join(parts)


def _frontmatter(doc: Document) -> str:
    values = {
        "url": doc.url,
        "title": doc.title,
        "source_status": doc.source_status,
        "chars": len(doc.markdown),
        "original_chars": doc.original_chars,
        "truncated": doc.truncated,
    }
    lines = ["---"]
    for key in _FM_KEYS:
        lines.append("{0}: {1}".format(key, _yaml_scalar(values[key])))
    if doc.links:
        lines.append("links: {0}".format(len(doc.links)))
    lines.append("---")
    return "\n".join(lines) + "\n"


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return '"{0}"'.format(text)
