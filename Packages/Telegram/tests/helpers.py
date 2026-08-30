"""Shared test fixtures: a fake env, a fake clock, and a recording HTTP client.

Every test in this suite runs offline. Nothing here opens a socket, and the two
tests that reach for an external tool (`node`, the Poller package) skip
explicitly rather than silently passing when it is absent.
"""

from __future__ import annotations

import os
import sys
import threading
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram.http import HttpFatal, HttpResponse, HttpTransient  # noqa: E402
from telegram.log import set_level  # noqa: E402

# Keep the suite quiet: the package logs warnings deliberately, and the ones
# under test are asserted on rather than read off the terminal.
import logging  # noqa: E402
from telegram.log import configure  # noqa: E402
set_level(logging.CRITICAL)
configure()  # apply the pinned level; otherwise logging's last-resort handler
             # prints every deliberate warning to stderr and buries the results


class FakeResolver:
    """Stands in for EnvResolver without touching a real .env."""

    REF_PREFIX = "@env:"

    def __init__(self, values: Optional[Dict[str, str]] = None, env_file: str = "<fake>"):
        self.values = dict(values or {})
        self.env_file = env_file

    def get(self, name: str, required: bool = True):
        value = self.values.get(name)
        if not value and required:
            from telegram.errors import ConfigError
            raise ConfigError("required environment value {0!r} not found".format(name))
        return value

    def present(self, name: str) -> bool:
        return bool(self.values.get(name))

    def resolve(self, value, required: bool = True):
        if isinstance(value, str) and value.startswith(self.REF_PREFIX):
            return self.get(value[len(self.REF_PREFIX):], required=required)
        return value


class FakeClock:
    """A clock that does not advance unless told to, and never really sleeps."""

    def __init__(self, epoch_ms: int = 1_756_500_000_000):
        self.epoch_ms = epoch_ms
        self.slept: List[float] = []
        self._monotonic = 0.0

    def now(self):
        import datetime as dt
        return dt.datetime.fromtimestamp(self.epoch_ms / 1000.0, tz=dt.timezone.utc)

    def iso(self) -> str:
        return self.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    def monotonic(self) -> float:
        return self._monotonic

    def advance(self, seconds: float) -> None:
        self._monotonic += seconds
        self.epoch_ms += int(seconds * 1000)

    def sleep(self, seconds: float, interrupt: Optional[threading.Event] = None) -> bool:
        self.slept.append(seconds)
        self.advance(seconds)
        return bool(interrupt and interrupt.is_set())


class RecordingClient:
    """An HttpClient stand-in that records calls and replays scripted answers."""

    def __init__(self, responses: Optional[List[Any]] = None):
        #: Each entry is an HttpResponse, or an exception instance to raise.
        self.responses = list(responses or [])
        self.calls: List[Dict[str, Any]] = []

    def request(self, method, url, headers=None, body=None, params=None) -> HttpResponse:
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {}),
                           "body": body, "params": dict(params or {})})
        if not self.responses:
            return HttpResponse(status=200, body=b'{"ok":true}', headers={})
        answer = self.responses.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    def get_json(self, url, headers=None, params=None):
        return self.request("GET", url, headers=headers, params=params).json()

    @property
    def last(self) -> Dict[str, Any]:
        return self.calls[-1]


def ok(payload: bytes = b'{"ok":true}', status: int = 200,
       headers: Optional[Dict[str, str]] = None) -> HttpResponse:
    return HttpResponse(status=status, body=payload, headers=headers or {})


__all__ = ["FakeResolver", "FakeClock", "RecordingClient", "ok",
           "HttpFatal", "HttpTransient", "HttpResponse"]
