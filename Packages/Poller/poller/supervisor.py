"""Watching the thing that started the watch.

A poller launched from an interactive session outlives that session by design —
it is a detached OS process. What does *not* survive is the attention: the
reports keep landing, but nobody is there to act on them.

This module answers one question each tick — "is my supervisor still alive?" —
so the engine can escalate when the answer changes (KI-19). Two signals are supported:

* **pid** — the supervising process id, probed the same way the instance lock
  probes its holder (`os.kill(pid, 0)` plus a `/proc` comparison; no `ps`).
  Inside a Claude Code session, `@env:CLAUDE_PID` captures it with no setup.
* **heartbeat_file** — a file the supervisor touches. Staler than
  `max_age_seconds` means gone. Use this when the supervisor is not a local
  process, or when liveness means "still working", not merely "still running".

A supervisor that was never configured is reported as present, so nothing
escalates by accident.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import Any, Dict, Optional

from .clock import Clock, age_seconds
from .lock import is_process_alive
from .log import get_logger

#: What to do when the supervisor goes away.
ON_LOSS_FALLBACK = "fallback"   # activate fallback sinks, and report the change
ON_LOSS_REPORT = "report"       # report the change only
ON_LOSS_IGNORE = "ignore"       # track it, do nothing
ON_LOSS_CHOICES = (ON_LOSS_FALLBACK, ON_LOSS_REPORT, ON_LOSS_IGNORE)


class Supervisor:
    """Liveness of whoever launched this poller."""

    def __init__(self, config: Optional[Dict[str, Any]], resolver=None,
                 clock: Optional[Clock] = None):
        config = config or {}
        self.clock = clock or Clock()
        self.on_loss = str(config.get("on_loss", ON_LOSS_FALLBACK))
        self.max_age_seconds = float(config.get("max_age_seconds", 300))
        self.heartbeat_file = config.get("heartbeat_file")
        self.label = config.get("label", "supervisor")
        self.pid = _coerce_pid(resolver.resolve(config.get("pid"), required=False)
                               if resolver else config.get("pid"))
        # Recorded once, at launch, so a pid recycled later cannot read as alive.
        self.cmdline = _cmdline_of(self.pid) if self.pid else None
        #: Level, refreshed by `poll()`. The engine reads this to decide whether
        #: fallback rails are active; `poll()` returns the edge, for reporting.
        self.alive = True
        self._was_alive = True

    @property
    def configured(self) -> bool:
        return bool(self.pid or self.heartbeat_file)

    def is_alive(self) -> bool:
        """True when no supervisor is configured, or the configured one is live."""
        if not self.configured:
            return True
        if self.pid and is_process_alive(self.pid, self.cmdline):
            return True
        if self.heartbeat_file:
            age = age_seconds(_mtime_iso(self.heartbeat_file, self.clock), self.clock.now())
            if age is not None and age <= self.max_age_seconds:
                return True
        return False

    def poll(self) -> Optional[str]:
        """Check liveness; return a description on the tick it is first lost.

        Returns None on every other tick — the loss is an edge, not a level, so
        it is reported once rather than every interval.
        """
        self.alive = self.is_alive()
        if self.alive or not self._was_alive:
            self._was_alive = self.alive
            return None
        self._was_alive = False
        detail = "pid {0}".format(self.pid) if self.pid else "heartbeat {0}".format(self.heartbeat_file)
        get_logger().warning("%s is gone (%s); the watch continues alone", self.label, detail)
        return "{0} ({1}) is no longer alive".format(self.label, detail)

    def describe(self) -> str:
        if not self.configured:
            return "none"
        return "{0} pid={1}".format(self.label, self.pid) if self.pid else \
            "{0} heartbeat={1}".format(self.label, self.heartbeat_file)


def _coerce_pid(value: Any) -> Optional[int]:
    try:
        pid = int(value)
    except (TypeError, ValueError):
        return None
    return pid if pid > 0 else None


def _cmdline_of(pid: int) -> Optional[str]:
    try:
        with open("/proc/{0}/cmdline".format(pid), "rb") as handle:
            return handle.read().decode("utf-8", "replace").replace("\x00", " ")
    except OSError:
        return None


def _mtime_iso(path: str, clock: Clock) -> Optional[str]:
    """The file's mtime as an ISO string, or None if it does not exist."""
    try:
        stamp = os.stat(os.path.expanduser(path)).st_mtime
    except OSError:
        return None
    return dt.datetime.fromtimestamp(stamp, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
