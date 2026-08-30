# Poller

A source-agnostic watch-and-report engine. Point it at any endpoint that returns
a list of things with states, and it reports each item that reaches a terminal
state — exactly once, on every rail you configure, and it tells you when it
stops watching.

Zero dependencies: Python 3.9+ standard library only. No pip, no Node, no paths
into other repos. The same tree runs in a container, on a VPS, or under cron on
a laptop.

- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** — the ways pollers have
  actually broken here, what each one looked like, and what guards it now.
  Read this before writing a config.
- **[IMPLEMENTATIONS.md](IMPLEMENTATIONS.md)** — how to plug in a new source,
  with Kaggle worked end to end and recipes for GitHub Actions, generic REST,
  and custom Python sources; plus how to configure the headless-session
  fallback and where n8n fits.

## Why this exists

Pollers here kept breaking in the same few ways: watching one hard-coded item
and missing a different one; exiting quietly so nothing was watching afterwards;
firing twice; announcing a result before the result existed; retrying a dead
credential for hours while looking healthy. Each fix was applied to one copied
script and never to the others.

So the engine is a package and a watch is a config. Every failure in
`KNOWN_ISSUES.md` has a guard in code and a test, and every guard is annotated
with the `KI-` id it came from — `grep -rn KI-07 poller/` finds the code an
incident bought.

## Quickstart

```bash
cd Packages/Poller
./run-tests.sh                                          # full suite, offline, ~1s

./bin/poller check  --config examples/kaggle-submissions.json   # prove credentials + endpoint
./bin/poller test   --config examples/kaggle-submissions.json   # prove the rails (dry)
./bin/poller run    --config examples/kaggle-submissions.json --once
./bin/poller status --config examples/kaggle-submissions.json
```

The minimum viable config:

```json
{
  "name": "my-watch",
  "env_file": "/studio/.env",
  "source": {
    "type": "http_json",
    "url": "https://api.example.com/jobs",
    "auth": { "scheme": "bearer", "token": "@env:MY_TOKEN" },
    "items_path": "data.jobs",
    "key_field": "id",
    "state": { "field": "status",
               "map": { "settled": ["done"], "failed": ["error"] } }
  },
  "sinks": [ { "type": "file", "path": "~/reports.md" } ]
}
```

## How it works

```
                 ┌──────────┐   items    ┌──────────┐
   any API ─────▶│  Source  │───────────▶│  Engine  │
                 └──────────┘            └────┬─────┘
             http_json · kaggle · python      │
                                              │  new item in a terminal state?
                                              ▼
                                       ┌─────────────┐
                                       │  Store      │  key:state ledger
                                       │  (durable)  │  + per-sink delivery
                                       └──────┬──────┘
                                              │  what does each rail still owe?
                                              ▼
                            ┌─────────────────┴──────────────────┐
                            ▼            ▼            ▼          ▼
                          file        slack       telegram    command
                        (always)                 (signed n8n)
                                                                 ┊
                          supervising session gone? ┄┄┄┄┄┄┄┄┄┄┄┄▶ headless
                                                                 claude -p
```

Each tick: fetch → classify → enroll anything newly terminal → drain the
delivery ledger → rewrite the heartbeat. Every exit path — duration reached,
signal, fatal error, unhandled crash — emits a report before the process ends.

### The guarantees

| Property | How |
|---|---|
| **At most one report per event** | Dedup on `item_key:state`, persisted |
| **At least one delivery attempt per rail** | Per-sink ledger; retries survive restarts |
| **A dead credential fails in seconds, not hours** | 401/403/404 are fatal; startup preflight |
| **A stopped watch is always announced** | Lifecycle events on every exit path |
| **Liveness is observable from outside** | Heartbeat file + `poller status` (no `ps` needed) |
| **Two instances cannot double-post** | PID lock with `/proc` liveness and stale reclaim |
| **A crash mid-write cannot lose state** | Atomic temp-file + rename + fsync |
| **Losing the launching session is noticed** | Supervisor liveness probe; `supervisor_lost` event |
| **Reports still get acted on after that** | Optional `claude_code` fallback rail |
| **No secret reaches a log, argv or URL** | Redacting formatter; stdin for commands |

