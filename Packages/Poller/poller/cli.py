"""Command line: `poller run | status | check | test | state | version`.

`run` is the watch. The other four exist because the historical failures were
not in the polling — they were in *not being able to tell what the poller was
doing*. `check` proves the credentials and the endpoint before a twelve-hour
watch starts; `status` answers "is it alive?" from outside the process; `test`
proves the report rails without waiting for a real event.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

from . import __version__
from .clock import Clock, age_seconds
from .config import Config, load_config
from .engine import EXIT_FATAL, EXIT_OK, Engine
from .envfile import EnvResolver
from .errors import ConfigError, PollerError
from .lock import InstanceLock, is_process_alive
from .log import configure, get_logger
from .model import Event, EventReason, Item, ItemState
from .render import render
from .sinks import build_sinks
from .sources import build_source
from .state import Store
from .supervisor import Supervisor

EXIT_UNHEALTHY = 1


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_UNHEALTHY

    if args.command == "version":
        print("poller {0}".format(__version__))
        return EXIT_OK

    try:
        config = load_config(args.config)
        configure(verbose=getattr(args, "verbose", False), logfile=config.log_file)
        return _COMMANDS[args.command](args, config)
    except ConfigError as exc:
        configure(verbose=getattr(args, "verbose", False))
        get_logger().error("configuration error: %s", exc)
        return EXIT_FATAL
    except PollerError as exc:
        get_logger().error("%s", exc)
        return EXIT_FATAL
    except KeyboardInterrupt:  # pragma: no cover - interactive only
        get_logger().info("interrupted")
        return EXIT_OK


# -- commands -----------------------------------------------------------------

def cmd_run(args, config: Config) -> int:
    engine = _engine(config, dry_run=args.dry_run, supervisor_pid=args.supervisor_pid)
    seed = False if args.no_seed else None
    return engine.run(once=args.once, seed=seed, force=args.force)


def cmd_check(args, config: Config) -> int:
    """Prove the whole chain without sending anything or writing state."""
    log = get_logger()
    resolver = EnvResolver(config.env_file)
    source = build_source(config.source, resolver)
    sinks = build_sinks(config.sinks, resolver, dry_run=True)

    log.info("config    OK   %s (interval %ss, limit %s)",
             config.name, config.interval_seconds,
             "none" if config.max_duration_hours == 0 else "{0}h".format(config.max_duration_hours))
    log.info("state     ->   %s", config.state_file)
    log.info("heartbeat ->   %s", config.heartbeat_file)

    for sink in sinks:
        sink.preflight()
        log.info("sink      OK   %s (%s)", sink.name, type(sink).__name__)

    items = source.fetch()
    log.info("source    OK   %s returned %d item(s)", source.describe(), len(items))
    by_state: Dict[str, int] = {}
    for item in items:
        by_state[item.state] = by_state.get(item.state, 0) + 1
    for state in ItemState.ALL:
        if by_state.get(state):
            log.info("               %-8s %d", state, by_state[state])
    reportable = [i for i in items if i.state in config.notify_states]
    log.info("would report on %d of %d item(s) if the state file were empty", len(reportable), len(items))
    for item in reportable[:5]:
        log.info("               %s [%s] %s", item.key, item.state, item.title)
    return EXIT_OK


def cmd_status(args, config: Config) -> int:
    """Answer "is this poller alive?" from outside the process.

    Exit code 0 = alive, 1 = stale/stopped/never started, so a cron watchdog can
    simply test the exit status.
    """
    clock = Clock()
    beat = _read_json(config.heartbeat_file)
    lock_holder = InstanceLock(config.lock_file, config.name).holder()
    pid_alive = is_process_alive((lock_holder or {}).get("pid"),
                                (lock_holder or {}).get("cmdline"))

    if not beat:
        report = {"verdict": "NEVER_RAN", "detail": "no heartbeat at {0}".format(config.heartbeat_file)}
    else:
        age = age_seconds(beat.get("updated_at"), clock.now())
        limit = max(3 * float(beat.get("interval_seconds") or config.interval_seconds), 60.0)
        status = beat.get("status")
        if status in ("ended", "failed"):
            report = {"verdict": "STOPPED", "detail": "{0}: {1}".format(status, beat.get("reason", ""))}
        elif age is None:
            report = {"verdict": "UNKNOWN", "detail": "unparseable heartbeat timestamp"}
        elif age > limit:
            report = {"verdict": "STALE",
                      "detail": "last tick {0:.0f}s ago, expected within {1:.0f}s".format(age, limit)}
        elif not pid_alive and lock_holder:
            report = {"verdict": "STALE", "detail": "lock pid {0} is gone".format(lock_holder.get("pid"))}
        else:
            report = {"verdict": "ALIVE", "detail": "tick {0}, {1:.0f}s ago".format(beat.get("ticks"), age)}
        report.update(
            ticks=beat.get("ticks"), pid=beat.get("pid"), status=status,
            consecutive_failures=beat.get("consecutive_failures"),
            last_error=beat.get("last_error"), updated_at=beat.get("updated_at"),
            source=beat.get("source"),
        )
    report["name"] = config.name
    report["lock_pid_alive"] = pid_alive

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("{0}: {1} — {2}".format(config.name, report["verdict"], report["detail"]))
        for key in ("ticks", "pid", "consecutive_failures", "last_error", "updated_at", "source"):
            if report.get(key) not in (None, "", 0):
                print("  {0:<22}{1}".format(key, report[key]))
    return EXIT_OK if report["verdict"] == "ALIVE" else EXIT_UNHEALTHY


def cmd_test(args, config: Config) -> int:
    """Push a synthetic event through every sink. Dry unless `--live`."""
    resolver = EnvResolver(config.env_file)
    sinks = build_sinks(config.sinks, resolver, dry_run=not args.live)
    item = Item(
        key="TEST-0000",
        state=ItemState.SETTLED,
        title="poller self-test",
        fields={"score": "0.000", "description": "poller self-test",
                "date": Clock().iso(), "error": ""},
    )
    spec = config.template_for(EventReason.SETTLED)
    event = Event(
        reason=EventReason.SETTLED,
        dedup_key="selftest",
        title=render(spec.get("title", "{title}"), item.context()),
        body="This is a poller self-test from {0}. No real event occurred.\n{1}".format(
            config.name, render(spec.get("body", ""), item.context())),
        severity="info",
        item=item,
    )
    log = get_logger()
    failures = 0
    for sink in sinks:
        try:
            sink.deliver(event)
            log.info("sink %-16s %s", sink.name, "SENT" if args.live else "rendered (dry-run)")
        except Exception as exc:
            failures += 1
            log.error("sink %-16s FAILED: %s", sink.name, exc)
    if not args.live:
        log.info("dry run — nothing was sent. Re-run with --live to actually deliver.")
    return EXIT_OK if failures == 0 else EXIT_UNHEALTHY


def cmd_state(args, config: Config) -> int:
    """Show what the poller remembers: seen items and undelivered reports."""
    store = Store(config.state_file)
    resolver = EnvResolver(config.env_file)
    sink_names = [s.name for s in build_sinks(config.sinks, resolver, dry_run=True)]
    summary: Dict[str, Any] = {
        "name": config.name,
        "state_file": config.state_file,
        "created_at": store.created_at,
        "seeded_at": store.seeded_at,
        "stats": store.stats(),
        "undelivered": [
            {"dedup_key": rec.dedup_key, "reason": rec.reason, "attempts": rec.attempts,
             "delivered": rec.delivered, "outstanding": rec.outstanding(sink_names),
             "failures": rec.failures, "fatal": rec.fatal}
            for rec in store.undelivered(sink_names, config.max_delivery_attempts)
        ],
        "abandoned": [rec.dedup_key for rec in store.records.values() if rec.abandoned],
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print("{0}: {1} record(s), {2} tracked item(s), seeded {3}".format(
            config.name, summary["stats"]["records"], summary["stats"]["tracked_items"],
            store.seeded_at or "never"))
        for entry in summary["undelivered"]:
            print("  UNDELIVERED {0} -> {1} (attempt {2})".format(
                entry["dedup_key"], ",".join(entry["outstanding"]), entry["attempts"]))
        for key in summary["abandoned"]:
            print("  ABANDONED   {0}".format(key))
    return EXIT_OK


# -- wiring -------------------------------------------------------------------

_COMMANDS = {
    "run": cmd_run,
    "check": cmd_check,
    "status": cmd_status,
    "test": cmd_test,
    "state": cmd_state,
}


def _engine(config: Config, dry_run: bool = False, supervisor_pid: Optional[int] = None) -> Engine:
    resolver = EnvResolver(config.env_file)
    source = build_source(config.source, resolver)
    sinks = build_sinks(config.sinks, resolver, dry_run=dry_run)
    supervisor_config = dict(config.supervisor)
    if supervisor_pid:
        supervisor_config["pid"] = supervisor_pid   # --supervisor-pid wins
    return Engine(config, source, sinks,
                  supervisor=Supervisor(supervisor_config, resolver=resolver))


def _read_json(path: str) -> Optional[dict]:
    try:
        with open(os.path.expanduser(path), "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="poller",
        description="Watch any collection endpoint and report each new terminal item exactly once.",
    )
    parser.add_argument("--version", action="version", version="poller {0}".format(__version__))
    subparsers = parser.add_subparsers(dest="command")

    def with_config(name: str, help_text: str) -> argparse.ArgumentParser:
        sub = subparsers.add_parser(name, help=help_text)
        sub.add_argument("-c", "--config", required=True, help="path to the poller JSON config")
        sub.add_argument("-v", "--verbose", action="store_true", help="debug logging")
        return sub

    run = with_config("run", "start the watch")
    run.add_argument("--once", action="store_true", help="run a single tick and exit (cron mode)")
    run.add_argument("--dry-run", action="store_true", help="render reports but send nothing")
    run.add_argument("--no-seed", action="store_true",
                     help="report on everything already terminal (default: seed and suppress)")
    run.add_argument("--force", action="store_true", help="take over a lock held by a dead process")
    run.add_argument("--supervisor-pid", type=int, default=None, metavar="PID",
                     help="watch this pid as the supervising session; when it dies, "
                          "fallback rails activate (inside Claude Code: $CLAUDE_PID)")

    with_config("check", "validate config, credentials and the source without sending anything")

    status = with_config("status", "report whether the watch is alive")
    status.add_argument("--json", action="store_true", help="machine-readable output")

    test = with_config("test", "push a synthetic event through the sinks")
    test.add_argument("--live", action="store_true", help="actually send (default is dry-run)")

    state = with_config("state", "show remembered items and undelivered reports")
    state.add_argument("--json", action="store_true", help="machine-readable output")

    subparsers.add_parser("version", help="print the version")
    return parser


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
