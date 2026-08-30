"""The scrape backend: a thin Firecrawl v1 client over the injectable HttpClient.

Modeled directly on the studio ops client (``packages/ops-mcp`` ``firecrawl_scrape``):
``POST https://api.firecrawl.dev/v1/scrape`` with a ``Bearer`` key and a minimal
``{"url", "formats"}`` body; the markdown lives at ``data.markdown`` and the title
/ source status at ``data.metadata``. The HTTP object is injected (a fake in
tests, a real ``HttpClient`` in production), and the client's job is only to make
the request and map HTTP failures onto the package's transient/fatal taxonomy —
never to log the key (KI-04).

A ``BUILTIN_BACKENDS`` registry + ``build_client`` factory keep the seam open for
a second backend later without the engine ever knowing which one it holds.
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Mapping, Optional

from .config import Config, resolve_api_key
from .errors import ConfigError, EmptyContentError, FatalFetchError, TransientFetchError
from .http import HttpClient, HttpFatal, HttpTransient


class FirecrawlClient:
    name = "firecrawl"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.firecrawl.dev/v1",
        formats: Optional[List[str]] = None,
        timeout: float = 60.0,
        http: Optional[HttpClient] = None,
    ) -> None:
        if not api_key:
            raise ConfigError("FirecrawlClient needs an API key")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.formats = list(formats) if formats else ["markdown"]
        self.http = http or HttpClient(timeout=timeout)

    def scrape(self, url: str) -> Dict[str, Any]:
        """Scrape one URL, returning Firecrawl's ``data`` object.

        Raises ``FatalFetchError`` for a bad URL / auth / 404, ``TransientFetchError``
        for a 429/5xx/timeout, and ``EmptyContentError`` for a 2xx with no markdown.
        """
        scheme = urllib.parse.urlparse(url).scheme.lower()
        if scheme not in ("http", "https"):
            raise FatalFetchError("not a scrapeable URL: {0!r}".format(url))

        endpoint = self.base_url + "/scrape"
        payload = {"url": url, "formats": self.formats}
        headers = {"Authorization": "Bearer {0}".format(self.api_key)}

        try:
            resp = self.http.post_json(endpoint, payload, headers=headers)
            body = resp.json()
        except HttpFatal as err:
            raise FatalFetchError("Firecrawl scrape failed: {0}".format(err))
        except HttpTransient as err:
            raise TransientFetchError("Firecrawl scrape unavailable: {0}".format(err))

        data = body.get("data") if isinstance(body, Mapping) else None
        data = dict(data) if isinstance(data, Mapping) else {}
        if not isinstance(data.get("markdown"), str) or not data["markdown"].strip():
            raise EmptyContentError("Firecrawl returned no markdown for {0}".format(url))
        return data


# type string -> backend class. A new backend registers here; the engine and CLI
# never learn which one they hold.
BUILTIN_BACKENDS = {"firecrawl": FirecrawlClient}


def build_client(
    config: Config,
    api_key: Optional[str] = None,
    http: Optional[HttpClient] = None,
    env: Optional[Mapping[str, str]] = None,
) -> FirecrawlClient:
    """Assemble the real backend named by ``config.backend``.

    This is the one place a live credential and a live ``HttpClient`` are wired
    together; tests build a client (or inject a fake ``http``) directly instead.
    """
    backend = BUILTIN_BACKENDS.get(config.backend)
    if backend is None:
        raise ConfigError(
            "unknown backend {0!r}; known: {1}".format(
                config.backend, ", ".join(sorted(BUILTIN_BACKENDS))
            )
        )
    key = api_key if api_key is not None else resolve_api_key(config, env=env)
    real_http = http or HttpClient(
        timeout=config.timeout,
        retries=config.retries,
        allow_insecure=config.allow_insecure,
    )
    return backend(
        api_key=key,
        base_url=config.base_url,
        formats=config.formats,
        http=real_http,
    )
