"""Domain value objects: a scraped ``Document`` and its optional ``Chunk``s.

A ``Document`` is the LLM-ready result of one scrape: the cleaned markdown, the
metadata worth keeping (title, source URL, the scraped page's own HTTP status),
any extracted links, and — if chunking was asked for — the markdown split into
token-bounded pieces. It knows how to describe itself as a plain dict so the
JSON renderer and the tests never reach into private state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Chunk:
    index: int
    text: str
    tokens: int

    def to_dict(self) -> Dict[str, Any]:
        return {"index": self.index, "tokens": self.tokens, "text": self.text}


@dataclass
class Document:
    url: str
    markdown: str
    title: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    source_status: Optional[int] = None
    truncated: bool = False
    original_chars: int = 0
    chunks: List[Chunk] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "source_status": self.source_status,
            "chars": len(self.markdown),
            "original_chars": self.original_chars,
            "truncated": self.truncated,
            "links": list(self.links),
            "metadata": dict(self.metadata),
            "markdown": self.markdown,
            "chunks": [c.to_dict() for c in self.chunks],
        }
