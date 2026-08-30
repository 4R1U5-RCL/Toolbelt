"""Sinks: the report rails an event fans out to.

Each sink is independent and independently ledgered, so a Telegram outage never
loses the Slack post and never re-sends it either. A sink raises `SinkError` if
a later retry could work, and `FatalSinkError` if only a human can fix it —
retrying a revoked token for hours is noise, not resilience.

Built in: `file`, `stdout`, `slack`, `notify_webhook` (the signed n8n → Telegram
seam), `webhook` (any JSON POST), and `command` (shell out to an existing tool).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import re
import subprocess
from typing import Any, Dict, List, Optional

from .clock import Clock
from .errors import ConfigError, FatalSinkError, SinkError
from .http import HttpClient, HttpFatal, HttpTransient
from .log import get_logger
from .model import Event
from .render import render

DEFAULT_TEMPLATE = "{title}\n{body}"


class Sink:
    """Base sink: naming, filtering, templating, dry-run."""

    type_name = "sink"

    def __init__(self, config: Dict[str, Any], resolver, client: Optional[HttpClient] = None,
                 dry_run: bool = False, clock: Optional[Clock] = None):
        self.config = config or {}
        self.resolver = resolver
        self.client = client or HttpClient()
        self.dry_run = dry_run or bool(self.config.get("dry_run"))
        self.clock = clock or Clock()
        self.name = str(self.config.get("name") or self.type_name)
        self.template = self.config.get("template", DEFAULT_TEMPLATE)
        reasons = self.config.get("reasons")
        self.reasons = set(reasons) if reasons else None

    # -- contract --------------------------------------------------------------

    def accepts(self, event: Event) -> bool:
        """Whether this sink wants this event at all (per-sink `reasons` filter)."""
        return self.reasons is None or event.reason in self.reasons

    def deliver(self, event: Event) -> None:
        """Send one event. Raise SinkError/FatalSinkError on failure."""
        message = self.render_message(event)
        if self.dry_run:
            get_logger().info("[dry-run] %s would send:\n%s", self.name, message)
            return
        self.send(message, event)

    def send(self, message: str, event: Event) -> None:
        raise NotImplementedError

    def preflight(self) -> None:
        """Check configuration without sending anything."""

    def render_message(self, event: Event) -> str:
        return render(self.template, event.context())

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<{0} name={1!r} dry_run={2}>".format(type(self).__name__, self.name, self.dry_run)


class StdoutSink(Sink):
    """Print the report. The rail that cannot fail, useful as a floor under the others."""

    type_name = "stdout"

    def send(self, message: str, event: Event) -> None:
        print(message, flush=True)


class FileSink(Sink):
    """Append the report to a file — the local audit trail.

    Ordered first in every example config on purpose: it is the only rail that
    works with no network, so a report exists on disk even when both remote
    rails are down. The path is templated per event rather than fixed, so two
    concurrent pollers cannot overwrite each other's report (KI-17).
    """

    type_name = "file"

    def __init__(self, config, resolver, client=None, dry_run=False, clock=None):
        super().__init__(config, resolver, client, dry_run, clock)
        self.path_template = self.config.get("path")
        if not self.path_template:
            raise ConfigError("sink `file` requires a `path`")
        self.mode = self.config.get("mode", "append")

    def send(self, message: str, event: Event) -> None:
        # Item fields are interpolated into a filesystem path, and a key is
        # whatever the watched API says it is. Sanitize the substituted values
        # so a key like "../../etc/x" cannot steer the write out of the
        # configured directory.
        path = os.path.expanduser(render(self.path_template, _path_safe(event.context())))
        directory = os.path.dirname(os.path.abspath(path))
        try:
            os.makedirs(directory, exist_ok=True)
            with open(path, "a" if self.mode == "append" else "w", encoding="utf-8") as handle:
                handle.write("## {0} — {1}\n\n{2}\n\n".format(self.clock.iso(), event.reason, message))
        except OSError as exc:
            raise SinkError("cannot write {0}: {1}".format(path, exc))


class SlackSink(Sink):
    """Post to a Slack channel via `chat.postMessage`."""

    type_name = "slack"
    URL = "https://slack.com/api/chat.postMessage"
    # Slack answers HTTP 200 with `ok:false` and one of these; none improve with time.
    FATAL_ERRORS = frozenset({
        "invalid_auth", "not_authed", "token_revoked", "account_inactive",
        "channel_not_found", "not_in_channel", "is_archived", "missing_scope",
    })

    def __init__(self, config, resolver, client=None, dry_run=False, clock=None):
        super().__init__(config, resolver, client, dry_run, clock)
        self._token_name = self.config.get("token_env", "SLACK_BOT_TOKEN")
        self._channel_name = self.config.get("channel_env", "SLACK_CHANNEL_ID")
        self.channel_literal = self.config.get("channel")

    def preflight(self) -> None:
        self.resolver.get(self._token_name)
        if not self.channel_literal:
            self.resolver.get(self._channel_name)

    def send(self, message: str, event: Event) -> None:
        token = self.resolver.get(self._token_name)
        channel = self.channel_literal or self.resolver.get(self._channel_name)
        payload = {"channel": channel, "text": message}
        try:
            response = self.client.post_json(
                self.URL, payload, headers={"Authorization": "Bearer {0}".format(token)}
            )
            body = response.json()
        except HttpFatal as exc:
            raise FatalSinkError("slack rejected the request: {0}".format(exc))
        except HttpTransient as exc:
            raise SinkError("slack unreachable: {0}".format(exc))
        if not body.get("ok"):
            error = str(body.get("error", "unknown"))
            if error in self.FATAL_ERRORS:
                raise FatalSinkError("slack error {0!r} — fix the app config".format(error))
            raise SinkError("slack error {0!r}".format(error))


class NotifyWebhookSink(Sink):
    """The studio's signed notify seam (n8n -> Telegram).

    Reimplements `packages/notify/src/client.mjs` in the standard library so a
    poller needs no Node runtime and no path into another repo (KI-10). The
    envelope is byte-compatible: same field order, same compact separators, and
    the HMAC covers `"<unix-ms>.<body>"` exactly as the workflow verifies it.
    """

    type_name = "notify_webhook"
    SCHEMA = "studio.notify.v1"
    KIND_BY_SEVERITY = {"error": "alert", "warn": "attention", "info": "complete"}

    def __init__(self, config, resolver, client=None, dry_run=False, clock=None):
        super().__init__(config, resolver, client, dry_run, clock)
        self._url_name = self.config.get("url_env", "NOTIFY_WEBHOOK_URL")
        self._token_name = self.config.get("token_env", "NOTIFY_TOKEN")
        self._secret_name = self.config.get("secret_env", "NOTIFY_SECRET")
        self.source_name = self.config.get("source", "poller")
        self.title_template = self.config.get("title_template", "{title}")
        self.body_template = self.config.get("body_template", "{body}")

    def preflight(self) -> None:
        self.resolver.get(self._url_name)
        self.resolver.get(self._token_name)

    def send(self, message: str, event: Event) -> None:
        url = self.resolver.get(self._url_name)
        token = self.resolver.get(self._token_name)
        secret = self.resolver.get(self._secret_name, required=False) or token
        context = event.context()
        body_bytes, headers = self.build_request(
            title=render(self.title_template, context),
            summary=render(self.body_template, context),
            severity=event.severity,
            meta={"reason": event.reason, "key": context.get("key", "")},
            token=token,
            secret=secret,
            timestamp_ms=int(self.clock.now().timestamp() * 1000),
        )
        try:
            self.client.request("POST", url, headers=headers, body=body_bytes)
        except HttpFatal as exc:
            raise FatalSinkError("notify webhook rejected: {0}".format(exc))
        except HttpTransient as exc:
            raise SinkError("notify webhook unreachable: {0}".format(exc))

    def build_request(self, title: str, summary: str, severity: str, meta: Dict[str, Any],
                      token: str, secret: str, timestamp_ms: int):
        """Pure envelope builder — the clock is injected so tests can assert the signature."""
        payload = {
            "schema": self.SCHEMA,
            "source": self.source_name,
            "kind": self.KIND_BY_SEVERITY.get(severity, "complete"),
            "message": title,
            "summary": summary,
            "event": None,
            "meta": dict(meta, severity=severity),
            "sentAt": _iso_millis(timestamp_ms),
        }
        # Compact separators + non-escaped unicode reproduce JSON.stringify's
        # bytes; the signature is over those exact bytes, so this must not change.
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        signature = hmac.new(
            secret.encode("utf-8"),
            "{0}.{1}".format(timestamp_ms, body).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-Notify-Token": token,
            "x-notify-timestamp": str(timestamp_ms),
            "x-notify-signature": signature,
        }
        return body.encode("utf-8"), headers


class WebhookSink(Sink):
    """POST the report as JSON to any URL — Discord, Teams, an internal collector."""

    type_name = "webhook"

    def __init__(self, config, resolver, client=None, dry_run=False, clock=None):
        super().__init__(config, resolver, client, dry_run, clock)
        self.url = self.resolver.resolve(self.config.get("url"))
        if not self.url:
            raise ConfigError("sink `webhook` requires a `url` (literal or @env:NAME)")
        self.field = self.config.get("field", "text")
        self.headers = self.resolver.resolve_mapping(self.config.get("headers"))

    def send(self, message: str, event: Event) -> None:
        payload = dict(self.config.get("extra") or {})
        payload[self.field] = message
        try:
            self.client.post_json(self.url, payload, headers=self.headers)
        except HttpFatal as exc:
            raise FatalSinkError("webhook rejected: {0}".format(exc))
        except HttpTransient as exc:
            raise SinkError("webhook unreachable: {0}".format(exc))


class CommandSink(Sink):
    """Pipe the report into an existing CLI (e.g. `studio-slack post --stdin`).

    The message goes in on stdin, never in argv: arguments are visible to every
    process on the box, and a report can quote a secret-adjacent field.
    """

    type_name = "command"

    def __init__(self, config, resolver, client=None, dry_run=False, clock=None):
        super().__init__(config, resolver, client, dry_run, clock)
        self.argv: List[str] = list(self.config.get("argv") or [])
        if not self.argv:
            raise ConfigError("sink `command` requires a non-empty `argv` array")
        self.timeout = float(self.config.get("timeout_seconds", 60))

    def send(self, message: str, event: Event) -> None:
        argv = [render(part, event.context()) for part in self.argv]
        try:
            result = subprocess.run(
                argv, input=message.encode("utf-8"),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=self.timeout, check=False,
            )
        except FileNotFoundError as exc:
            raise FatalSinkError("command not found: {0}".format(exc))
        except subprocess.TimeoutExpired:
            raise SinkError("command timed out after {0}s".format(self.timeout))
        if result.returncode != 0:
            output = result.stdout.decode("utf-8", "replace").strip()[:400]
            raise SinkError("command exited {0}: {1}".format(result.returncode, output))


BUILTIN_SINKS = {
    cls.type_name: cls
    for cls in (StdoutSink, FileSink, SlackSink, NotifyWebhookSink, WebhookSink, CommandSink)
}


def build_sinks(configs, resolver, client=None, dry_run: bool = False,
                clock: Optional[Clock] = None) -> List[Sink]:
    """Instantiate the sink list, guaranteeing every sink has a unique name.

    Names are the delivery-ledger keys, so duplicates would make two rails share
    one "delivered" flag and silently drop half the reports.
    """
    if not configs:
        raise ConfigError("at least one sink is required — a poller that reports nowhere is a no-op")
    sinks: List[Sink] = []
    used = set()
    for index, config in enumerate(configs):
        if not isinstance(config, dict):
            raise ConfigError("sinks[{0}] must be an object".format(index))
        kind = config.get("type")
        if kind not in BUILTIN_SINKS:
            raise ConfigError("unknown sink type {0!r}; known: {1}".format(
                kind, ", ".join(sorted(BUILTIN_SINKS))))
        sink = BUILTIN_SINKS[kind](config, resolver, client=client, dry_run=dry_run, clock=clock)
        base = sink.name
        suffix = 2
        while sink.name in used:
            sink.name = "{0}-{1}".format(base, suffix)
            suffix += 1
        used.add(sink.name)
        sinks.append(sink)
    return sinks


_PATH_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _path_safe(context: Dict[str, Any]) -> Dict[str, str]:
    """Reduce every context value to characters that are safe in a filename."""
    safe = {}
    for key, value in context.items():
        text = _PATH_UNSAFE.sub("-", "" if value is None else str(value)).strip("-.")
        safe[key] = text[:80] or "unnamed"
    return safe


def _iso_millis(timestamp_ms: int) -> str:
    """`2026-08-30T12:34:56.789Z` — matching JavaScript's Date#toISOString."""
    moment = dt.datetime.fromtimestamp(timestamp_ms / 1000.0, dt.timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + "{0:03d}Z".format(timestamp_ms % 1000)
