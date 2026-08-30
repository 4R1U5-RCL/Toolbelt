"""A small, retrying HTTPS client built on urllib.

Deliberately not `requests`: this package must run where nothing can be
installed. What it adds over raw urlopen is the part that matters for an
unattended caller — timeouts on every call, exponential backoff with full
jitter, `Retry-After` support, and a hard split between "try again" and "stop,
a human must fix this".

Both the clock and the randomness are injectable so the backoff schedule is
deterministic under test.
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

from .log import get_logger

# Status codes worth trying again. Everything else in 4xx is a configuration
# defect: retrying a 401 for twelve hours is the failure mode this replaces.
RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504, 507, 509})


class HttpError(Exception):
    """Base for transport/protocol failures, carrying the status when known."""

    def __init__(self, message: str, status: int = 0, body: str = ""):
        super().__init__(message)
        self.status = status
        self.body = body


class HttpTransient(HttpError):
    """Expected to succeed later: timeout, reset, 429, 5xx."""


class HttpFatal(HttpError):
    """Will not fix itself: 401/403 (auth), 404 (wrong URL), 400/422 (bad request)."""


@dataclass
class HttpResponse:
    status: int
    body: bytes
    headers: Dict[str, str] = field(default_factory=dict)

    def json(self) -> Any:
        """Parse the body as JSON, raising HttpFatal on garbage.

        An endpoint that answers 200 with an HTML login page is a configuration
        error wearing a success code; treating it as fatal surfaces it instead
        of looping on it.
        """
        try:
            return json.loads(self.body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            preview = self.body[:200].decode("utf-8", "replace")
            raise HttpFatal(
                "response was not JSON ({0}); first 200 bytes: {1!r}".format(exc, preview),
                status=self.status,
            )


class HttpClient:
    """One HTTPS client per process. Reused across sends; holds no session state."""

    def __init__(
        self,
        timeout: float = 30.0,
        retries: int = 4,
        backoff_base: float = 1.5,
        backoff_cap: float = 60.0,
        user_agent: str = "achilles-telegram/1.0 (+stdlib-urllib)",
        allow_insecure: bool = False,
        sleep: Callable[[float], None] = time.sleep,
        rand: Callable[[], float] = random.random,
    ):
        self.timeout = timeout
        self.retries = retries
        self.backoff_base = backoff_base
        self.backoff_cap = backoff_cap
        self.user_agent = user_agent
        self.allow_insecure = allow_insecure
        self._sleep = sleep
        self._rand = rand

    # -- public ----------------------------------------------------------------

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> HttpResponse:
        """Perform one request, retrying transient failures up to `retries` times.

        Raises HttpFatal immediately on a non-retryable status, and HttpTransient
        once the retry budget is spent.
        """
        target = self._with_params(url, params)
        self._check_scheme(target)
        request_headers = {"User-Agent": self.user_agent}
        request_headers.update(headers or {})

        last: HttpError = HttpTransient("no attempt was made", status=0)
        for attempt in range(self.retries + 1):
            try:
                return self._attempt(method, target, request_headers, body)
            except HttpFatal:
                raise
            except HttpTransient as exc:
                last = exc
                if attempt == self.retries:
                    break
                delay = self._backoff(attempt, exc)
                get_logger().warning(
                    "%s %s failed (%s); retry %d/%d in %.1fs",
                    method, _safe_url(target), exc, attempt + 1, self.retries, delay,
                )
                self._sleep(delay)
        raise last

    def get_json(self, url: str, headers: Optional[Dict[str, str]] = None,
                 params: Optional[Dict[str, str]] = None) -> Any:
        return self.request("GET", url, headers=headers, params=params).json()

    def post_json(self, url: str, payload: Any, headers: Optional[Dict[str, str]] = None) -> HttpResponse:
        body = json.dumps(payload).encode("utf-8")
        merged = {"Content-Type": "application/json; charset=utf-8"}
        merged.update(headers or {})
        return self.request("POST", url, headers=merged, body=body)

    # -- internals -------------------------------------------------------------

    def _attempt(self, method: str, url: str, headers: Dict[str, str],
                 body: Optional[bytes]) -> HttpResponse:
        request = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return HttpResponse(
                    status=response.status,
                    body=response.read(),
                    headers={k.lower(): v for k, v in response.headers.items()},
                )
        except urllib.error.HTTPError as exc:
            payload = _read_error_body(exc)
            message = "HTTP {0}: {1}".format(exc.code, payload[:200] or exc.reason)
            if exc.code in RETRYABLE_STATUS:
                transient = HttpTransient(message, status=exc.code, body=payload)
                # A 429 that tells us how long to wait is worth more than our
                # own guess; carry it through to the backoff calculation.
                transient.retry_after = _header(exc, "Retry-After")
                raise transient
            raise HttpFatal(message, status=exc.code, body=payload)
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as exc:
            # DNS failure, refused connection, TLS reset, read timeout. All of
            # these are routinely transient on a long watch.
            raise HttpTransient("transport error: {0}".format(exc), status=0)

    def _backoff(self, attempt: int, exc: HttpError) -> float:
        """Full-jitter exponential backoff, floored by any Retry-After hint."""
        window = min(self.backoff_cap, self.backoff_base * (2 ** attempt))
        delay = self._rand() * window
        retry_after = _retry_after_seconds(exc)
        if retry_after is not None:
            delay = max(delay, min(retry_after, self.backoff_cap))
        return round(delay, 2)

    def _check_scheme(self, url: str) -> None:
        scheme = urllib.parse.urlparse(url).scheme.lower()
        if scheme == "https":
            return
        if scheme == "http" and self.allow_insecure:
            get_logger().warning("insecure http request permitted by config: %s", _safe_url(url))
            return
        raise HttpFatal(
            "refusing non-https URL {0!r} (set allow_insecure to override)".format(_safe_url(url))
        )

    @staticmethod
    def _with_params(url: str, params: Optional[Dict[str, str]]) -> str:
        if not params:
            return url
        separator = "&" if "?" in url else "?"
        return url + separator + urllib.parse.urlencode(params)


def _header(exc: urllib.error.HTTPError, name: str):
    """Best-effort header read off an HTTPError (its headers may be absent)."""
    headers = getattr(exc, "headers", None)
    return headers.get(name) if headers else None


def _read_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        return exc.read().decode("utf-8", "replace")
    except Exception:  # pragma: no cover - the error body is best-effort context
        return ""


def _retry_after_seconds(exc: HttpError) -> Optional[float]:
    """Extract a numeric Retry-After if the server sent one."""
    raw = getattr(exc, "retry_after", None)
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _safe_url(url: str) -> str:
    """URL with query string dropped — query strings carry API keys (TG-16)."""
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
