"""A small, deliberately-not-``requests`` HTTP client on the standard library.

Zero dependencies is the whole point of this package, so the transport is
`urllib`. The two things worth caring about are baked in:

* **Retry policy is honest about transient vs fatal** — a 429/5xx/timeout is
  retried with full-jitter backoff that respects ``Retry-After`` (KI-05); a
  4xx auth/not-found is fatal and raised immediately, because retrying a bad key
  four times just hammers the API.
* **Determinism under test** — the clock (``sleep``) and the RNG (``rand``) are
  injected as callables, so a test can assert the exact backoff windows without
  waiting. The real network call is isolated in ``_attempt`` around
  ``urllib.request.urlopen``, which tests monkeypatch at that one seam.
"""

from __future__ import annotations

import json
import random
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

# Statuses where another attempt might plausibly help.
RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504, 507, 509})

DEFAULT_USER_AGENT = "toolbelt-scrape/1.0 (+stdlib-urllib)"


class HttpError(Exception):
    """Base HTTP failure, carrying the status and (truncated) body for context."""

    def __init__(self, message: str, status: Optional[int] = None, body: str = "") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class HttpTransient(HttpError):
    """Worth retrying — a 429, a 5xx, a timeout, a transport blip."""


class HttpFatal(HttpError):
    """Stop and surface it — a 4xx, a non-JSON body where JSON was required."""


@dataclass
class HttpResponse:
    status: int
    body: str
    headers: Dict[str, str] = field(default_factory=dict)

    def json(self) -> Any:
        """Parse the body as JSON.

        A 200 that is actually an HTML error/login page is a configuration
        mistake, not a payload — so a non-JSON body raises ``HttpFatal`` rather
        than a bare ``ValueError`` the caller might mistake for retryable (KI-07).
        """
        text = self.body.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except ValueError:
            raise HttpFatal(
                "expected JSON but got a {0}-char non-JSON body".format(len(self.body)),
                status=self.status,
                body=self.body[:300],
            )


class HttpClient:
    """A retrying JSON-friendly HTTP client with injected clock and RNG."""

    def __init__(
        self,
        timeout: float = 60.0,
        retries: int = 3,
        backoff_base: float = 1.5,
        backoff_cap: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
        allow_insecure: bool = False,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
    ) -> None:
        self.timeout = float(timeout)
        self.retries = int(retries)
        self.backoff_base = float(backoff_base)
        self.backoff_cap = float(backoff_cap)
        self.user_agent = user_agent
        self.allow_insecure = bool(allow_insecure)
        self._sleep = sleep
        self._rand = rand

    # -- public surface ----------------------------------------------------

    def post_json(
        self,
        url: str,
        payload: Any,
        headers: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        body = json.dumps(payload).encode("utf-8")
        hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
        if headers:
            hdrs.update(headers)
        return self.request("POST", url, headers=hdrs, body=body)

    def get_json(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        hdrs = {"Accept": "application/json"}
        if headers:
            hdrs.update(headers)
        return self.request("GET", url, headers=hdrs)

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
    ) -> HttpResponse:
        self._require_https(url)
        hdrs = {"User-Agent": self.user_agent}
        if headers:
            hdrs.update(headers)
        attempt = 0
        while True:
            attempt += 1
            try:
                return self._attempt(method, url, hdrs, body)
            except HttpFatal:
                raise
            except HttpTransient as err:
                if attempt > self.retries:
                    raise HttpTransient(
                        "gave up after {0} attempt(s): {1}".format(attempt, err),
                        status=err.status,
                        body=err.body,
                    )
                self._sleep(self._backoff(attempt, err))

    # -- internals ---------------------------------------------------------

    def _attempt(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[bytes],
    ) -> HttpResponse:
        request = urllib.request.Request(url=url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                raw = resp.read().decode("utf-8", "replace")
                status = getattr(resp, "status", None) or resp.getcode()
                hdrs = {k.lower(): v for k, v in dict(resp.headers).items()}
                return HttpResponse(status=int(status), body=raw, headers=hdrs)
        except urllib.error.HTTPError as err:
            detail = ""
            try:
                detail = err.read().decode("utf-8", "replace")
            except Exception:  # noqa: BLE001 - the body is best-effort context only
                detail = ""
            retry_after = err.headers.get("Retry-After") if err.headers else None
            self._raise_for_status(int(err.code), detail, retry_after)
        except (urllib.error.URLError, socket.timeout, TimeoutError) as err:
            raise HttpTransient("transport failure — {0}".format(err))

    def _raise_for_status(self, status: int, body: str, retry_after: Optional[str]) -> None:
        message = "HTTP {0} — {1}".format(status, (body or "")[:500])
        if status in RETRYABLE_STATUS:
            err = HttpTransient(message, status=status, body=body[:500])
            err.retry_after = _parse_retry_after(retry_after)  # type: ignore[attr-defined]
            raise err
        raise HttpFatal(message, status=status, body=body[:500])

    def _backoff(self, attempt: int, err: HttpTransient) -> float:
        # A server-set Retry-After wins over our own schedule.
        server = getattr(err, "retry_after", None)
        if server is not None:
            return min(float(server), self.backoff_cap)
        window = min(self.backoff_base ** attempt, self.backoff_cap)
        return window * self._rand()  # full jitter

    def _require_https(self, url: str) -> None:
        scheme = urllib.parse.urlparse(url).scheme.lower()
        if scheme == "https":
            return
        if scheme == "http" and self.allow_insecure:
            return
        raise HttpFatal("refusing non-HTTPS URL: {0}".format(_safe_url(url)))


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None  # HTTP-date form is not honored; our own backoff takes over


def _safe_url(url: str) -> str:
    """Drop the query string before anything reaches a log line (KI-04)."""
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
