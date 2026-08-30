"""Command line: `telegram render | send | check | verify | templates | decode`.

`send` is the point of the package. The other five exist because the failures
were never in the sending — they were in not being able to see what would
arrive, or whether it did.

* `render` builds a message offline and prints exactly what Telegram would
  receive, including where it would be chunked and what the buttons encode to.
  Nothing leaves the machine. This is the command that prevents the formatting
  traps, because it makes them visible before a send rather than after.
* `check` proves the credentials resolve, without sending.
* `verify` asks n8n whether the delivery node actually ran (TG-02).
* `decode` turns a `callback_data` string back into its parts, for when a button
  press did something unexpected.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

from . import __version__
from .clock import Clock
from .envfile import EnvResolver
from .errors import ConfigError, TelegramError
from .inbound import decode_update
from .keyboard import decode as decode_callback
from .log import configure, get_logger
from .seam import Seam
from .template import GROUPS, Catalogue, catalogue_dir
from .text import TELEGRAM_LIMIT, tg_len
from .verify import DeliveryVerifier

EXIT_OK = 0
EXIT_ERROR = 1
#: A send that was accepted but could not be proven delivered. Distinct from a
#: failure on purpose: a caller scripting a gate needs to tell "it did not send"
#: from "it sent and I cannot prove what happened next" (TG-02).
EXIT_UNPROVEN = 2

DEFAULT_ENV_FILE = "/studio/.env"


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_ERROR

    configure(verbose=getattr(args, "verbose", False))
    if args.command == "version":
        print("telegram {0}".format(__version__))
        return EXIT_OK

    try:
        return _COMMANDS[args.command](args)
    except TelegramError as exc:
        get_logger().error("%s", exc)
        return EXIT_ERROR
    except KeyboardInterrupt:  # pragma: no cover - interactive only
        get_logger().info("interrupted")
        return EXIT_OK


# -- commands ------------------------------------------------------------------


def cmd_templates(args) -> int:
    """List the catalogue. The answer to "what can I send?"."""
    catalogue = Catalogue(_catalogue_dirs(args)).load()
    templates = catalogue.by_group(args.group) if args.group else catalogue.all()

    if args.json:
        print(json.dumps([{
            "id": t.id, "group": t.group, "kind": t.kind, "severity": t.severity,
            "requires": t.requires, "description": t.description,
            "interactive": bool(t.buttons or t.poll),
        } for t in templates], indent=2, ensure_ascii=False))
        return EXIT_OK

    if not templates:
        print("no templates found in: {0}".format(", ".join(_catalogue_dirs(args))))
        return EXIT_ERROR

    # Grouped, not alphabetical: the catalogue's shape is the three groups, and
    # an id-sorted list interleaves them into noise.
    for group in GROUPS:
        members = [t for t in templates if t.group == group]
        if not members:
            continue
        print("\n{0}".format(group.upper()))
        for template in members:
            requires = ", ".join(template.requires) or "—"
            print("  {0:<26} {1}".format(template.id, template.description))
            print("  {0:<26} requires: {1}".format("", requires))
    print("")
    return EXIT_OK


def cmd_render(args) -> int:
    """Build a message and show exactly what would be sent. Offline."""
    catalogue = Catalogue(_catalogue_dirs(args)).load()
    template = catalogue.get(args.template)
    message = template.render(_payload(args), strict=not args.lenient)

    if args.json:
        print(json.dumps({
            "template": template.id,
            "text": message.text,
            "parts": message.parts(),
            "meta": message.meta(),
            "missing": message.missing,
            "length_utf16": tg_len(message.text),
        }, indent=2, ensure_ascii=False))
        return EXIT_OK

    parts = message.parts()
    print("─" * 60)
    for index, part in enumerate(parts, 1):
        if len(parts) > 1:
            print("[message {0} of {1}]".format(index, len(parts)))
        print(part)
        print("─" * 60)
    print("template : {0}  ({1}/{2})".format(template.id, template.group, template.severity))
    print("length   : {0} of {1} UTF-16 units{2}".format(
        tg_len(message.text), TELEGRAM_LIMIT,
        "  → {0} messages".format(len(parts)) if len(parts) > 1 else ""))
    if message.reply_markup:
        print("buttons  :")
        for number, row in enumerate(message.reply_markup["inline_keyboard"], 1):
            # Rows are shown because they are how the keyboard actually lays out
            # on a phone, and a five-button row is unusable in a way a flat list
            # of five buttons does not reveal.
            print("           row {0}".format(number))
            for cell in row:
                print("             {0!r} → {1}".format(cell["text"], cell["callback_data"]))
    if message.poll:
        print("poll     : {0!r}".format(message.poll["question"]))
        for option in message.poll["options"]:
            print("           ○ {0}".format(option))
        print("           (needs n8n/telegram-interactive.json; the live fan-out "
              "sends this as text)")
    if message.missing:
        print("MISSING  : {0}".format(", ".join(message.missing)))
    return EXIT_OK


def cmd_check(args) -> int:
    """Prove the seam is configured, before anything depends on it."""
    resolver = _resolver(args)
    seam = Seam(resolver, source=args.source)
    try:
        details = seam.preflight()
    except ConfigError as exc:
        get_logger().error("%s", exc)
        return EXIT_ERROR

    verifier = DeliveryVerifier(resolver)
    catalogue = Catalogue(_catalogue_dirs(args)).load()

    # Names and presence only — never a value (a printed credential is a leaked
    # credential, and this output routinely ends up pasted into a log).
    print("env file       : {0}".format(resolver.env_file or "<none>"))
    print("webhook url    : {0} is set".format(details["url_env"]))
    print("token          : {0} is set".format(details["token_env"]))
    print("signing secret : {0}".format(details["secret_source"]))
    print("delivery proof : {0}".format(
        "available" if verifier.available()
        else "UNAVAILABLE — N8N_BASE_URL/N8N_API_KEY absent, sends cannot be "
             "confirmed delivered (TG-02)"))
    print("interactive    : {0}".format(
        "NOTIFY_INTERACTIVE_URL is set — polls and buttons available"
        if resolver.present("NOTIFY_INTERACTIVE_URL")
        else "NOT SET — the default rail cannot attach buttons or send a poll "
             "(TG-18, TG-19)"))
    print("templates      : {0} loaded".format(len(catalogue.all())))
    return EXIT_OK


def cmd_send(args) -> int:
    """Render a template and send it through the seam."""
    resolver = _resolver(args)
    catalogue = Catalogue(_catalogue_dirs(args)).load()
    template = catalogue.get(args.template)
    message = template.render(_payload(args), strict=not args.lenient)

    seam = Seam(resolver, clock=Clock(), source=args.source, dry_run=args.dry_run,
                url_env=args.url_env or "NOTIFY_WEBHOOK_URL")
    parts = message.parts()
    results = []

    for index, part in enumerate(parts):
        # Buttons and polls ride the FIRST message only. Repeating a keyboard on
        # every chunk would offer the same decision several times, and pressing
        # the second copy is indistinguishable from pressing the first.
        extras = index == 0
        result = seam.send(
            message=part,
            kind=template.kind,
            summary=message.body if extras else None,
            meta=message.meta() if extras else {"template": template.id, "part": str(index + 1)},
            chat_id=args.chat_id,
        )
        results.append(result)
        if not result.accepted:
            get_logger().error("send failed: %s", result.note)
            break

    accepted = all(r.accepted for r in results)
    request_id = results[0].request_id if results else None

    if args.json:
        print(json.dumps({"accepted": accepted,
                          "parts": [r.as_dict() for r in results]},
                         indent=2, ensure_ascii=False))
    else:
        for result in results:
            print("{0} — {1}".format("accepted" if result.accepted else "FAILED", result.note))

    if not accepted:
        return EXIT_ERROR
    if args.dry_run:
        return EXIT_OK

    if args.verify:
        verdict = DeliveryVerifier(resolver).confirm(
            request_id=request_id, wait_seconds=args.verify_wait)
        print("delivery: {0} — {1}".format(verdict.status, verdict.note))
        return EXIT_OK if verdict.ok else EXIT_UNPROVEN

    print("NOTE: accepted by the webhook. Run `telegram verify --request-id {0}` "
          "to confirm it was delivered (TG-02).".format(request_id))
    return EXIT_OK


def cmd_verify(args) -> int:
    """Confirm a send actually reached the delivery node."""
    verifier = DeliveryVerifier(_resolver(args), delivery_node=args.node)
    verdict = verifier.confirm(request_id=args.request_id, needle=args.needle,
                               limit=args.limit, wait_seconds=args.wait)
    if args.json:
        print(json.dumps(verdict.as_dict(), indent=2, ensure_ascii=False))
    else:
        print("{0}: {1}".format(verdict.status, verdict.note))
    return EXIT_OK if verdict.ok else EXIT_UNPROVEN


def cmd_decode(args) -> int:
    """Decode a callback_data string, or a whole Telegram update."""
    raw = args.data
    if raw == "-":
        raw = sys.stdin.read().strip()

    if raw.lstrip().startswith("{"):
        answer = decode_update(json.loads(raw),
                               allowed_chats=args.allow_chat or None,
                               allowed_actions=args.allow_action or None)
        print(json.dumps(answer.as_dict(), indent=2, ensure_ascii=False))
        return EXIT_OK if answer.trusted else EXIT_ERROR

    print(json.dumps(decode_callback(raw), indent=2, ensure_ascii=False))
    return EXIT_OK


# -- helpers -------------------------------------------------------------------


def _resolver(args) -> EnvResolver:
    return EnvResolver(env_file=args.env_file)


def _catalogue_dirs(args) -> List[str]:
    dirs = [catalogue_dir()]
    extra = getattr(args, "templates_dir", None)
    if extra:
        # Prepended so a local override wins over the bundled catalogue.
        dirs.insert(0, os.path.expanduser(extra))
    return dirs


def _payload(args) -> Dict[str, Any]:
    """Assemble the render context from --data, stdin, and --set overrides."""
    payload: Dict[str, Any] = {}
    source = getattr(args, "data", None)
    if source:
        raw = sys.stdin.read() if source == "-" else _read(source)
        try:
            parsed = json.loads(raw)
        except ValueError as exc:
            raise ConfigError("--data is not valid JSON: {0}".format(exc))
        if not isinstance(parsed, dict):
            raise ConfigError("--data must be a JSON object of template fields")
        payload.update(parsed)

    for pair in getattr(args, "set", None) or []:
        if "=" not in pair:
            raise ConfigError("--set expects NAME=VALUE, got {0!r}".format(pair))
        name, value = pair.split("=", 1)
        payload[name.strip()] = value
    return payload


def _read(path: str) -> str:
    with open(os.path.expanduser(path), "r", encoding="utf-8") as handle:
        return handle.read()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="telegram",
        description="The studio's Telegram messaging seam: one signed envelope, "
                    "one template catalogue.")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    subparsers = parser.add_subparsers(dest="command")

    def common(sub, env=True, templates=True):
        if env:
            sub.add_argument("--env-file", default=DEFAULT_ENV_FILE,
                             help="dotenv file @env: names resolve against")
        if templates:
            sub.add_argument("--templates-dir", default=None,
                             help="extra template directory, searched before the bundled one")
        return sub

    def payload_args(sub):
        sub.add_argument("--data", default=None,
                         help="JSON file of template fields, or '-' for stdin")
        sub.add_argument("--set", action="append", metavar="NAME=VALUE",
                         help="override or supply one field (repeatable)")
        sub.add_argument("--lenient", action="store_true",
                         help="render blanks for missing required fields instead of failing")
        return sub

    listing = common(subparsers.add_parser("templates", help="list the catalogue"),
                     env=False)
    listing.add_argument("--group", choices=("input", "output", "interactive"))
    listing.add_argument("--json", action="store_true")

    render = payload_args(common(subparsers.add_parser(
        "render", help="build a message and print it, offline"), env=False))
    render.add_argument("template")
    render.add_argument("--json", action="store_true")

    check = common(subparsers.add_parser("check", help="prove the seam is configured"))
    check.add_argument("--source", default="telegram")

    send = payload_args(common(subparsers.add_parser("send", help="render and send")))
    send.add_argument("template")
    send.add_argument("--source", default="telegram",
                      help="the `source` field of the envelope; name the caller")
    send.add_argument("--url-env", default=None,
                      help="env name holding the destination webhook URL. Defaults to "
                           "NOTIFY_WEBHOOK_URL (the live fan-out). Use "
                           "NOTIFY_INTERACTIVE_URL to reach [STUDIO] Telegram "
                           "Interactive, which is the only workflow that can send a "
                           "poll or attach buttons (TG-18, TG-19)")
    send.add_argument("--chat-id", default=None,
                      help="override the destination chat (default: TELEGRAM_DEFAULT_CHAT)")
    send.add_argument("--dry-run", action="store_true", help="build and sign, send nothing")
    send.add_argument("--verify", action="store_true",
                      help="after sending, confirm the delivery node ran")
    send.add_argument("--verify-wait", type=float, default=20.0,
                      help="seconds to wait for the execution record (default 20)")
    send.add_argument("--json", action="store_true")

    verify = common(subparsers.add_parser(
        "verify", help="confirm a send was delivered, not merely accepted"), templates=False)
    verify.add_argument("--request-id", default=None)
    verify.add_argument("--needle", default=None,
                        help="text to look for, when there is no request id")
    verify.add_argument("--node", default=None,
                        help="delivery node name, or a comma-separated list. Defaults "
                             "to every known delivery node across the studio's "
                             "Telegram workflows")
    verify.add_argument("--limit", type=int, default=20, help="executions to scan")
    verify.add_argument("--wait", type=float, default=0.0,
                        help="seconds to keep looking for the execution record")
    verify.add_argument("--json", action="store_true")

    decode = subparsers.add_parser(
        "decode", help="decode a callback_data string or a Telegram update")
    decode.add_argument("data", help="callback_data, a JSON update, or '-' for stdin")
    decode.add_argument("--allow-chat", action="append", help="allow-listed chat id (repeatable)")
    decode.add_argument("--allow-action", action="append", help="allow-listed action (repeatable)")

    subparsers.add_parser("version", help="print the package version")
    return parser


_COMMANDS = {
    "templates": cmd_templates,
    "render": cmd_render,
    "check": cmd_check,
    "send": cmd_send,
    "verify": cmd_verify,
    "decode": cmd_decode,
}
