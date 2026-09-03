"""Command line for Sentinel."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import sys

from . import __version__, checks, config, report
from .errors import SentinelError
from .runner import LocalRunner, Runner, SshRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinel",
        description="Host integrity sweep — AIDE, distribution checksums and "
                    "signature scanning across configured hosts.",
    )
    parser.add_argument("--version", action="version", version=f"sentinel {__version__}")
    parser.add_argument("--baselines", metavar="DIR",
                        help=f"baselines directory (default: {config.DEFAULT_BASELINES}, "
                             f"or ${config.ENV_BASELINES})")

    sub = parser.add_subparsers(dest="command", required=True)

    sweep = sub.add_parser("sweep", help="run the configured checks and report")
    sweep.add_argument("--host", metavar="NAME", help="sweep one host instead of all")
    sweep.add_argument("--json", action="store_true", help="emit JSON instead of text")
    sweep.add_argument("--only", metavar="CHECK", action="append",
                       choices=config.KNOWN_CHECKS,
                       help="run only this check (repeatable). Use it to keep a "
                            "routine sweep off production's CPU: the fingerprint "
                            "check is one sha256sum, a full sweep is minutes.")
    sweep.add_argument("--dry-run", action="store_true",
                       help="print the commands that would run; execute nothing")

    sub.add_parser("hosts", help="list the configured hosts and their checks")

    return parser


def runner_for(host: config.Host) -> Runner:
    return LocalRunner() if host.local else SshRunner(host.target, host.identity)


def main(argv: list[str] | None = None, stdout=None) -> int:
    out = stdout or sys.stdout
    args = build_parser().parse_args(argv)

    try:
        cfg = config.load(args.baselines)
    except SentinelError as exc:
        print(f"sentinel: {exc}", file=sys.stderr)
        return 2

    if args.command == "hosts":
        for host in cfg.hosts:
            where = "local" if host.local else host.target
            print(f"{host.name}\t{where}\t{','.join(host.checks)}", file=out)
        return 0

    targets = [cfg.host(args.host)] if args.host else list(cfg.hosts)

    if getattr(args, "only", None):
        selected = tuple(args.only)
        targets = [dataclasses.replace(h, checks=tuple(c for c in h.checks if c in selected))
                   for h in targets]
        targets = [h for h in targets if h.checks]
        if not targets:
            print(f"sentinel: no configured host runs {', '.join(selected)}", file=sys.stderr)
            return 2

    if args.dry_run:
        for host in targets:
            for name in host.checks:
                print(f"{host.name}\t{name}", file=out)
        return 0

    results = []
    for host in targets:
        results.extend(checks.sweep_host(runner_for(host), host, cfg))

    taken_at = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    render = report.render_json if args.json else report.render_text
    print(render(results, taken_at), file=out)
    return report.exit_code_for(results)
