"""Configuration: one JSON file describes an entire poller.

The rule this package exists to enforce is that a new watch is a new *config*,
never an edited copy of a script (KI-16). Editing code per run is how a slug got baked
into a poller, how the copy drifted from the original, and how the next watch
silently reported on the wrong thing.

Unknown keys are warned about rather than ignored: a typo in `interval_seconds`
that silently keeps the 180s default is a bug you find six hours late.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .errors import ConfigError
from .log import get_logger
from .model import EventReason, ItemState

DEFAULT_STATE_DIR = "~/.poller"

#: Report text for each kind of event. Every value is a `str.format` template
#: over the item's fields plus `key`, `state`, `title`, `reason`.
DEFAULT_TEMPLATES: Dict[str, Dict[str, str]] = {
    EventReason.SETTLED: {
        "title": "Settled: {title}",
        "body": "id {key} · state {state}",
    },
    EventReason.FAILED: {
        "title": "FAILED: {title}",
        "body": "id {key} · state {state}\n{error}",
    },
    EventReason.STALE: {
        "title": "Still pending: {title}",
        "body": "id {key} has been pending past its SLA. Nothing is wrong with the poller.",
    },
    EventReason.WATCH_STARTED: {
        "title": "Poller started: {poller}",
        "body": "watching {source} every {interval}s for up to {duration}",
    },
    EventReason.WATCH_ENDED: {
        "title": "Poller stopped: {poller}",
        "body": "reason: {stop_reason}. Nothing is watching {source} now.",
    },
    EventReason.WATCH_FAILED: {
        "title": "Poller FAILED: {poller}",
        "body": "{stop_reason}\nNothing is watching {source} now — this needs a human.",
    },
    EventReason.DEGRADED: {
        "title": "Poller degraded: {poller}",
        "body": "{failures} consecutive fetch failures. Still retrying. Last error: {error}",
    },
    EventReason.HEARTBEAT: {
        "title": "Poller alive: {poller}",
        "body": "tick {ticks} · {items} items tracked · watching {source}",
    },
}

_KNOWN_KEYS = {
    "name", "env_file", "interval_seconds", "jitter_seconds", "max_duration_hours",
    "state_dir", "state_file", "heartbeat_file", "lock_file", "log_file",
    "notify_states", "stale_after_seconds", "heartbeat_every_ticks",
    "notify_on_start", "notify_on_end", "max_delivery_attempts", "max_records",
    "seed_on_first_run", "degraded_after_failures", "templates", "source", "sinks",
}


@dataclass
class Config:
    """A fully-resolved poller configuration."""

    name: str
    source: Dict[str, Any]
    sinks: List[Dict[str, Any]]
    env_file: Optional[str] = None

    # cadence
    interval_seconds: float = 180.0
    jitter_seconds: float = 0.0
    max_duration_hours: float = 12.0  # 0 = run until stopped

    # paths
    state_dir: str = DEFAULT_STATE_DIR
    state_file: str = ""
    heartbeat_file: str = ""
    lock_file: str = ""
    log_file: Optional[str] = None

    # behaviour
    notify_states: List[str] = field(default_factory=lambda: [ItemState.SETTLED, ItemState.FAILED])
    stale_after_seconds: float = 0.0        # 0 = never report a slow item
    heartbeat_every_ticks: int = 0          # 0 = no periodic "still alive" ping
    notify_on_start: bool = True
    notify_on_end: bool = True
    max_delivery_attempts: int = 5
    max_records: int = 2000
    seed_on_first_run: bool = True
    degraded_after_failures: int = 3
    templates: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # -- derived ---------------------------------------------------------------

    def __post_init__(self) -> None:
        base = os.path.expanduser(self.state_dir)
        self.state_file = os.path.expanduser(self.state_file or os.path.join(base, self.name + ".state.json"))
        self.heartbeat_file = os.path.expanduser(self.heartbeat_file or os.path.join(base, self.name + ".heartbeat.json"))
        self.lock_file = os.path.expanduser(self.lock_file or os.path.join(base, self.name + ".lock"))
        if self.log_file:
            self.log_file = os.path.expanduser(self.log_file)
        merged = {reason: dict(spec) for reason, spec in DEFAULT_TEMPLATES.items()}
        for reason, spec in (self.templates or {}).items():
            merged.setdefault(reason, {}).update(spec or {})
        self.templates = merged
        self._validate()

    def template_for(self, reason: str) -> Dict[str, str]:
        return self.templates.get(reason, {"title": "{title}", "body": "{body}"})

    @property
    def max_duration_seconds(self) -> float:
        return float(self.max_duration_hours) * 3600.0

    def _validate(self) -> None:
        if not self.name or not str(self.name).strip():
            raise ConfigError("`name` is required — it names the state, lock and heartbeat files")
        if any(ch in self.name for ch in "/\\ "):
            raise ConfigError("`name` must be a filename-safe slug (no spaces or slashes)")
        if self.interval_seconds < 1:
            raise ConfigError("`interval_seconds` must be at least 1")
        if self.jitter_seconds < 0:
            raise ConfigError("`jitter_seconds` cannot be negative")
        if self.max_duration_hours < 0:
            raise ConfigError("`max_duration_hours` cannot be negative (use 0 to run indefinitely)")
        if self.max_delivery_attempts < 1:
            raise ConfigError("`max_delivery_attempts` must be at least 1")
        unknown = set(self.notify_states) - set(ItemState.ALL)
        if unknown:
            raise ConfigError("`notify_states` contains unknown states: {0}; valid: {1}".format(
                ", ".join(sorted(unknown)), ", ".join(ItemState.ALL)))
        if not self.source:
            raise ConfigError("`source` is required")
        if not self.sinks:
            raise ConfigError("`sinks` must list at least one rail")


def load_config(path: str, overrides: Optional[Dict[str, Any]] = None) -> Config:
    """Read a JSON config file into a validated `Config`."""
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except FileNotFoundError:
        raise ConfigError("config file not found: {0}".format(expanded))
    except ValueError as exc:
        raise ConfigError("config file is not valid JSON ({0}): {1}".format(exc, expanded))
    if not isinstance(raw, dict):
        raise ConfigError("config file must contain a JSON object")
    raw.update(overrides or {})
    return from_dict(raw)


def from_dict(raw: Dict[str, Any]) -> Config:
    """Build a Config from an already-decoded mapping."""
    unknown = set(raw) - _KNOWN_KEYS
    if unknown:
        get_logger().warning(
            "ignoring unknown config keys: %s (typo? known keys: %s)",
            ", ".join(sorted(unknown)), ", ".join(sorted(_KNOWN_KEYS)),
        )
    accepted = {key: value for key, value in raw.items() if key in _KNOWN_KEYS}
    try:
        return Config(**accepted)
    except TypeError as exc:
        raise ConfigError("config is missing a required key: {0}".format(exc))