## Commands

| Command | Does | Exit codes |
|---|---|---|
| `run` | The watch. `--once`, `--dry-run`, `--no-seed`, `--force`, `--supervisor-pid` | 0 clean · 2 fatal · 3 already running |
| `check` | Validates config, resolves credentials, calls the source, prints what it *would* report. Sends nothing, writes nothing | 0 ok · 2 problem |
| `status` | ALIVE / STALE / STOPPED / NEVER_RAN from the heartbeat. `--json` | 0 alive · 1 not |
| `test` | Pushes a synthetic event through every rail. Dry unless `--live` | 0 ok · 1 a rail failed |
| `state` | Remembered items, undelivered reports, abandoned ones. `--json` | 0 |

## Layout

```
Packages/Poller/
├── README.md              this file
├── KNOWN_ISSUES.md        the failure catalogue and its guards
├── IMPLEMENTATIONS.md     how to plug in a new source
├── bin/poller             executable entry point (no install needed)
├── run-tests.sh           the whole suite, offline
├── examples/              kaggle · kaggle-with-fallback · github-actions · generic-http
├── poller/
│   ├── engine.py          the loop, delivery, heartbeat, lifecycle
│   ├── state.py           durable dedup + per-sink delivery ledger
│   ├── sinks.py           file · stdout · slack · notify_webhook · webhook ·
│   │                      command · claude_code
│   ├── sources/           base · http_json (declarative) · kaggle (preset)
│   ├── http.py            retrying HTTPS client (transient vs fatal)
│   ├── config.py          config schema, defaults, validation
│   ├── lock.py            single-instance lock without `ps`
│   ├── supervisor.py      liveness of the session that launched the watch
│   ├── clock.py           injectable time; interruptible sleep
│   ├── envfile.py         read .env without sourcing it
│   ├── render.py          total templating
│   ├── log.py             redacting logger
│   ├── model.py           Item · Event · ItemState
│   └── errors.py          the transient/fatal taxonomy
└── tests/                 the suite; no network, no fixtures to install
```

## Testing

```bash
./run-tests.sh          # or: python3 -m unittest discover -s tests -t tests
```

Everything is offline and deterministic: the clock is injectable, so a
twelve-hour watch runs in milliseconds, and HTTP backoff is asserted exactly
because the jitter source is injected too. The suite includes a frozen vector
generated from the reference Node notify client — if the Python envelope ever
drifts, a test fails instead of a delivery.

## Surviving the session that launched it

A poller is a detached OS process: it already outlives the Claude Code session,
terminal or cron job that started it. What does *not* survive is the
**attention** — reports keep landing with nobody reading them.

Name a supervisor and the poller notices:

```json
"supervisor": { "pid": "@env:CLAUDE_PID", "on_loss": "fallback" }
```

Inside a Claude Code session `$CLAUDE_PID` needs no setup; `--supervisor-pid`
and a `heartbeat_file` are the alternatives. When that process goes away the
poller emits `supervisor_lost` once and activates any rail marked
`"when": "fallback"` — typically the `claude_code` sink, which spawns
`claude -p` so a successor session can post the result, update a board, or open
an issue. It is off unless configured, bounded by `max_spawns_per_run`, limited
to the tools you name, and it treats item fields as untrusted data. See
`IMPLEMENTATIONS.md` and KI-19/KI-20/KI-21.

**The poller does not run on n8n**, and should not: it needs a durable dedup
ledger and per-sink delivery state. n8n is the *delivery* rail (the signed
Telegram seam) and the right place for the outer dead-man's-switch that watches
the watcher.

## Adding to the package

- A new API that fits the declarative shape → a config, and nothing else.
- A new API that needs logic → a `python` source (see IMPLEMENTATIONS.md).
- A new rail → a `Sink` subclass with a `send`; register it in `BUILTIN_SINKS`.
- A new failure mode → an entry in `KNOWN_ISSUES.md`, a guard, and a test that
  fails without the guard.
