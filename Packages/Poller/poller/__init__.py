"""poller — a source-agnostic watch-and-report engine.

Poll *any* collection endpoint, detect items that reach a terminal state, and
report each one exactly once through a fan-out of sinks.

The package is deliberately dependency-free (Python 3.9+ standard library only)
so it runs unchanged inside the /studio container, on a bare VPS, or under cron
on a laptop — the three places pollers have historically been asked to live.

Public surface:

    from poller import Engine, load_config, build_source, build_sinks, Supervisor

Everything else is an implementation detail and may change.
"""

from .config import Config, load_config
from .engine import Engine
from .model import Event, Item, ItemState
from .sinks import build_sinks
from .sources import build_source
from .supervisor import Supervisor

__version__ = "2.0.0"

__all__ = [
    "Config",
    "Engine",
    "Event",
    "Item",
    "ItemState",
    "__version__",
    "Supervisor",
    "build_sinks",
    "build_source",
    "load_config",
]
