"""The engine: the loop, and everything that keeps it honest.

Read this file as the answer to four questions a poller must be able to answer
about itself:

* *Did anything happen?* — `tick` fetches, classifies, and enrolls one record
  per newly-terminal item, keyed so nothing is reported twice.
* *Did the report get out?* — `_dispatch` drains the delivery ledger every tick,
  per sink, retrying what failed and never re-sending what landed.
* *Is it still alive?* — a heartbeat file is rewritten every tick and `poller
  status` reads it; a silent death is therefore observable from outside.
* *Did it stop?* — every exit path emits an event. A watch that ends without
  telling anyone is the failure that motivated this package: a poller quietly
  self-exited, the next submission was never watched, and a real result was
  missed (KI-02).
"""

from __future__ import annotations

import os
import random
import signal
import threading
from typing import Dict, List, Optional, Sequence

from .clock import Clock, age_seconds
from .config import Config
from .errors import (AlreadyRunning, FatalSinkError, FatalSourceError, SinkError,
                     TransientSourceError)
from .lock import InstanceLock
from .log import get_logger
from .model import Event, EventReason, Item, ItemState
from .render import render
from .sinks import Sink
from .supervisor import ON_LOSS_FALLBACK, Supervisor
from .sinks import WHEN_FALLBACK
from .sources.base import Source
from .state import Store, write_json_atomic

EXIT_OK = 0
EXIT_FATAL = 2
EXIT_LOCKED = 3


