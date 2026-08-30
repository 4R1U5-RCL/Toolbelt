"""Sources: everything that turns "some API" into a list of `Item`s.

A source is the only part of a poller that knows about the system being watched.
Three ways to get one, in increasing order of effort:

1. `"type": "http_json"` — declarative. A URL, an auth scheme, a path to the
   list, and a mapping from the API's status vocabulary to ours. Most REST APIs
   need nothing more.
2. `"type": "kaggle_submissions"` — a preset: `http_json` with the quirks of one
   API already encoded (see `IMPLEMENTATIONS.md`).
3. `"type": "python", "target": "mypkg.mod:MySource"` — a class you write, for
   pagination, GraphQL, or anything with real logic. Implement `fetch()` and you
   inherit dedup, retries, delivery and survivability for free.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Optional

from ..errors import ConfigError
from ..http import HttpClient
from .base import Source
from .http_json import HttpJsonSource
from .kaggle import KaggleSubmissionsSource

BUILTIN_SOURCES = {
    "http_json": HttpJsonSource,
    "kaggle_submissions": KaggleSubmissionsSource,
}

__all__ = ["Source", "HttpJsonSource", "KaggleSubmissionsSource", "build_source", "BUILTIN_SOURCES"]


def build_source(config: Dict[str, Any], resolver, client: Optional[HttpClient] = None) -> Source:
    """Instantiate the source described by a config block."""
    if not isinstance(config, dict):
        raise ConfigError("`source` must be an object")
    kind = config.get("type")
    if not kind:
        raise ConfigError("`source.type` is required (one of: {0}, python)".format(
            ", ".join(sorted(BUILTIN_SOURCES))))

    if kind == "python":
        cls = _import_target(config.get("target"))
    elif kind in BUILTIN_SOURCES:
        cls = BUILTIN_SOURCES[kind]
    else:
        raise ConfigError("unknown source type {0!r}; known types: {1}, python".format(
            kind, ", ".join(sorted(BUILTIN_SOURCES))))

    return cls(config, resolver, client)


def _import_target(target: Optional[str]):
    """Load `module:ClassName` for a custom source."""
    if not target or ":" not in target:
        raise ConfigError('source.target must be "module.path:ClassName" for type "python"')
    module_name, class_name = target.split(":", 1)
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        raise ConfigError("cannot import custom source module {0!r}: {1}".format(module_name, exc))
    try:
        cls = getattr(module, class_name)
    except AttributeError:
        raise ConfigError("module {0!r} has no attribute {1!r}".format(module_name, class_name))
    if not issubclass(cls, Source):
        raise ConfigError("{0} must subclass poller.sources.Source".format(target))
    return cls
