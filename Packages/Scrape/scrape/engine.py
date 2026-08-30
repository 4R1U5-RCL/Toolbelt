"""Orchestration: one scrape, and a batch that survives a bad page.

``scrape_url`` runs the pipeline for a single URL — fetch → translate → (optional)
chunk. ``scrape_many`` runs it per URL **independently**: a page that 404s or
times out is recorded as a failed outcome and the batch keeps going, because the
one lesson every batch scraper eventually learns is that one slow/broken page
must not take the rest down with it (KI-01).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Protocol

from .chunk import chunk_markdown
from .config import Config
from .errors import ScrapeError
from .model import Document
from .transform import to_document


class Backend(Protocol):
    def scrape(self, url: str) -> Any: ...


def scrape_url(url: str, client: Backend, config: Config) -> Document:
    data = client.scrape(url)
    doc = to_document(data, url, clean=config.clean, max_chars=config.max_chars)
    if config.chunk:
        doc.chunks = chunk_markdown(doc.markdown, config.max_tokens, config.overlap)
    return doc


@dataclass
class Outcome:
    url: str
    document: Optional[Document] = None
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.document is not None


def scrape_many(
    urls: Iterable[str],
    client: Backend,
    config: Config,
    on_error: str = "continue",
) -> List[Outcome]:
    """Scrape each URL independently. ``on_error='stop'`` halts on the first failure."""
    outcomes: List[Outcome] = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        try:
            outcomes.append(Outcome(url=url, document=scrape_url(url, client, config)))
        except ScrapeError as err:
            outcomes.append(Outcome(url=url, error=str(err)))
            if on_error == "stop":
                break
    return outcomes
