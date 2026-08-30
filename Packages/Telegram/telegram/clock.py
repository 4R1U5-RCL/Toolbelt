"""Time, injectable.

Two things depend on this being one seam. The signature carries a unix-ms
timestamp that the receiver checks against a five-minute skew window (TG-10), so
a test must be able to sign at an exact instant and assert the bytes. And
`telegram verify` waits on an n8n execution appearing, so that wait must be
interruptible rather than a blocking sleep.

Every timestamp written for humans is UTC ISO-8601 with a `Z` suffix.
"""

from __future__ import annotations

import datetime as _dt
import threading
import time
from typing import Optional

ISO = "%Y-%m-%dT%H:%M:%SZ"


class Clock:
    """Wall clock, monotonic clock, and an interruptible sleep."""

    def now(self) -> _dt.datetime:
        return _dt.datetime.now(_dt.timezone.utc)

    def iso(self) -> str:
        return self.now().strftime(ISO)

    def monotonic(self) -> float:
        return time.monotonic()

    def sleep(self, seconds: float, interrupt: Optional[threading.Event] = None) -> bool:
        """Sleep, returning True if woken early by `interrupt` being set.

        Waiting on a delivery confirmation must still die promptly on SIGINT, so
        the wait is an Event.wait, never time.sleep.
        """
        if seconds <= 0:
            return bool(interrupt and interrupt.is_set())
        if interrupt is None:
            time.sleep(seconds)
            return False
        return interrupt.wait(seconds)


def parse_iso(value: Optional[str]) -> Optional[_dt.datetime]:
    """Parse an ISO-8601 timestamp into an aware UTC datetime, or None.

    Tolerates the shapes real APIs emit: a `Z` suffix, fractional seconds, an
    explicit offset, or a naive string (assumed UTC — an API that returns a
    naive local timestamp is a bug we cannot fix from here, and assuming UTC at
    least keeps the arithmetic monotonic).
    """
    if not value or not isinstance(value, str):
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = _dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.timezone.utc)
    return parsed.astimezone(_dt.timezone.utc)


def age_seconds(since: Optional[str], now: _dt.datetime) -> Optional[float]:
    """Seconds between an ISO timestamp and `now`, or None if unparseable."""
    parsed = parse_iso(since)
    if parsed is None:
        return None
    return (now - parsed).total_seconds()