class Engine:
    """Owns one watch: a source, a set of sinks, and the state between ticks."""

    def __init__(
        self,
        config: Config,
        source: Source,
        sinks: Sequence[Sink],
        store: Optional[Store] = None,
        clock: Optional[Clock] = None,
        lock: Optional[InstanceLock] = None,
        rand: Optional[random.Random] = None,
        supervisor: Optional[Supervisor] = None,
    ):
        self.config = config
        self.source = source
        self.sinks = list(sinks)
        self.clock = clock or Clock()
        self.store = store or Store(config.state_file, clock=self.clock,
                                    max_records=config.max_records)
        self.lock = lock or InstanceLock(config.lock_file, name=config.name, clock=self.clock)
        self.supervisor = supervisor or Supervisor(config.supervisor, clock=self.clock)
        self.rand = rand or random.Random()
        self.log = get_logger()

        self.stop_event = threading.Event()
        # Identifies this run's lifecycle events. The pid disambiguates two runs
        # started inside the same second — a real case under a per-minute cron.
        self.run_id = "{0}#{1}".format(self.clock.iso(), os.getpid())
        self.ticks = 0
        self.consecutive_failures = 0
        self.last_error = ""
        self._degraded_announced = False
        self._sink_names = [sink.name for sink in self.sinks]

    # -- lifecycle -------------------------------------------------------------

    def run(self, once: bool = False, seed: Optional[bool] = None, force: bool = False) -> int:
        """Run the watch to completion. Returns a process exit code."""
        try:
            self.lock.acquire(force=force)
        except AlreadyRunning as exc:
            self.log.error("%s", exc)      # the message names the incumbent pid
            return EXIT_LOCKED
        except OSError as exc:
            self.log.error("cannot take the lock at %s: %s", self.config.lock_file, exc)
            return EXIT_FATAL

        self._install_signal_handlers()
        stop_reason = "unknown"
        exit_code = EXIT_OK
        try:
            self._startup(seed, once)
            stop_reason = self._loop(once)
        except FatalSourceError as exc:
            stop_reason = "fatal source error: {0}".format(exc)
            self.log.error("%s", stop_reason)
            self._emit_lifecycle(EventReason.WATCH_FAILED, stop_reason, severity="error")
            self._write_heartbeat(status="failed", reason=stop_reason)
            exit_code = EXIT_FATAL
        except Exception as exc:  # unexpected: still report before dying (KI-02)
            stop_reason = "unhandled error: {0!r}".format(exc)
            self.log.exception("poller crashed")
            self._emit_lifecycle(EventReason.WATCH_FAILED, stop_reason, severity="error")
            self._write_heartbeat(status="failed", reason=stop_reason)
            exit_code = EXIT_FATAL
        else:
            if self.config.notify_on_end:
                self._emit_lifecycle(EventReason.WATCH_ENDED, stop_reason,
                                     severity="warn" if stop_reason != "single tick" else "info")
            self._write_heartbeat(status="ended", reason=stop_reason)
        finally:
            self.store.save()
            self.lock.release()
            self.log.info("watch finished (%s) after %d tick(s)", stop_reason, self.ticks)
        return exit_code

    def _startup(self, seed: Optional[bool], once: bool = False) -> None:
        self.log.info("poller %r watching %s every %ss (limit %s, supervisor %s)",
                      self.config.name, self.source.describe(),
                      self.config.interval_seconds, self._duration_text(),
                      self.supervisor.describe())
        fallback = [s.name for s in self.sinks if s.when == WHEN_FALLBACK]
        if fallback and not self.supervisor.configured:
            self.log.warning(
                "fallback rail(s) %s are configured but no supervisor is — they will "
                "never activate", ", ".join(fallback))
        should_seed = self.config.seed_on_first_run if seed is None else seed
        if self.store.was_fresh and should_seed:
            self._seed()
        else:
            if self.store.was_fresh:
                self.log.warning("no seed: every currently-terminal item will be reported")
            if not once:
                # Fail fast on bad credentials before committing to a long watch.
                # A single-tick run needs no separate probe — the tick itself is
                # one, and doubling every cron tick's API calls is not free.
                self.source.preflight()
        if self.config.notify_on_start:
            self._emit_lifecycle(EventReason.WATCH_STARTED, "started", severity="info")

    def _seed(self) -> None:
        """Record what already exists so a first run reports history, not news (KI-15).

        The count is logged (and available in the state file) because a silent
        seed is indistinguishable from a poller that saw nothing at all.
        """
        items = self.source.fetch()
        suppressed = 0
        for item in items:
            self.store.observe(item.key)
            if self._is_reportable(item):
                self.store.enroll(self._item_event(item), seeded=True)
                suppressed += 1
        self.store.mark_seeded()
        self.store.save()
        self.log.info("seeded from %d existing item(s); %d already-terminal item(s) "
                      "recorded as seen and will NOT be reported", len(items), suppressed)

    def _loop(self, once: bool) -> str:
        deadline = None
        if self.config.max_duration_seconds > 0:
            deadline = self.clock.monotonic() + self.config.max_duration_seconds

        while True:
            self.tick()
            if once:
                return "single tick"
            if self.stop_event.is_set():
                return "stop signal received"
            if deadline is not None and self.clock.monotonic() >= deadline:
                return "max duration reached ({0})".format(self._duration_text())
            if self.clock.sleep(self._next_delay(), self.stop_event):
                return "stop signal received"

    # -- the tick --------------------------------------------------------------

    def tick(self) -> List[Event]:
        """One poll: fetch, classify, enroll, deliver, heartbeat."""
        self.ticks += 1
        events: List[Event] = []
        # Before acting: know whether anyone is still listening. Checking here
        # rather than after dispatch means a successor rail is told *why* it
        # woke up before it is handed this tick's reports.
        self._check_supervisor()
        try:
            items = self.source.fetch()
        except TransientSourceError as exc:
            self._note_fetch_failure(exc)
            self._write_heartbeat(status="degraded", reason=str(exc))
            self._dispatch()  # a backlog can still drain while the source is down
            return events

        self.consecutive_failures = 0
        self._degraded_announced = False
        for item in items:
            first_seen = self.store.observe(item.key)
            event = self._event_for(item, first_seen)
            if event and not self.store.knows(event.dedup_key):
                self.store.enroll(event)
                events.append(event)
                self.log.info("new event: %s (%s)", event.dedup_key, event.reason)

        self.store.save()
        self._dispatch()
        self._maybe_heartbeat_ping()
        self._write_heartbeat(status="running", items=len(items))
        self.log.debug("tick %d: %d item(s), %d new event(s)", self.ticks, len(items), len(events))
        return events

    def _event_for(self, item: Item, first_seen: str) -> Optional[Event]:
        """Decide whether this observation of an item is worth reporting."""
        if self._is_reportable(item):
            return self._item_event(item)
        # A slow item and a dead poller look identical from outside; the SLA
        # signal is what tells them apart (KI-18).
        if item.state == ItemState.PENDING and self.config.stale_after_seconds > 0:
            age = age_seconds(first_seen, self.clock.now())
            if age is not None and age >= self.config.stale_after_seconds:
                return self._item_event(item, reason=EventReason.STALE,
                                        dedup_key="{0}:stale".format(item.key),
                                        severity="warn")
        return None

    def _is_reportable(self, item: Item) -> bool:
        return item.state in self.config.notify_states

    def _item_event(self, item: Item, reason: Optional[str] = None,
                    dedup_key: Optional[str] = None, severity: Optional[str] = None) -> Event:
        reason = reason or (EventReason.FAILED if item.state == ItemState.FAILED
                            else EventReason.SETTLED)
        severity = severity or ("error" if reason == EventReason.FAILED else "info")
        spec = self.config.template_for(reason)
        context = item.context()
        return Event(
            reason=reason,
            dedup_key=dedup_key or item.dedup_key,
            title=render(spec.get("title", "{title}"), context),
            body=render(spec.get("body", ""), context),
            severity=severity,
            item=item,
        )

    def _check_supervisor(self) -> None:
        """Notice when the session that launched this watch has gone away.

        The watch itself never depended on that session — it is a detached
        process. What it loses is the attention: reports keep landing with
        nobody reading them. Reporting the loss (and, if configured, switching
        on fallback rails) is what closes that gap.
        """
        lost = self.supervisor.poll()
        if lost:
            self._emit_lifecycle(EventReason.SUPERVISOR_LOST, lost, severity="warn")

    @property
    def fallback_active(self) -> bool:
        """True when fallback-only rails should deliver.

        Derived from the supervisor's current liveness rather than latched, so a
        restarted poller re-evaluates from scratch instead of inheriting a stale
        verdict.
        """
        return (not self.supervisor.alive
                and self.supervisor.on_loss == ON_LOSS_FALLBACK)

    # -- delivery --------------------------------------------------------------

    def _dispatch(self) -> None:
        """Drain the delivery ledger: every record, every sink that still owes one."""
        backlog = self.store.undelivered(self._sink_names, self.config.max_delivery_attempts)
        if not backlog:
            return
        for record in backlog:
            event = record.to_event()
            for sink in self.sinks:
                if sink.name in record.delivered or sink.name in record.fatal:
                    continue
                if sink.when == WHEN_FALLBACK and not self.fallback_active:
                    # A fallback rail stays dark while the supervisor is alive.
                    # Counted as delivered so the record can complete; if the
                    # supervisor dies later, it is *future* events that escalate,
                    # not a replay of everything already reported.
                    self.store.mark_delivered(record, sink.name)
                    continue
                if not sink.accepts(event):
                    # Filtered out by this sink's `reasons`: count it settled so
                    # the record can complete instead of retrying forever.
                    self.store.mark_delivered(record, sink.name)
                    continue
                try:
                    sink.deliver(event)
                except FatalSinkError as exc:
                    self.store.mark_failed(record, sink.name, str(exc), fatal=True)
                except SinkError as exc:
                    self.store.mark_failed(record, sink.name, str(exc))
                    self.log.warning("sink %r failed for %s: %s", sink.name, record.dedup_key, exc)
                except Exception as exc:  # a sink bug must not kill the watch
                    self.store.mark_failed(record, sink.name, "unexpected: {0!r}".format(exc))
                    self.log.exception("sink %r raised unexpectedly", sink.name)
                else:
                    self.store.mark_delivered(record, sink.name)
            self.store.note_attempt(record, self.config.max_delivery_attempts)
        self.store.save()

    def _emit_lifecycle(self, reason: str, detail: str, severity: str = "info") -> None:
        """Enroll and immediately deliver a watch-lifecycle event.

        If delivery fails here it stays in the ledger, so the *next* run of this
        poller delivers it late rather than losing it.
        """
        spec = self.config.template_for(reason)
        context = self._lifecycle_context(detail)
        event = Event(
            reason=reason,
            dedup_key="{0}:{1}".format(reason, self.run_id),
            title=render(spec.get("title", "{title}"), context),
            body=render(spec.get("body", ""), context),
            severity=severity,
            extra=context,  # run facts, not item fields; persisted with the record
        )
        self.store.enroll(event)
        self.store.save()
        self._dispatch()

    def _lifecycle_context(self, detail: str) -> Dict[str, str]:
        return {
            "poller": self.config.name,
            "source": self.source.describe(),
            "interval": str(int(self.config.interval_seconds)),
            "duration": self._duration_text(),
            "stop_reason": detail,
            "error": self.last_error,
            "failures": str(self.consecutive_failures),
            "ticks": str(self.ticks),
            "items": str(len(self.store.first_seen)),
            "run_id": self.run_id,
            "supervisor": self.supervisor.describe(),
        }

    # -- health ----------------------------------------------------------------

    def _note_fetch_failure(self, exc: Exception) -> None:
        self.consecutive_failures += 1
        self.last_error = str(exc)
        self.log.warning("fetch failed (%d consecutive): %s", self.consecutive_failures, exc)
        threshold = self.config.degraded_after_failures
        if threshold and self.consecutive_failures >= threshold and not self._degraded_announced:
            self._degraded_announced = True
            self._emit_lifecycle(EventReason.DEGRADED, self.last_error, severity="warn")

    def _maybe_heartbeat_ping(self) -> None:
        every = self.config.heartbeat_every_ticks
        if every and self.ticks % every == 0:
            self._emit_lifecycle(EventReason.HEARTBEAT, "alive", severity="info")

    def _write_heartbeat(self, status: str, reason: str = "", items: Optional[int] = None) -> None:
        """Rewrite the liveness file. Best-effort: never fail a tick over it."""
        payload = {
            "name": self.config.name,
            "pid": os.getpid(),
            "run_id": self.run_id,
            "status": status,
            "reason": reason,
            "updated_at": self.clock.iso(),
            "ticks": self.ticks,
            "interval_seconds": self.config.interval_seconds,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "items_last_tick": items,
            "source": self.source.describe(),
            "sinks": self._sink_names,
            "supervisor": self.supervisor.describe(),
            "supervisor_alive": self.supervisor.alive,
            "fallback_active": self.fallback_active,
            "state": self.store.stats(),
        }
        try:
            write_json_atomic(self.config.heartbeat_file, payload)
        except OSError as exc:  # pragma: no cover - disk full / read-only mount
            self.log.warning("could not write heartbeat file: %s", exc)

    # -- plumbing --------------------------------------------------------------

    def _next_delay(self) -> float:
        """Interval plus optional jitter, so N pollers do not stampede one API (KI-12)."""
        jitter = self.rand.uniform(0, self.config.jitter_seconds) if self.config.jitter_seconds else 0
        return self.config.interval_seconds + jitter

    def _duration_text(self) -> str:
        """A duration a human reads at a glance — this string ends up in reports."""
        seconds = self.config.max_duration_seconds
        if seconds <= 0:
            return "no limit"
        if seconds < 90:
            return "{0:g}s".format(round(seconds))
        if seconds < 5400:
            return "{0:g}m".format(round(seconds / 60))
        return "{0:g}h".format(round(seconds / 3600, 1))

    def _install_signal_handlers(self) -> None:
        """Turn SIGTERM/SIGINT into a clean, *reported* stop."""

        def handler(signum, _frame):
            self.log.info("signal %s received; finishing current tick", signum)
            self.stop_event.set()

        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):  # not the main thread (e.g. under test)
                pass
