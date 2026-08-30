"""The seam: one signed envelope, one place it is built.

Everything this package does eventually becomes a POST to the studio's hosted
n8n fan-out workflow, which delivers to Telegram. That envelope already has a
canonical definition in `/studio/packages/notify/src/client.mjs`, and a second
one that disagreed with it would be worse than none — so this module is a
deliberate port, and `tests/test_conformance.py` asserts the bytes match.

**Why a Python port at all**, when a Node implementation exists: it must run
where nothing can be installed and where reaching into another repo's absolute
path is not acceptable. `studio-ops/bin/studio-cpu-watchdog` already
hand-rolled its own Python copy of this envelope for exactly that reason. This
is that copy, made shared and tested instead of duplicated again.

**Why everything rides the webhook** rather than calling Telegram directly:
there is no bot token in this container (TG-08). The token lives only in an n8n
credential, which is the right place for it — but it means the Bot API is
unreachable from here, and the seam is not one option among several.

## What the live receiver actually checks

Read off the deployed `[TEMPLATE] Notification Fan-out` workflow, not off the
docs, because they disagree:

* HMAC-SHA256 over `` `${unix_ms}.${body}` `` keyed on `NOTIFY_FANOUT_SECRET`,
  with a five-minute skew window (TG-10). This is the **only** real gate.
* It accepts **either** header family — `x-n8n-signature`/`x-n8n-timestamp` or
  `x-notify-signature`/`x-notify-timestamp`. The studio has both conventions in
  the wild, so this module sends both (TG-05).
* `X-Notify-Token` is sent, and the notify docs describe it as a second gate,
  but the deployed webhook node has **no Header Auth configured** — nothing
  checks it (TG-06). It is sent for compatibility, and must not be mistaken for
  security.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import hmac
import json
import uuid
from typing import Any, Dict, Optional

from .clock import Clock
from .errors import ConfigError, FatalSendError, SendError
from .http import HttpClient, HttpFatal, HttpTransient
from .log import get_logger

#: The envelope version. Shared with client.mjs; changing it breaks every reader.
NOTIFY_SCHEMA = "studio.notify.v1"

TOKEN_HEADER = "X-Notify-Token"
#: Both families are sent. The receiver reads either; different studio callers
#: settled on different names and neither is going away (TG-05).
SIG_HEADERS = ("x-notify-signature", "x-n8n-signature")
TS_HEADERS = ("x-notify-timestamp", "x-n8n-timestamp")

#: The receiver rejects anything signed more than this long ago (TG-10).
MAX_SKEW_MS = 5 * 60 * 1000

DEFAULT_URL_ENV = "NOTIFY_WEBHOOK_URL"
DEFAULT_TOKEN_ENV = "NOTIFY_TOKEN"
DEFAULT_SECRET_ENV = "NOTIFY_SECRET"


class SendResult:
    """The outcome of one send. Never an exception — see `errors` for why.

    `accepted` and `delivered` are deliberately different fields. A 2xx means
    the webhook took the call; it does **not** mean Telegram showed anyone
    anything. Only `telegram verify` can promote one to the other, by looking at
    whether the workflow's delivery node actually ran (TG-02).
    """

    def __init__(self, accepted: bool, status: int, note: str,
                 request_id: Optional[str] = None, body: str = "",
                 response_signature_ok: Optional[bool] = None):
        self.accepted = accepted
        self.status = status
        self.note = note
        self.request_id = request_id
        self.body = body
        self.response_signature_ok = response_signature_ok
        #: Never set by `send`. Only `verify.confirm_delivery` may set it True.
        self.delivered = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "accepted": self.accepted,
            "delivered": self.delivered,
            "status": self.status,
            "request_id": self.request_id,
            "response_signature_ok": self.response_signature_ok,
            "note": self.note,
        }

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "SendResult({0}, status={1}, {2!r})".format(self.accepted, self.status, self.note)


def sign(body: str, secret: str) -> str:
    """Hex HMAC-SHA256 — the one signing primitive, matching client.mjs `sign`."""
    return hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).hexdigest()


def iso_ms(timestamp_ms: int) -> str:
    """`sentAt` exactly as JavaScript's `Date.toISOString()` writes it.

    Always three fractional digits and a literal `Z`. Python's `isoformat()`
    gives six digits and `+00:00`, which is a different string — and the string
    is inside the signed bytes, so "close enough" is a signature mismatch.
    """
    whole, millis = divmod(int(timestamp_ms), 1000)
    stamp = _dt.datetime.fromtimestamp(whole, tz=_dt.timezone.utc)
    return "{0}.{1:03d}Z".format(stamp.strftime("%Y-%m-%dT%H:%M:%S"), millis)


def build_payload(source: str, message: str, kind: Optional[str] = None,
                  summary: Optional[str] = None, event: Optional[Any] = None,
                  meta: Optional[Dict[str, Any]] = None, timestamp_ms: int = 0,
                  chat_id: Optional[str] = None,
                  request_id: Optional[str] = None) -> Dict[str, Any]:
    """The envelope, in the field order client.mjs writes it.

    Order matters: `json.dumps` preserves insertion order, `JSON.stringify`
    preserves it too, and the signature covers the serialised bytes. Reordering
    these keys would produce a valid-looking payload that fails verification.

    `chat_id` and `request_id` are appended **only when given**, so a default
    send is byte-identical to what client.mjs produces for the same inputs.
    """
    payload: Dict[str, Any] = {
        "schema": NOTIFY_SCHEMA,
        "source": source,
        "kind": kind,
        "message": message or "",
        "summary": summary,
        "event": event,
        "meta": meta if meta is not None else {},
        "sentAt": iso_ms(timestamp_ms),
    }
    if chat_id:
        payload["chat_id"] = str(chat_id)
    if request_id:
        payload["request_id"] = request_id
    return payload


def serialise(payload: Dict[str, Any]) -> str:
    """Serialise to the exact bytes `JSON.stringify` would produce.

    Compact separators (JS emits no padding) and `ensure_ascii=False` (JS does
    not escape non-ASCII). An emoji escaped to `\\ud83d\\udfe2` is a different
    body and therefore a different signature.
    """
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def build_request(payload: Dict[str, Any], token: str, secret: Optional[str],
                  timestamp_ms: int) -> Dict[str, Any]:
    """Build the exact bytes and headers for one call. Pure — no clock, no I/O.

    Kept pure for the same reason client.mjs keeps `buildRequest` pure: a test
    can then assert a signature deterministically, offline, with no network and
    no mocking.
    """
    body = serialise(payload)
    key = secret or token
    signature = sign("{0}.{1}".format(timestamp_ms, body), key)
    headers = {"Content-Type": "application/json", TOKEN_HEADER: token}
    for name in TS_HEADERS:
        headers[name] = str(timestamp_ms)
    for name in SIG_HEADERS:
        headers[name] = signature
    return {"body": body, "headers": headers, "signature": signature}


class Seam:
    """The configured send path. One per process; holds no per-message state."""

    def __init__(self, resolver, client: Optional[HttpClient] = None,
                 clock: Optional[Clock] = None, source: str = "telegram",
                 url_env: str = DEFAULT_URL_ENV, token_env: str = DEFAULT_TOKEN_ENV,
                 secret_env: str = DEFAULT_SECRET_ENV, dry_run: bool = False):
        self.resolver = resolver
        self.client = client or HttpClient()
        self.clock = clock or Clock()
        self.source = source
        self.url_env = url_env
        self.token_env = token_env
        self.secret_env = secret_env
        self.dry_run = dry_run

    # -- configuration ---------------------------------------------------------

    def preflight(self) -> Dict[str, Any]:
        """Prove the credentials resolve before anything tries to send.

        Returns names and presence only — never a value. Missing configuration
        is worth finding here, not at the moment something is trying to report a
        failure.
        """
        missing = [n for n in (self.url_env, self.token_env) if not self.resolver.present(n)]
        if missing:
            raise ConfigError(
                "notify seam is not configured: {0} absent from {1} and the process "
                "environment".format(", ".join(missing), self.resolver.env_file or "<no env file>"))
        return {
            "url_env": self.url_env,
            "token_env": self.token_env,
            "secret_env": self.secret_env,
            "secret_present": self.resolver.present(self.secret_env),
            "secret_source": (self.secret_env if self.resolver.present(self.secret_env)
                              else self.token_env + " (fallback, matching client.mjs)"),
        }

    # -- sending ---------------------------------------------------------------

    def send(self, message: str, kind: Optional[str] = None, summary: Optional[str] = None,
             event: Optional[Any] = None, meta: Optional[Dict[str, Any]] = None,
             chat_id: Optional[str] = None, correlate: bool = True,
             timestamp_ms: Optional[int] = None) -> SendResult:
        """Send one message. **Never raises** — the outcome is the return value.

        A notification is not the work. A caller reporting that a deploy failed
        must not itself fail because the notifier is down, so every error path
        below resolves to a `SendResult` carrying what went wrong. Failures are
        loud in the log; they are never silent successes.
        """
        request_id = uuid.uuid4().hex[:16] if correlate else None
        try:
            url = self.resolver.get(self.url_env)
            token = self.resolver.get(self.token_env)
            secret = self.resolver.get(self.secret_env, required=False) or token
        except ConfigError as exc:
            get_logger().error("send skipped: %s", exc)
            return SendResult(False, 0, "NOT WIRED — {0}".format(exc), request_id)

        stamp = timestamp_ms if timestamp_ms is not None else int(self.clock.now().timestamp() * 1000)
        payload = build_payload(
            source=self.source, message=message, kind=kind, summary=summary,
            event=event, meta=meta, timestamp_ms=stamp, chat_id=chat_id,
            request_id=request_id,
        )
        prepared = build_request(payload, token=token, secret=secret, timestamp_ms=stamp)

        if self.dry_run:
            get_logger().info("dry run: would POST %d bytes to %s",
                              len(prepared["body"].encode("utf-8")), self.url_env)
            return SendResult(True, 0, "dry run — nothing sent", request_id,
                              body=prepared["body"])

        try:
            response = self.client.request(
                "POST", url, headers=prepared["headers"],
                body=prepared["body"].encode("utf-8"))
        except HttpFatal as exc:
            get_logger().error("notify webhook rejected the call: %s", exc)
            return SendResult(False, getattr(exc, "status", 0),
                              "rejected: {0}".format(exc), request_id)
        except HttpTransient as exc:
            get_logger().error("notify webhook unreachable: %s", exc)
            return SendResult(False, getattr(exc, "status", 0),
                              "unreachable: {0}".format(exc), request_id)

        raw = response.body.decode("utf-8", "replace")
        return SendResult(
            accepted=True, status=response.status,
            note="accepted by the n8n webhook — not yet proof of delivery (TG-02)",
            request_id=request_id, body=raw,
            response_signature_ok=verify_response(response, secret),
        )


def verify_response(response, secret: str) -> Optional[bool]:
    """Check the signature the fan-out puts on its own reply.

    The workflow signs `{"ok":true,"request_id":…}` with the shared secret and
    nothing in the studio has ever checked it. Verified here so a hijacked or
    misrouted endpoint cannot answer a confident 200.

    **Advisory, never fatal.** n8n serialises the response body itself, so a
    difference in its JSON spacing would break byte-equality without any
    security meaning. A mismatch is logged and reported; it does not turn an
    accepted send into a rejected one. Returns None when unsigned.
    """
    signature = ""
    for name in SIG_HEADERS:
        signature = response.headers.get(name) or signature
    if not signature:
        return None
    expected = sign(response.body.decode("utf-8", "replace"), secret)
    ok = hmac.compare_digest(expected, signature)
    if not ok:
        get_logger().warning(
            "response signature did not match — this is advisory (n8n re-serialises "
            "the reply), but a persistent mismatch is worth investigating")
    return ok


__all__ = [
    "NOTIFY_SCHEMA", "MAX_SKEW_MS", "SIG_HEADERS", "TS_HEADERS", "TOKEN_HEADER",
    "Seam", "SendResult", "SendError", "FatalSendError",
    "build_payload", "build_request", "serialise", "sign", "iso_ms", "verify_response",
]
