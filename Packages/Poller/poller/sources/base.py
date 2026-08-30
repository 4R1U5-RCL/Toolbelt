"""The Source contract."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..http import HttpClient
from ..model import Item


class Source:
    """Base class for everything the engine can watch.

    Subclasses need only `fetch`. `preflight` defaults to one real fetch, which
    is the cheapest honest answer to "are the credentials good?" — and asking it
    at startup is the difference between a nine-hour silent 401 loop and a
    two-second error message (KI-05).
    """

    #: Shown in logs and reports.
    name = "source"

    def __init__(self, config: Dict[str, Any], resolver, client: Optional[HttpClient] = None):
        self.config = config or {}
        self.resolver = resolver
        self.name = self.config.get("name") or self.name
        self.client = client or HttpClient(
            timeout=float(self.config.get("timeout_seconds", 30)),
            retries=int(self.config.get("retries", 4)),
            allow_insecure=bool(self.config.get("allow_insecure", False)),
        )

    def fetch(self) -> List[Item]:
        """Return the current contents of the watched collection.

        Must raise `TransientSourceError` for anything worth retrying and
        `FatalSourceError` for anything a human has to fix.
        """
        raise NotImplementedError

    def preflight(self) -> None:
        """Fail fast at startup on bad credentials or an unreachable endpoint."""
        self.fetch()

    def describe(self) -> str:
        """One line, safe to log — never include credentials or query strings."""
        return self.name
