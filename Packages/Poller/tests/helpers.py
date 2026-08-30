"""Test doubles: a controllable clock, a scriptable source, and sinks that fail
in each of the ways a real rail fails.

Everything here exists so the whole suite runs offline in well under a second —
a poller's interesting behaviour happens over hours, and tests that cannot fast
forward do not get written.
"""

from __future__ import annotations

import datetime as dt
import logging
import os
import sys
from typing import List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from poller.clock import ISO  # noqa: E402
from poller.log import configure, set_level  # noqa: E402
from poller.errors import FatalSinkError, SinkError  # noqa: E402
from poller.model import Item, ItemState  # noqa: E402
from poller.sinks import Sink  # noqa: E402
from poller.sources.base import Source  # noqa: E402


# Tests assert on behaviour, not log lines; keep the suite output readable.
# Pinned rather than merely set, so the CLI tests' own configure() calls cannot
# turn logging back on for everything that runs after them.
set_level(logging.CRITICAL)
configure()


class FakeClock:
    """A clock that only moves when the test says so."""

    def __init__(self, start: str = "2026-08-30T00:00:00Z"):
        self._now = dt.datetime.strptime(start, ISO).replace(tzinfo=dt.timezone.utc)
        self._monotonic = 0.0
        self.slept: List[float] = []

    def now(self) -> dt.datetime:
        return self._now

    def iso(self) -> str:
        return self._now.strftime(ISO)

    def monotonic(self) -> float:
        return self._monotonic

    def sleep(self, seconds: float, interrupt=None) -> bool:
        self.slept.append(seconds)
        self.advance(seconds)
        return bool(interrupt and interrupt.is_set())

    def advance(self, seconds: float) -> None:
        self._now = self._now + dt.timedelta(seconds=seconds)
        self._monotonic += seconds


class ScriptedSource(Source):
    """Returns a queued list of Items (or raises a queued exception) per fetch."""

    name = "scripted"

    def __init__(self, script: List[object], preflight_ok: bool = True):
        self.script = list(script)
        self.calls = 0
        self.preflight_ok = preflight_ok

    def fetch(self) -> List[Item]:
        self.calls += 1
        step = self.script[min(self.calls - 1, len(self.script) - 1)]
        if isinstance(step, Exception):
            raise step
        return list(step)

    def preflight(self) -> None:
        if self.preflight_ok:
            return
        self.fetch()

    def describe(self) -> str:
        return "scripted source"


class RecordingSink(Sink):
    """Captures every delivered message."""

    type_name = "recording"

    def __init__(self, name: str = "recording", reasons=None, when: str = "always"):
        super().__init__({"name": name, "reasons": reasons, "when": when}, resolver=None)
        self.messages: List[str] = []
        self.events: List[object] = []

    def send(self, message: str, event) -> None:
        self.messages.append(message)
        self.events.append(event)


class FlakySink(Sink):
    """Fails `fail_times` deliveries with a retryable error, then succeeds."""

    type_name = "flaky"

    def __init__(self, name: str = "flaky", fail_times: int = 1):
        super().__init__({"name": name}, resolver=None)
        self.fail_times = fail_times
        self.attempts = 0
        self.messages: List[str] = []

    def send(self, message: str, event) -> None:
        self.attempts += 1
        if self.attempts <= self.fail_times:
            raise SinkError("simulated transient failure {0}".format(self.attempts))
        self.messages.append(message)


class DeadSink(Sink):
    """Always fails fatally — the revoked-token case."""

    type_name = "dead"

    def __init__(self, name: str = "dead"):
        super().__init__({"name": name}, resolver=None)
        self.attempts = 0

    def send(self, message: str, event) -> None:
        self.attempts += 1
        raise FatalSinkError("simulated revoked credential")


def item(key: str, state: str = ItemState.SETTLED, **fields) -> Item:
    return Item(key=key, state=state, title=fields.get("description", key), fields=fields)


def settled(key: str, score: str = "1.000") -> Item:
    return item(key, ItemState.SETTLED, score=score, description="sub-{0}".format(key))


def pending(key: str) -> Item:
    return item(key, ItemState.PENDING, score=None, description="sub-{0}".format(key))


def failed(key: str, error: str = "kernel error") -> Item:
    return item(key, ItemState.FAILED, error=error, description="sub-{0}".format(key))
