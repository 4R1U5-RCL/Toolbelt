"""Durable state: what has been seen, and what has actually been delivered.

This module is where "the poller fired twice" and "the poller never fired" are
both prevented, and they need different guarantees:

* **At most one report per event** comes from the dedup ledger keyed on
  `item_key:state`.
* **At least one delivery attempt per sink** comes from recording delivery
  *per sink*, so a crash between the Slack post and the Telegram ping resends
  only Telegram on the next tick (KI-06).

Writes are atomic (temp file + `os.replace` + fsync) because the alternative —
a truncated JSON state file after a container stop — silently resets the whole
memory of the watch (KI-07).
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, List, Optional

from .clock import Clock
from .log import get_logger
from .model import Event, Item

SCHEMA_VERSION = 1


@dataclass
class Record:
    """One reportable event and its per-sink delivery ledger."""

    dedup_key: str
    reason: str
    title: str
    body: str
    severity: str = "info"
    item_key: str = ""
    item_state: str = ""
    context: Dict[str, str] = field(default_factory=dict)
    first_seen: str = ""
    delivered: List[str] = field(default_factory=list)
    failures: Dict[str, str] = field(default_factory=dict)
    fatal: Dict[str, str] = field(default_factory=dict)   # sink -> why it will never work
    attempts: int = 0
    seeded: bool = False       # suppressed on first run; never delivered
    abandoned: bool = False    # retry budget spent; a human needs to look

    def outstanding(self, sink_names: Iterable[str]) -> List[str]:
        """Sinks that still owe a delivery for this record.

        Sinks that failed fatally are excluded: a revoked Slack token will not
        heal on tick 40, and burning the retry budget on it would starve the
        rails that still work.
        """
        if self.seeded or self.abandoned:
            return []
        return [name for name in sink_names
                if name not in self.delivered and name not in self.fatal]

    def to_event(self) -> Event:
        """Rebuild the deliverable event from the ledger.

        Reports survive a restart because the rendered context is stored, not
        recomputed: the source may no longer return the row at all by the time
        a retry succeeds.
        """
        item = None
        if self.item_key:
            item = Item(key=self.item_key, state=self.item_state,
                        title=self.title, fields=dict(self.context))
        return Event(
            reason=self.reason,
            dedup_key=self.dedup_key,
            title=self.title,
            body=self.body,
            severity=self.severity,
            item=item,
            extra=dict(self.context) if item is None else {},
        )

    def is_complete(self, sink_names: Iterable[str]) -> bool:
        return not self.outstanding(sink_names)


class Store:
    """The on-disk memory of one poller, loaded once and saved after each change."""

    def __init__(self, path: str, clock: Optional[Clock] = None, max_records: int = 2000):
        self.path = os.path.expanduser(path)
        self.clock = clock or Clock()
        self.max_records = max_records
        self.created_at: str = ""
        self.seeded_at: Optional[str] = None
        self.first_seen: Dict[str, str] = {}   # item_key -> when we first observed it
        self.records: Dict[str, Record] = {}
        self.was_fresh: bool = True            # no usable state file existed
        self._dirty: bool = False              # nothing to write until something changes
        self._load()

    # -- lifecycle -------------------------------------------------------------

    def _load(self) -> None:
        if not os.path.isfile(self.path):
            self.created_at = self.clock.iso()
            return
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                raw = json.load(handle)
        except (ValueError, OSError) as exc:
            # Corrupt or unreadable: keep the evidence, start clean, and let the
            # seed pass suppress history rather than replaying every past event.
            backup = "{0}.corrupt-{1}".format(self.path, self.clock.iso().replace(":", ""))
            try:
                shutil.copy2(self.path, backup)
            except OSError:
                backup = "<backup failed>"
            get_logger().error("state file unreadable (%s); preserved at %s, starting fresh",
                               exc, backup)
            self.created_at = self.clock.iso()
            return

        if raw.get("schema") != SCHEMA_VERSION:
            get_logger().warning("state schema %r != %d; starting fresh",
                                 raw.get("schema"), SCHEMA_VERSION)
            self.created_at = self.clock.iso()
            return

        self.created_at = raw.get("created_at") or self.clock.iso()
        self.seeded_at = raw.get("seeded_at")
        self.first_seen = dict(raw.get("first_seen") or {})
        for key, value in (raw.get("records") or {}).items():
            self.records[key] = Record(**value)
        self.was_fresh = False

    def save(self, force: bool = False) -> None:
        """Write the whole state atomically, but only if something changed.

        An idle tick must not cost an fsync: on a slow overlay filesystem that
        turned a poll interval into several seconds of I/O for no new facts.
        """
        if not (self._dirty or force):
            return
        payload = {
            "schema": SCHEMA_VERSION,
            "created_at": self.created_at,
            "updated_at": self.clock.iso(),
            "seeded_at": self.seeded_at,
            "first_seen": self.first_seen,
            "records": {key: asdict(rec) for key, rec in self.records.items()},
        }
        write_json_atomic(self.path, payload)
        self._dirty = False

    # -- queries ---------------------------------------------------------------

    def knows(self, dedup_key: str) -> bool:
        return dedup_key in self.records

    def get(self, dedup_key: str) -> Optional[Record]:
        return self.records.get(dedup_key)

    def undelivered(self, sink_names: Iterable[str], max_attempts: int) -> List[Record]:
        """Records still owing a delivery and still inside their retry budget.

        Returned oldest-first so a backlog drains in the order it happened.
        """
        names = list(sink_names)
        pending = [
            rec for rec in self.records.values()
            if rec.outstanding(names) and rec.attempts < max_attempts
        ]
        return sorted(pending, key=lambda rec: rec.first_seen)

    def stats(self) -> Dict[str, int]:
        return {
            "records": len(self.records),
            "seeded": sum(1 for r in self.records.values() if r.seeded),
            "abandoned": sum(1 for r in self.records.values() if r.abandoned),
            "tracked_items": len(self.first_seen),
        }

    # -- mutations -------------------------------------------------------------

    def observe(self, item_key: str) -> str:
        """Record the first time an item was ever seen; returns that timestamp.

        This is the clock staleness is measured against, so an item that sits
        pending past its SLA can be reported instead of quietly waited on.
        """
        if item_key not in self.first_seen:
            self.first_seen[item_key] = self.clock.iso()
            self._dirty = True
        return self.first_seen[item_key]

    def enroll(self, event: Event, seeded: bool = False) -> Record:
        """Create (or return) the ledger record for an event."""
        existing = self.records.get(event.dedup_key)
        if existing:
            return existing
        record = Record(
            dedup_key=event.dedup_key,
            reason=event.reason,
            title=event.title,
            body=event.body,
            severity=event.severity,
            item_key=event.item.key if event.item else "",
            item_state=event.item.state if event.item else "",
            context=event.context(),
            first_seen=self.clock.iso(),
            seeded=seeded,
        )
        self.records[event.dedup_key] = record
        self._dirty = True
        self._prune()
        return record

    def mark_delivered(self, record: Record, sink_name: str) -> None:
        if sink_name not in record.delivered:
            record.delivered.append(sink_name)
        record.failures.pop(sink_name, None)
        self._dirty = True

    def mark_failed(self, record: Record, sink_name: str, reason: str, fatal: bool = False) -> None:
        record.failures[sink_name] = reason
        self._dirty = True
        if fatal:
            record.fatal[sink_name] = reason
            get_logger().error("sink %r will not be retried for %s: %s",
                               sink_name, record.dedup_key, reason)

    def note_attempt(self, record: Record, max_attempts: int) -> None:
        """Count one delivery sweep against the record's retry budget."""
        record.attempts += 1
        self._dirty = True
        if record.attempts >= max_attempts and record.failures:
            record.abandoned = True
            get_logger().error(
                "giving up on %s after %d attempts; undelivered to %s",
                record.dedup_key, record.attempts, ", ".join(sorted(record.failures)),
            )

    def mark_seeded(self) -> None:
        self.seeded_at = self.clock.iso()
        self._dirty = True

    def _prune(self) -> None:
        """Bound the file's growth by dropping the oldest fully-settled records.

        Only records that owe nothing are eligible, and the drop is logged: a
        pruned key that reappears would be reported a second time, so the number
        must stay large relative to how many items an API keeps returning.
        """
        if len(self.records) <= self.max_records:
            return
        droppable = sorted(
            (rec for rec in self.records.values() if not rec.failures and not rec.abandoned),
            key=lambda rec: rec.first_seen,
        )
        excess = len(self.records) - self.max_records
        for record in droppable[:excess]:
            del self.records[record.dedup_key]
            self.first_seen.pop(record.item_key, None)
        if excess > 0:
            self._dirty = True
            get_logger().info("pruned %d old state records (cap %d)", excess, self.max_records)


def write_json_atomic(path: str, payload: dict) -> None:
    """Write JSON so a reader never observes a half-written file."""
    path = os.path.expanduser(path)
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    temp = "{0}.tmp.{1}".format(path, os.getpid())
    with open(temp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
    # fsync the directory too, so the rename itself survives a hard stop.
    try:
        dir_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:  # pragma: no cover - not all filesystems allow this
        pass
