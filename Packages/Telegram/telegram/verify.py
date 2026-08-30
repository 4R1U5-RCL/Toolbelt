"""Proving a message was delivered, not merely accepted.

The fan-out webhook responds immediately, before the Telegram node runs. So a
2xx means *the workflow took the call* — it is not evidence that anything
reached a human. Those are different claims, and conflating them is how a rail
comes to be believed while it is quietly failing (TG-02).

The only honest proof available from outside is the workflow's own execution
record: find the execution this send produced, and check that the delivery node
actually ran and did not error. That is what this module does.

It needs `N8N_BASE_URL` + `N8N_API_KEY`. Without them, verification is
**unavailable, and says so** — it never degrades into assuming success, because
an assumed pass is worse than an admitted gap.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from .clock import Clock
from .http import HttpClient, HttpError
from .log import get_logger

DEFAULT_BASE_ENV = "N8N_BASE_URL"
DEFAULT_KEY_ENV = "N8N_API_KEY"
#: The node that actually talks to Telegram in `[TEMPLATE] Notification Fan-out`.
DEFAULT_DELIVERY_NODE = "Deliver"


class Verdict:
    """What the execution record supports — and nothing beyond it."""

    DELIVERED = "delivered"
    FAILED = "failed"
    NOT_FOUND = "not_found"
    UNAVAILABLE = "unavailable"

    def __init__(self, status: str, note: str, execution_id: Optional[str] = None,
                 node: Optional[str] = None):
        self.status = status
        self.note = note
        self.execution_id = execution_id
        self.node = node

    @property
    def ok(self) -> bool:
        return self.status == self.DELIVERED

    def as_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "note": self.note,
                "execution_id": self.execution_id, "node": self.node}

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "Verdict({0!r}, {1!r})".format(self.status, self.note)


class DeliveryVerifier:
    """Reads n8n's execution history to confirm a delivery actually happened."""

    def __init__(self, resolver, client: Optional[HttpClient] = None,
                 clock: Optional[Clock] = None, base_env: str = DEFAULT_BASE_ENV,
                 key_env: str = DEFAULT_KEY_ENV,
                 delivery_node: str = DEFAULT_DELIVERY_NODE):
        self.resolver = resolver
        self.client = client or HttpClient()
        self.clock = clock or Clock()
        self.base_env = base_env
        self.key_env = key_env
        self.delivery_node = delivery_node

    def available(self) -> bool:
        return self.resolver.present(self.base_env) and self.resolver.present(self.key_env)

    def confirm(self, request_id: Optional[str] = None, needle: Optional[str] = None,
                limit: int = 20, wait_seconds: float = 0.0,
                interrupt: Optional[threading.Event] = None) -> Verdict:
        """Look for an execution carrying `request_id` (or containing `needle`).

        `wait_seconds` polls, because the execution record is written when the
        workflow finishes and a send returns before that. Without a wait, an
        immediate check races the very thing it is checking and reports
        `not_found` for a message that arrives a second later.
        """
        if not self.available():
            return Verdict(Verdict.UNAVAILABLE,
                           "{0}/{1} not configured — delivery cannot be verified from here"
                           .format(self.base_env, self.key_env))
        if not request_id and not needle:
            return Verdict(Verdict.UNAVAILABLE,
                           "nothing to match on: pass a request_id or a needle")

        deadline = self.clock.monotonic() + max(0.0, wait_seconds)
        attempt = 0
        while True:
            attempt += 1
            try:
                verdict = self._scan(request_id, needle, limit)
            except HttpError as exc:
                return Verdict(Verdict.UNAVAILABLE, "n8n API unreachable: {0}".format(exc))
            if verdict.status != Verdict.NOT_FOUND:
                return verdict
            if self.clock.monotonic() >= deadline:
                return verdict
            get_logger().debug("execution not recorded yet; re-checking (attempt %d)", attempt)
            if self.clock.sleep(2.0, interrupt):
                return Verdict(Verdict.NOT_FOUND, "interrupted while waiting")

    # -- internals -------------------------------------------------------------

    def _scan(self, request_id: Optional[str], needle: Optional[str], limit: int) -> Verdict:
        base = str(self.resolver.get(self.base_env)).rstrip("/")
        headers = {"X-N8N-API-KEY": str(self.resolver.get(self.key_env)),
                   "Accept": "application/json"}
        listing = self.client.get_json(
            "{0}/api/v1/executions".format(base), headers=headers,
            params={"limit": str(max(1, min(int(limit), 100)))})
        rows = listing.get("data") if isinstance(listing, dict) else None

        for row in rows or []:
            execution_id = str(row.get("id"))
            detail = self.client.get_json(
                "{0}/api/v1/executions/{1}".format(base, execution_id),
                headers=headers, params={"includeData": "true"})
            blob = _stringify(detail)
            if request_id and request_id not in blob:
                continue
            if needle and needle not in blob:
                continue
            return self._judge(detail, execution_id)

        return Verdict(Verdict.NOT_FOUND,
                       "no execution in the last {0} carried that message yet".format(limit))

    def _judge(self, detail: Dict[str, Any], execution_id: str) -> Verdict:
        """Did the delivery node run, and did it run clean?"""
        run_data = (((detail.get("data") or {}).get("resultData") or {}).get("runData") or {})
        runs: List[Dict[str, Any]] = run_data.get(self.delivery_node) or []
        if not runs:
            reached = ", ".join(sorted(run_data)) or "(none)"
            return Verdict(Verdict.FAILED,
                           "execution {0} never reached {1!r} — nodes that ran: {2}".format(
                               execution_id, self.delivery_node, reached),
                           execution_id, self.delivery_node)
        for run in runs:
            if run.get("error"):
                return Verdict(Verdict.FAILED,
                               "{0!r} errored in execution {1}: {2}".format(
                                   self.delivery_node, execution_id,
                                   str(run.get("error"))[:200]),
                               execution_id, self.delivery_node)
        return Verdict(Verdict.DELIVERED,
                       "{0!r} ran clean in execution {1}".format(
                           self.delivery_node, execution_id),
                       execution_id, self.delivery_node)


def _stringify(value: Any) -> str:
    """Flatten an execution record to text so a correlation id can be found in it.

    Deliberately crude. The id could be in the webhook body, in a Code node's
    output, or in the response — searching the whole record is more robust than
    guessing which, and this runs once per verification, not per tick.
    """
    import json
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return str(value)
