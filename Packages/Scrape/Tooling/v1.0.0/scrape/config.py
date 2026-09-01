"""Scrape configuration — one dataclass, loaded from flags and/or a JSON file.

A config never carries the API key itself: it names the *environment variable*
the key lives in (``api_key_env``, default ``FIRECRAWL_API_KEY``) and the key is
read from the process environment at run time and only ever placed in an
``Authorization`` header (KI-04). ``resolve_api_key`` raises a plain
``ConfigError`` naming the variable when it is unset — it never echoes a value.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from .errors import ConfigError

log = logging.getLogger("scrape.config")

DEFAULT_BASE_URL = "https://api.firecrawl.dev/v1"
DEFAULT_API_KEY_ENV = "FIRECRAWL_API_KEY"
# Firecrawl markdown for a big page can be enormous; this is both the default
# and the hard cap on how much we keep (KI-03), matching the studio ops client.
MAX_CHARS_CAP = 40_000
OUTPUT_FORMATS = ("markdown", "json", "text")


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


@dataclass
class Config:
    # backend
    backend: str = "firecrawl"
    base_url: str = DEFAULT_BASE_URL
    api_key_env: str = DEFAULT_API_KEY_ENV
    formats: List[str] = field(default_factory=lambda: ["markdown"])

    # translation / behaviour
    clean: bool = True
    max_chars: int = MAX_CHARS_CAP
    chunk: bool = False
    max_tokens: int = 1500
    overlap: int = 0
    out_format: str = "markdown"

    # http
    timeout: float = 60.0
    retries: int = 3
    allow_insecure: bool = False

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if "markdown" not in self.formats:
            # markdown is the LLM-ready payload this tool is built around.
            self.formats = ["markdown"] + [f for f in self.formats if f != "markdown"]
        if self.out_format not in OUTPUT_FORMATS:
            raise ConfigError(
                "out_format must be one of {0}, got {1!r}".format(
                    ", ".join(OUTPUT_FORMATS), self.out_format
                )
            )
        self.max_chars = _clamp(int(self.max_chars), 1, MAX_CHARS_CAP)
        if self.max_tokens < 1:
            raise ConfigError("max_tokens must be >= 1, got {0}".format(self.max_tokens))
        if self.overlap < 0 or self.overlap >= self.max_tokens:
            raise ConfigError(
                "overlap must be in [0, max_tokens), got {0}".format(self.overlap)
            )
        if self.retries < 0:
            raise ConfigError("retries must be >= 0, got {0}".format(self.retries))


_KNOWN_KEYS = set(Config().__dict__.keys())


def from_dict(data: Mapping[str, Any], overrides: Optional[Mapping[str, Any]] = None) -> Config:
    merged: Dict[str, Any] = dict(data or {})
    if overrides:
        merged.update({k: v for k, v in overrides.items() if v is not None})
    unknown = [k for k in merged if k not in _KNOWN_KEYS]
    for key in unknown:
        # Warn rather than silently drop — a typo'd key should be visible.
        log.warning("ignoring unknown config key: %s", key)
    accepted = {k: v for k, v in merged.items() if k in _KNOWN_KEYS}
    try:
        return Config(**accepted)
    except TypeError as err:
        raise ConfigError("bad config: {0}".format(err))


def load_config(
    path: Optional[str] = None,
    overrides: Optional[Mapping[str, Any]] = None,
) -> Config:
    """Load a Config from an optional JSON file, then apply flag overrides."""
    data: Dict[str, Any] = {}
    if path:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            raise ConfigError("config file not found: {0}".format(path))
        except ValueError as err:
            raise ConfigError("config file is not valid JSON ({0}): {1}".format(path, err))
        if not isinstance(data, dict):
            raise ConfigError("config file must be a JSON object: {0}".format(path))
    return from_dict(data, overrides)


def resolve_api_key(config: Config, env: Optional[Mapping[str, str]] = None) -> str:
    """Return the API key from the named env var, or raise ConfigError.

    Never prints or returns any hint of the value on failure — only the variable
    name, so a missing key is a clear, non-leaky error.
    """
    source = env if env is not None else os.environ
    key = (source.get(config.api_key_env) or "").strip()
    if not key:
        raise ConfigError(
            "{0} is not set — export the Firecrawl API key into it".format(config.api_key_env)
        )
    return key
