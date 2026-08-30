"""Typed exception hierarchy for the scraper.

The central axis is **transient vs fatal**, declared here so the engine never has
to guess whether to retry: a transient error is worth another attempt (a 429, a
5xx, a socket timeout); a fatal error is a human's job to fix (a bad URL, a 401,
a page that genuinely has no content). The CLI catches the base `ScrapeError` and
maps it to an exit code.
"""

from __future__ import annotations


class ScrapeError(Exception):
    """Base for everything the package raises deliberately."""


class ConfigError(ScrapeError):
    """Unusable configuration (or a missing credential); fatal, before any fetch."""


class FetchError(ScrapeError):
    """Base for anything that goes wrong talking to the scrape backend."""


class TransientFetchError(FetchError):
    """Retryable — a 429/5xx/timeout. Another attempt may succeed."""


class FatalFetchError(FetchError):
    """A human must fix it — a bad URL, an auth failure, a 404. Never retried."""


class EmptyContentError(FatalFetchError):
    """A 2xx response that carried no usable content (KI-02).

    Firecrawl can return HTTP 200 with no ``data.markdown`` for a JS-only or
    blocked page. That is a real failure, not a blank success — retrying the same
    URL will not conjure content, so it is classified fatal.
    """
