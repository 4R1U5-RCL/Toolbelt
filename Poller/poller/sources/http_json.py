"""The declarative HTTP+JSON source — the one most pollers will use.

Everything about *which* API is watched lives in config: the URL, how to
authenticate, where in the response the list of things lives, which field is the
identity, and how that API's status words map onto `pending / settled / failed`.

That mapping is the whole trick. Once an API's vocabulary is declared, the
engine's dedup, retry, staleness and delivery logic apply to it unchanged.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional

from ..errors import ConfigError, FatalSourceError, TransientSourceError
from ..http import HttpFatal, HttpTransient
from ..log import get_logger
from ..model import Item, ItemState
from ..render import render
from .base import Source

#: Checked in this order so an ambiguous status resolves toward the louder
#: outcome: reporting a failure that was really a success is recoverable,
#: reporting a success that was really a failure is not.
_STATE_ORDER = (ItemState.FAILED, ItemState.SETTLED, ItemState.PENDING)


def dig(obj: Any, path: Optional[str], default: Any = None) -> Any:
    """Walk a dotted path through nested dicts and lists.

    `""`, `"."` and None all mean "the root object", which is what an API that
    returns a bare top-level array needs.
    """
    if path in (None, "", "."):
        return obj
    current = obj
    for part in str(path).split("."):
        if isinstance(current, dict):
            if part not in current:
                return default
            current = current[part]
        elif isinstance(current, (list, tuple)):
            try:
                index = int(part)
                current = current[index]
            except (ValueError, IndexError):
                return default
        else:
            return default
    return current


class HttpJsonSource(Source):
    """Fetch one JSON endpoint and normalize a list inside it into Items."""

    name = "http_json"

    def __init__(self, config, resolver, client=None):
        super().__init__(config, resolver, client)
        self.url = self.config.get("url")
        if not self.url:
            raise ConfigError("source.url is required for an http_json source")
        self.method = str(self.config.get("method", "GET")).upper()
        self.items_path = self.config.get("items_path", "")
        self.key_field = self.config.get("key_field", "id")
        self.title_template = self.config.get("title_template", "{key}")
        self.field_map: Dict[str, str] = dict(self.config.get("fields") or {})
        self.filters = self.config.get("filter") or []
        if isinstance(self.filters, dict):
            self.filters = [self.filters]

        state_cfg = self.config.get("state") or {}
        self.state_field = state_cfg.get("field", "status")
        self.state_map = self._normalize_state_map(state_cfg.get("map") or {})
        self.state_match = state_cfg.get("match", "icontains")
        self.state_default = state_cfg.get("default", ItemState.UNKNOWN)
        self.settled_requires = list(state_cfg.get("settled_requires") or [])

        self.params = dict(self.config.get("params") or {})
        self._headers = self.resolver.resolve_mapping(self.config.get("headers"))
        self._apply_auth()

    # -- Source contract -------------------------------------------------------

    def fetch(self) -> List[Item]:
        payload = self._get()
        rows = self.extract_rows(payload)
        items = [self.to_item(row) for row in rows if isinstance(row, dict) and self._keep(row)]
        return [item for item in items if item is not None]

    def extract_rows(self, payload: Any) -> List[Dict[str, Any]]:
        """Pull the list of rows out of a decoded response body.

        Overridable: some APIs return a bare array on one endpoint and a wrapped
        object on another, and a preset should absorb that rather than making
        every operator discover it (see KaggleSubmissionsSource).
        """
        rows = dig(payload, self.items_path, default=None)
        if rows is None:
            raise FatalSourceError(
                "items_path {0!r} matched nothing in the response; got a {1} with keys {2}".format(
                    self.items_path, type(payload).__name__,
                    sorted(payload)[:10] if isinstance(payload, dict) else "n/a")
            )
        if not isinstance(rows, list):
            raise FatalSourceError(
                "items_path {0!r} resolved to a {1}, expected a list".format(
                    self.items_path, type(rows).__name__)
            )
        return rows

    def describe(self) -> str:
        return "{0} <- {1}".format(self.name, self.url.split("?")[0])

    # -- normalization ---------------------------------------------------------

    def to_item(self, row: Dict[str, Any]) -> Optional[Item]:
        """Turn one JSON row into an Item, or None if it has no usable identity."""
        key = dig(row, self.key_field)
        if key in (None, ""):
            get_logger().warning(
                "row without key_field %r skipped; a poller cannot dedup what it cannot name",
                self.key_field,
            )
            return None
        fields = {alias: dig(row, path) for alias, path in self.field_map.items()}
        fields.setdefault("raw_state", dig(row, self.state_field))
        state = self.classify(row, fields)
        title = render(self.title_template, dict(fields, key=str(key), state=state))
        return Item(key=str(key), state=state, title=title, fields=fields)

    def classify(self, row: Dict[str, Any], fields: Dict[str, Any]) -> str:
        """Map the API's status word onto one of our four states."""
        raw = dig(row, self.state_field)
        text = "" if raw is None else str(raw)
        state = self.state_default
        for candidate in _STATE_ORDER:
            patterns = self.state_map.get(candidate) or ()
            if any(self._matches(text, pattern) for pattern in patterns):
                state = candidate
                break

        # "Complete, but the score field is still null" is the single most
        # expensive false positive available: it reports a settle with no result.
        if state == ItemState.SETTLED and self.settled_requires:
            missing = [name for name in self.settled_requires if _blank(fields.get(name), row, name)]
            if missing:
                get_logger().debug(
                    "row %s reads settled but %s still empty; holding as pending",
                    dig(row, self.key_field), ", ".join(missing),
                )
                return ItemState.PENDING
        return state

    # -- internals -------------------------------------------------------------

    def _get(self):
        try:
            response = self.client.request(
                self.method, self.url, headers=self._headers, params=self.params or None
            )
            return response.json()
        except HttpFatal as exc:
            raise FatalSourceError(str(exc))
        except HttpTransient as exc:
            raise TransientSourceError(str(exc))

    def _keep(self, row: Dict[str, Any]) -> bool:
        """Apply optional row filters (all must pass)."""
        for rule in self.filters:
            value = dig(row, rule.get("field"))
            text = "" if value is None else str(value)
            if "equals" in rule and text != str(rule["equals"]):
                return False
            if "contains" in rule and str(rule["contains"]).lower() not in text.lower():
                return False
            if "not_contains" in rule and str(rule["not_contains"]).lower() in text.lower():
                return False
        return True

    def _matches(self, text: str, pattern: str) -> bool:
        left, right = text.strip().lower(), str(pattern).strip().lower()
        if self.state_match == "exact":
            return left == right
        if self.state_match == "prefix":
            return left.startswith(right)
        return right in left  # icontains (default): survives "SubmissionStatus.COMPLETE"

    @staticmethod
    def _normalize_state_map(raw: Dict[str, Any]) -> Dict[str, List[str]]:
        normalized = {}
        for state, patterns in raw.items():
            if isinstance(patterns, str):
                patterns = [patterns]
            normalized[state] = [str(p) for p in patterns or []]
        return normalized

    def _apply_auth(self) -> None:
        """Fold the declared auth scheme into headers or query params."""
        auth = self.config.get("auth") or {}
        scheme = str(auth.get("scheme", "none")).lower()
        if scheme in ("none", ""):
            return
        if scheme == "bearer":
            token = self.resolver.resolve(auth.get("token"))
            self._headers.setdefault("Authorization", "Bearer {0}".format(token))
        elif scheme == "header":
            token = self.resolver.resolve(auth.get("token"))
            self._headers.setdefault(auth.get("header", "X-API-Key"), str(token))
        elif scheme == "basic":
            token = self.resolver.resolve(auth.get("token"), required=False)
            if not token:
                user = self.resolver.resolve(auth.get("username"))
                secret = self.resolver.resolve(auth.get("password"))
                token = "{0}:{1}".format(user, secret)
            encoded = base64.b64encode(str(token).encode("utf-8")).decode("ascii")
            self._headers.setdefault("Authorization", "Basic {0}".format(encoded))
        elif scheme == "query":
            self.params[auth.get("param", "key")] = str(self.resolver.resolve(auth.get("token")))
        else:
            raise ConfigError(
                "unknown auth scheme {0!r}; use bearer, header, basic, query or none".format(scheme)
            )


def _blank(value: Any, row: Dict[str, Any], name: str) -> bool:
    """True when a required-for-settled field carries no usable value.

    Checks the mapped alias first, then the raw row, so `settled_requires` can
    name either. A score of `0` is a real result and must not read as blank —
    only None, the empty string, and empty containers do.
    """
    if _empty(value):
        value = dig(row, name)
    return _empty(value)


def _empty(value: Any) -> bool:
    if value is None or value == "":
        return True
    return isinstance(value, (dict, list, tuple, set)) and len(value) == 0
