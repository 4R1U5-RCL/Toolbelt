"""Kaggle competition submissions — a preset over `http_json`.

Every quirk below was paid for once already; encoding them here means the next
Kaggle poller starts from a working configuration instead of rediscovering them.

* Auth is **Bearer `KAGGLE_API_TOKEN`**. The older Basic `username:key` token is
  dead and answers 401 (KI-05).
* The endpoint answers with a bare JSON array, but neighbouring endpoints wrap
  their rows in an object — `extract_rows` accepts either.
* `status` has been observed as both `complete` and `SubmissionStatus.COMPLETE`,
  so matching is case-insensitive substring.
* A row can read `complete` while `publicScore` is still `null` for a few
  seconds. Reporting then would announce a settle with no score, so
  `publicScore` is required before a row counts as settled (KI-04).
* Identity is `ref` — the immutable submission id. Never the description: that
  is human-typed, changes between submissions, and pinning a watch to it is
  exactly how a real settle got missed (KI-01).
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..errors import ConfigError
from ..model import ItemState
from .http_json import HttpJsonSource

API_ROOT = "https://www.kaggle.com/api/v1"

DEFAULT_STATE_MAP = {
    ItemState.FAILED: ["error", "failed", "cancel"],
    ItemState.SETTLED: ["complete", "success"],
    ItemState.PENDING: ["pending", "running", "queued", "submitting"],
}

DEFAULT_STATE = {
    "field": "status",
    "map": DEFAULT_STATE_MAP,
    "match": "icontains",
    "default": ItemState.PENDING,     # unknown Kaggle status = keep watching, never "done"
    "settled_requires": ["publicScore"],
}

DEFAULT_FIELDS = {
    "score": "publicScore",
    "private_score": "privateScore",
    "date": "date",
    "description": "description",
    "error": "errorDescription",
    "filename": "fileName",
    "status": "status",
}


class KaggleSubmissionsSource(HttpJsonSource):
    """Watch every submission on one competition, not one named notebook."""

    name = "kaggle_submissions"

    def __init__(self, config, resolver, client=None):
        competition = config.get("competition")
        if not competition and not config.get("url"):
            raise ConfigError(
                "source.competition (the competition slug) is required for kaggle_submissions"
            )
        # Operator config wins throughout; the preset only fills the blanks.
        merged: Dict[str, Any] = dict(config)
        merged["url"] = config.get("url") or "{0}/competitions/submissions/list/{1}".format(
            API_ROOT, competition)
        merged.setdefault("items_path", "")
        merged.setdefault("key_field", "ref")
        merged.setdefault("title_template", "{description}")
        merged.setdefault("auth", {"scheme": "bearer", "token": "@env:KAGGLE_API_TOKEN"})
        merged["fields"] = dict(DEFAULT_FIELDS, **(config.get("fields") or {}))
        merged["state"] = dict(DEFAULT_STATE, **(config.get("state") or {}))

        self.competition = competition
        super().__init__(merged, resolver, client)

    def extract_rows(self, payload: Any) -> List[Dict[str, Any]]:
        """Accept both the bare array and the `{"submissions": [...]}` wrapper."""
        if isinstance(payload, dict):
            for wrapper in ("submissions", "items", "results"):
                if isinstance(payload.get(wrapper), list):
                    return payload[wrapper]
        return super().extract_rows(payload)

    def describe(self) -> str:
        return "kaggle submissions <- {0}".format(self.competition or self.url.split("?")[0])
