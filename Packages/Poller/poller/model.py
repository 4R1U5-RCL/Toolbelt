"""The two values the engine moves around: Item (what a source sees) and Event
(what a sink delivers).

A source's only job is to turn whatever an API returns into `Item`s. Everything
downstream — dedup, staleness, templating, delivery — is written against these
two shapes and knows nothing about Kaggle, GitHub, or HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class ItemState:
    """The states a watched item can be in.

    Sources map their own vocabulary onto these four. Only `SETTLED` and
    `FAILED` are terminal; both are reportable, and reporting them *distinctly*
    is a requirement — a submission that errored is news, not noise (KI-08).
    """

    PENDING = "pending"
    SETTLED = "settled"
    FAILED = "failed"
    UNKNOWN = "unknown"

    TERMINAL = (SETTLED, FAILED)
    ALL = (PENDING, SETTLED, FAILED, UNKNOWN)


@dataclass(frozen=True)
class Item:
    """One row of the watched collection, normalized.

    `key` must be stable and unique for the lifetime of the item — an API's own
    immutable id (a submission ref, a run id), never an index or a
    human-typed description (KI-01).

    `fields` are the flattened, template-visible values a report can reference.
    They are stringified at render time, never eval'd.
    """

    key: str
    state: str
    title: str = ""
    fields: Dict[str, Any] = field(default_factory=dict)
    seen_at: Optional[str] = None  # ISO-8601 UTC, stamped by the engine

    @property
    def dedup_key(self) -> str:
        """The identity used for "have I already reported this?".

        Deliberately `key:state`, not `key`: an item observed as pending and
        later as settled must produce a *second* report, while two observations
        of the same settled item must produce only one.
        """
        return "{0}:{1}".format(self.key, self.state)

    @property
    def is_terminal(self) -> bool:
        return self.state in ItemState.TERMINAL

    def context(self) -> Dict[str, str]:
        """Flat string mapping for report templates."""
        ctx = {k: "" if v is None else str(v) for k, v in self.fields.items()}
        ctx.update(key=self.key, state=self.state, title=self.title)
        return ctx


@dataclass(frozen=True)
class Event:
    """A single thing worth telling a human about, addressed to every sink.

    `dedup_key` is what the delivery ledger records, so an event is delivered
    at-least-once per sink and reported at-most-once overall.
    """

    reason: str  # see EventReason
    dedup_key: str
    title: str
    body: str
    severity: str = "info"  # info | warn | error
    item: Optional[Item] = None
    #: Extra template fields for events that describe the *watch* rather than an
    #: item (run id, poll interval, stop reason). Stored with the record so a
    #: retry after a restart still renders the same report.
    extra: Dict[str, str] = field(default_factory=dict)

    def context(self) -> Dict[str, str]:
        ctx = dict(self.extra)
        if self.item:
            ctx.update(self.item.context())
        ctx.update(
            reason=self.reason,
            title=self.title,
            body=self.body,
            severity=self.severity,
        )
        return ctx


class EventReason:
    """Why an event fired. Sinks may filter on these."""

    SETTLED = "settled"          # an item reached a successful terminal state
    FAILED = "failed"            # an item reached an error terminal state
    STALE = "stale"              # an item has been pending past its SLA
    WATCH_STARTED = "watch_started"
    WATCH_ENDED = "watch_ended"  # clean exit: duration reached, or signal
    WATCH_FAILED = "watch_failed"  # fatal error: auth, unparseable source
    SUPERVISOR_LOST = "supervisor_lost"  # the session that launched the watch is gone
    DEGRADED = "degraded"        # N consecutive fetch failures, still trying
    HEARTBEAT = "heartbeat"      # periodic "still watching" ping

    LIFECYCLE = (WATCH_STARTED, WATCH_ENDED, WATCH_FAILED, DEGRADED, HEARTBEAT,
                 SUPERVISOR_LOST)
