"""scrape — turn web pages into LLM-ready text via Firecrawl.

Fetch a URL through Firecrawl, normalize the returned markdown, bound it to a
context-window-safe size, and (optionally) split it into token-bounded chunks —
emitting a typed ``Document`` you can hand straight to a model.

The package is deliberately dependency-free (Python 3.9+ standard library only),
so the same tree runs inside the /studio container, on a bare VPS, or under cron
on a laptop. The one network boundary (``HttpClient``) is injected, so the whole
pipeline is unit-tested offline against fake Firecrawl responses.

Public surface:

    from scrape import scrape_url, scrape_many, load_config, build_client, Document

Everything else is an implementation detail and may change.
"""

from .client import FirecrawlClient, build_client
from .config import Config, load_config, resolve_api_key
from .engine import Outcome, scrape_many, scrape_url
from .model import Chunk, Document

__version__ = "1.0.0"

__all__ = [
    "Chunk",
    "Config",
    "Document",
    "FirecrawlClient",
    "Outcome",
    "__version__",
    "build_client",
    "load_config",
    "resolve_api_key",
    "scrape_many",
    "scrape_url",
]
