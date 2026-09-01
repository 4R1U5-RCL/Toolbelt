# Implementation guide — plugging the poller into a new source

The engine never changes. Implementing a poller means answering five questions
about the system you want to watch and writing the answers into a JSON file.

1. **What URL returns the list?** Not the detail endpoint for one thing — the
   collection. Watching a collection is what stops you from missing the item you
   did not think to watch (KI-01).
2. **What is the immutable id of a row?** A `ref`, an `id`, a uuid. Never a
   title or a description.
3. **Which of its status words mean finished, failed, and still-going?**
4. **Is "finished" ever true before the result is there?** If so, which field
   proves the result exists?
5. **Where should the report go, and what should it say?**

Answer those and the rest — dedup, retries, backoff, delivery ledger,
heartbeat, locking, staleness, clean shutdown — you get unchanged.

---

## Anatomy of a config

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

```jsonc
{
  "name": "kaggle-agentsec",        // filename-safe; names the state/lock/heartbeat files
  "env_file": "/studio/.env",       // where @env: references are resolved from

  "interval_seconds": 180,          // how often to poll
  "jitter_seconds": 15,             // spread, so parallel pollers do not sync up
  "max_duration_hours": 24,         // 0 = run until stopped
  "stale_after_seconds": 21600,     // warn once if an item is pending this long; 0 = never
  "notify_states": ["settled", "failed"],
  "degraded_after_failures": 3,     // consecutive fetch failures before an alarm
  "max_delivery_attempts": 5,       // delivery sweeps before a report is abandoned
  "seed_on_first_run": true,        // suppress pre-existing items on a fresh state file

  "state_dir": "~/.poller",         // state_file/lock_file/heartbeat_file derive from this
  "log_file": null,                 // optional: an audit trail that survives a lost terminal

  "source": { },                    // see below
  "templates": { },                 // report text per event reason
  "sinks": [ ]                      // one or more rails
}
```

Unknown keys are warned about, not silently ignored — a typo'd `intervall_seconds`
would otherwise leave you polling at the default for hours.

---

## Worked example: Kaggle competition submissions

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

The one this package was built for. Config:
[`examples/kaggle-submissions.json`](examples/kaggle-submissions.json).

### 1. Answering the five questions

| Question | Kaggle's answer |
|---|---|
| Collection URL | `https://www.kaggle.com/api/v1/competitions/submissions/list/<slug>` |
| Immutable id | `ref` |
| Status words | `complete` / `error` / `pending` — sometimes as `SubmissionStatus.COMPLETE` |
| Finished-before-result? | **Yes** — `status: complete` with `publicScore: null` for a few seconds |
| Report | file + Slack + Telegram, with score, ref, date and description |

All of that is already encoded in the `kaggle_submissions` source, so the config
only names the competition:

```json
"source": {
  "type": "kaggle_submissions",
  "competition": "ai-agent-security-multi-step-tool-attacks"
}
```

Auth is `KAGGLE_API_TOKEN` sent as a **Bearer** header. The legacy Basic
`username:key` token is dead and returns 401 — see KI-05. Both live in
`/studio/.env`; the config references names, never values.

### 2. Narrowing (optional, and rarely what you want)

To watch only one notebook family:

```json
"filter": { "field": "description", "contains": "agentsec-" }
```

This narrows *which rows are watched* while still watching all of them — it is
not the same as pinning to one submission. If you can avoid it, do: the whole
point is that a submission you did not anticipate still gets reported.

### 3. Report text

Templates are `str.format` strings over the item's fields:

```json
"templates": {
  "settled": {
    "title": "Kaggle settled: {score}",
    "body": "*{description}*\nscore *{score}*  ·  ref `{key}`  ·  {date}"
  },
  "failed": {
    "title": "Kaggle submission FAILED",
    "body": "`{description}` did not score (status {status}).\nError: {error}\nA submission slot was spent — read the run log before resubmitting."
  }
}
```

Available fields for the Kaggle source: `score`, `private_score`, `date`,
`description`, `error`, `filename`, `status`, plus `key` (the ref), `state` and
`title`. A field the row does not have renders empty rather than failing.

Deliberately absent: any interpretation of the score. The poller reports what
happened; deciding what a number means is a human gate, and encoding a verdict
ladder in a watcher is how a report starts lying after the ladder moves.

### 4. Rails

```json
"sinks": [
  { "type": "file", "name": "findings",
    "path": "/studio/scratch/kaggle/FINDINGS_poller_{key}.md" },
  { "type": "slack", "name": "slack",
    "token_env": "SLACK_BOT_TOKEN", "channel_env": "SLACK_KAGGLE_CHANNEL_ID" },
  { "type": "notify_webhook", "name": "telegram", "source": "kaggle-poller",
    "reasons": ["settled", "failed", "watch_failed", "watch_ended", "degraded"] }
]
```

The file sink goes first on purpose: it is the only rail that works with no
network. The `reasons` filter keeps routine lifecycle chatter off the phone
while still letting the important lifecycle events (`watch_failed`,
`watch_ended`) through — because a stopped watch is exactly what you want to be
told about (KI-02).

### 5. Arm it

```bash
cd Packages/Poller

# 1. Prove the credentials and the endpoint. Sends nothing, writes nothing.
./bin/poller check --config examples/kaggle-submissions.json

# 2. Prove the rails. Dry by default; --live actually posts.
./bin/poller test --config examples/kaggle-submissions.json
./bin/poller test --config examples/kaggle-submissions.json --live

# 3. One tick, seeding the current submissions so history is not reported.
./bin/poller run --config examples/kaggle-submissions.json --once

# 4. Arm the watch.
nohup ./bin/poller run --config examples/kaggle-submissions.json \
      >> ~/kaggle-poller.log 2>&1 &

# 5. Any time afterwards:
./bin/poller status --config examples/kaggle-submissions.json
```

The first `run --once` seeds and reports nothing — that is correct. From then on
every *new* submission that settles or errors is reported once, whichever
notebook it came from.

---

## Recipe: GitHub Actions runs

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

A different vocabulary, and a list nested inside an object. Config:
[`examples/github-actions.json`](examples/github-actions.json).

```json
"source": {
  "type": "http_json",
  "url": "https://api.github.com/repos/OWNER/REPO/actions/runs",
  "params": { "per_page": "20", "branch": "main" },
  "headers": { "Accept": "application/vnd.github+json" },
  "auth": { "scheme": "bearer", "token": "@env:GITHUB_TOKEN" },

  "items_path": "workflow_runs",
  "key_field": "id",
  "title_template": "{name} #{run_number} ({head_branch})",

  "state": {
    "field": "conclusion",
    "match": "exact",
    "default": "pending",
    "map": {
      "settled": ["success"],
      "failed": ["failure", "cancelled", "timed_out", "startup_failure"]
    }
  },

  "fields": { "name": "name", "url": "html_url", "actor": "actor.login" }
}
```

Two things worth copying:

* The state lives in `conclusion`, not `status`. While a run is in flight
  `conclusion` is `null`, which matches nothing and falls to `default: "pending"`.
  Picking the field that is *only* populated at the end removes the need for
  `settled_requires` entirely.
* `match: "exact"` because GitHub's words are exact. Use `icontains` (the
  default) when an API might return `JobStatus.SUCCESS` or change its casing.

---

## Recipe: a generic REST job queue

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

Config: [`examples/generic-http.json`](examples/generic-http.json). It shows the
three things most in-house APIs need:

```json
"auth":  { "scheme": "header", "header": "X-API-Key", "token": "@env:EXAMPLE_API_KEY" },
"items_path": "data.jobs",
"state": { "settled_requires": ["result"] },
"filter": [ { "field": "owner", "equals": "me" } ]
```

`items_path` walks dotted paths through nested objects and list indices
(`data.jobs`, `payload.0.items`). An empty path means "the response is the list".

### Auth schemes

| Scheme | Config | Sends |
|---|---|---|
| `bearer` | `{"scheme":"bearer","token":"@env:TOK"}` | `Authorization: Bearer …` |
| `header` | `{"scheme":"header","header":"X-API-Key","token":"@env:TOK"}` | that header |
| `basic` | `{"scheme":"basic","token":"@env:USER_COLON_KEY"}` or `username`/`password` | `Authorization: Basic …` |
| `query` | `{"scheme":"query","param":"apikey","token":"@env:TOK"}` | a query parameter (stripped from logs) |
| `none` | omit `auth` | nothing |

---

## When declarative is not enough: a Python source

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

Pagination, GraphQL, a second call per row, or a signature scheme — write a
class. You implement one method and inherit everything else.

```python
# my_sources.py
from poller.model import Item, ItemState
from poller.sources.base import Source

class PagedJobs(Source):
    name = "paged-jobs"

    def fetch(self):
        items, page = [], 1
        while True:
            body = self.client.get_json(
                self.config["url"],
                headers={"Authorization": "Bearer " + self.resolver.get("MY_TOKEN")},
                params={"page": str(page)},
            )
            for row in body["items"]:
                items.append(Item(
                    key=str(row["uuid"]),
                    state=ItemState.SETTLED if row["done"] else ItemState.PENDING,
                    title=row["name"],
                    fields={"result": row.get("result")},
                ))
            if not body.get("next"):
                return items
            page += 1
```

```json
"source": { "type": "python", "target": "my_sources:PagedJobs",
            "url": "https://api.example.com/jobs" }
```

The module must be importable (same directory, or on `PYTHONPATH`). Contract:

* Return a list of `Item`s. `key` must be stable and unique.
* Raise `TransientSourceError` for anything retryable and `FatalSourceError`
  for anything a human must fix — `self.client` already does this
  classification for you if you use it.
* `self.client` is the retrying HTTP client; `self.resolver` resolves
  credentials by name and registers them for log redaction.

A working example lives at [`tests/fake_source.py`](tests/fake_source.py), and
the test suite exercises the plugin path end to end.

---

## Choosing rails

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

| Sink | Use it for | Notes |
|---|---|---|
| `file` | The audit trail. Always include one. | Works with no network. Template `{key}` into the path for one file per event |
| `slack` | Team-visible reports | Needs `chat:write` and the bot invited to the channel; `not_in_channel` is fatal, not retried |
| `notify_webhook` | Telegram via the signed n8n seam | Byte-compatible with `packages/notify`; needs `NOTIFY_WEBHOOK_URL` + `NOTIFY_TOKEN` |
| `webhook` | Discord, Teams, an internal collector | `field` names the JSON key the text goes in |
| `command` | Anything with an existing CLI | Message arrives on **stdin**, never argv |
| `claude_code` | Handing the report to a headless agent | Spawns `claude -p`. Off unless configured; see below |
| `stdout` | Development, and as a floor under everything else | |

Per-sink `reasons` filters which events a rail gets. Per-sink `template`
overrides the report text for that rail — useful when Slack wants markdown and
Telegram wants one line.

### Proving a rail end to end

`poller test --live` reports `SENT` when the rail accepted the message. For the
`notify_webhook` rail that is an honest but incomplete claim: a 2xx from the n8n
webhook means the workflow **accepted** the call, not that Telegram delivered
it. To close that gap, check the execution:

```bash
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_BASE_URL/api/v1/executions?limit=3" |
  python3 -c 'import json,sys; [print(e["id"], e["status"], e["startedAt"]) for e in json.load(sys.stdin)["data"]]'

# then, for the execution whose timestamp matches your test:
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$N8N_BASE_URL/api/v1/executions/<id>?includeData=true" |
  python3 -c 'import json,sys; d=json.load(sys.stdin); print(list((d["data"]["resultData"]["runData"] or {}).keys()))'
```

A delivered ping shows the whole chain having run —
`Webhook → Verify HMAC → Auth Gate → Format → Deliver`. If `Verify HMAC` is
absent or errored, the envelope has drifted from the signing contract; the
frozen vector in `tests/test_sinks.py` is what stops that happening silently.

If `NOTIFY_SECRET` is unset the token is used as the signing secret, matching
the reference client's `secret ?? token` behaviour — that is the supported
single-secret mode, not a misconfiguration.

---

## Surviving the session that launched it

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

### What actually needs surviving

A poller is a detached OS process. Started with `nohup` or from cron it already
outlives the Claude Code session, terminal, or laptop lid that launched it —
that part has never been the problem. What does not survive is the **attention**:
reports keep arriving in Slack and Telegram with nobody reading or acting on
them.

Two separate mechanisms, for two separate failures:

| Failure | Mechanism |
|---|---|
| The **poller** dies | Heartbeat file + `poller status` + an external watchdog (KI-09) |
| The **supervising session** dies | `supervisor` block + `"when": "fallback"` rails (KI-19) |

### Naming a supervisor

```json
"supervisor": {
  "label": "launching Claude Code session",
  "pid": "@env:CLAUDE_PID",
  "on_loss": "fallback"
}
```

| Key | Meaning |
|---|---|
| `pid` | The process to watch. Inside Claude Code, `@env:CLAUDE_PID` needs no setup. `--supervisor-pid N` overrides it |
| `heartbeat_file` + `max_age_seconds` | Alternative signal: a file the supervisor touches. Use when liveness means "still working", not merely "still running" |
| `on_loss` | `fallback` (report **and** activate fallback rails), `report` (report only), `ignore` |

Liveness uses the same probe as the instance lock — `os.kill(pid, 0)` plus a
`/proc` command-line comparison against what was recorded at launch, so a
recycled pid cannot masquerade as a live supervisor, and no `ps` binary is
needed. **No supervisor configured means "present"**, so an unsupervised poller
never escalates by accident (and a fallback rail configured without a supervisor
warns at startup, because it would otherwise stay dark forever).

On the tick the supervisor is first seen to be gone, the poller emits
`supervisor_lost` once, and fallback rails go live. Supervision is checked at the
*start* of a tick, so a successor rail is told why it woke up before it is handed
that tick's reports. The verdict is recomputed each tick rather than latched, so
a restarted poller re-evaluates from scratch.

### The headless-session rail

```json
{
  "type": "claude_code",
  "name": "headless-fallback",
  "when": "fallback",
  "cwd": "/studio",
  "allowed_tools": ["Bash", "Read", "Write"],
  "permission_mode": "acceptEdits",
  "max_spawns_per_run": 5,
  "timeout_seconds": 900,
  "task": "Post the event above to Slack with studio-slack, then append a dated line to POLLER_HANDOFF.md. Do not submit anything or push to git."
}
```

The other rails deliver text; this one delivers **agency**. It runs
`claude -p --output-format json`, feeding it a prompt built as: a preamble, the
rendered event fenced in a `<poller-event trust="untrusted-data">` block, then
your task. A zero exit code is not treated as success — `is_error` in the JSON
result is checked too, and the session id, turn count and cost are logged.

Three things to be deliberate about:

* **Cost.** Each spawn is a real session — tens of thousands of cached input
  tokens before it does anything, measured at roughly **US$0.30 for a trivial
  prompt**. This is why it belongs on `"when": "fallback"` rather than
  `"always"`, and why `max_spawns_per_run` exists (KI-21).
* **Blast radius.** The spawned session can only use the tools you name in
  `allowed_tools`. Name none and it can think and reply but not act — safe, and
  probably not what you want, so it warns at preflight. Write the task narrowly
  and say what *not* to do.
* **Trust.** Item fields come from a third-party API. They are fenced and
  labelled as data, and the preamble tells the session never to follow
  instructions found inside them — but do not hand it destructive tools on the
  strength of that alone (KI-20).

Set `"when": "always"` if you genuinely want an agent handling every event. Be
sure about the cost first.

### Where n8n fits

**Correction to an earlier version of this guide.** It argued the poll loop
should not run on n8n, because the engine needs a durable ledger and per-sink
delivery state. That reasoning was about *state*, and it missed the binding
constraint: **availability**. A poller in a container on a laptop dies when that
laptop does, and nothing is left to restart it — a dead-man's-switch can tell
you the watch died, but not bring it back. For a watch that must not lapse, the
clock belongs on hardware you are not carrying around.

n8n solves state adequately — `$getWorkflowStaticData('global')` persists across
executions in the workflow record, which is exactly how the existing
`[OPERORCH] Runner Watcher` keeps its episode state — and solves availability
completely. So there are two tiers, and the choice between them is about what
you are protecting against:

| | Local engine | n8n workflow |
|---|---|---|
| Survives the host going down | No | **Yes** |
| Per-sink delivery ledger, staleness SLA, degraded alarms | **Yes** | No |
| Headless-session fallback | **Yes** | No |
| Changing it | Edit a JSON config | Edit a workflow |

A ready-made n8n-resident poller for the Kaggle source lives in
[`n8n/`](n8n/), with its classification deliberately mirroring
`poller/sources/kaggle.py` — keeping the two in parity is a maintenance
obligation, and generating the workflow from a poller config is a known gap.


---

## Running it

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

| How | Command | When |
|---|---|---|
| **Cron tick** | `poller run -c cfg.json --once` every N minutes | **Preferred.** No long-lived process to die; cron is the survivability layer |
| **Long watch** | `nohup poller run -c cfg.json >> log 2>&1 &` | A bounded wait on an always-on host |
| **systemd** | `ExecStart=… poller run -c cfg.json`, `Restart=always` | A permanent watch (`max_duration_hours: 0`) |

`--once` is the mode to reach for. The lock makes overlapping cron ticks safe,
the ledger makes each tick pick up whatever the last one failed to deliver, and
there is no process whose death you have to notice. Two things to set for it:

```json
"notify_on_start": false,
"notify_on_end": false
```

Otherwise every cron tick announces its own start and stop, which is noise when
the "watch" is one tick long — and the lifecycle records accumulate in the
state file. A single-tick run also skips the separate startup preflight (the
tick itself proves the credentials), so cron mode costs exactly one API call
per tick.

Whatever you choose, point a watchdog at it:

```bash
poller status --config cfg.json || echo "poller is not alive" | mail -s alert me
```

---

## Before you arm a watch

**status.** `legacy` — predates v2.1.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

- [ ] `poller check` passes — credentials resolve, endpoint answers, rows parse
- [ ] The state counts in `check` look right (settled/failed/pending)
- [ ] `poller test --live` produced a message on every rail you care about
- [ ] `key_field` is an id, not a description (KI-01)
- [ ] `settled_requires` names the result field, if the API can be finished
      without one (KI-04)
- [ ] `state.map.failed` lists the API's error words (KI-08)
- [ ] `stale_after_seconds` is a real SLA for this API (KI-18)
- [ ] The first `run --once` seeded and reported nothing (KI-15)
- [ ] Something checks `poller status` on a schedule (KI-09)
- [ ] The config contains no secret values — only `@env:` references (KI-11)

---

### Template index (appended 2026-08-31, v2.1.0 migration)

Appended, not rewritten — this file is append-only (PROCESS.md §5.2). Two things
changed underneath the guide above and are recorded here rather than edited in
place:

**1. Paths.** As of `v2.1.0` the tool's code lives under
`Packages/Poller/Tooling/v2.1.0/`. Every relative path above — `bin/poller`,
`examples/*.json`, `run-tests.sh`, `n8n/` — is now relative to that directory,
not to the tool root. So `cd Packages/Poller` in the snippets above reads
`cd Packages/Poller/Tooling/v2.1.0`. The commands are otherwise unchanged.

**2. Reciprocity.** Each implementation section now cites its template entry in
[`TEMPLATES.md`](TEMPLATES.md), as PROCESS.md §3 requires:

| Implementation section (above) | Entry id (below) | Template |
|---|---|---|
| Worked example: Kaggle competition submissions | [`impl-kaggle-submissions`](#impl-kaggle-submissions) | [`tpl-kaggle-submissions`](TEMPLATES.md#tpl-kaggle-submissions) — `examples/kaggle-submissions.json` |
| Surviving the session that launched it / The headless-session rail | [`impl-kaggle-fallback`](#impl-kaggle-fallback) | [`tpl-kaggle-fallback`](TEMPLATES.md#tpl-kaggle-fallback) — `examples/kaggle-with-fallback.json` |
| Worked example → 5. Arm it (a single named watch) | [`impl-kaggle-v15scar`](#impl-kaggle-v15scar) | [`tpl-kaggle-v15scar`](TEMPLATES.md#tpl-kaggle-v15scar) — `examples/kaggle-v15scar-final.json` |
| Recipe: GitHub Actions runs | [`impl-github-actions`](#impl-github-actions) | [`tpl-github-actions`](TEMPLATES.md#tpl-github-actions) — `examples/github-actions.json` |
| Recipe: a generic REST job queue / Auth schemes | [`impl-generic-http`](#impl-generic-http) | [`tpl-generic-http`](TEMPLATES.md#tpl-generic-http) — `examples/generic-http.json` |
| Where n8n fits | [`impl-n8n-always-on`](#impl-n8n-always-on) | [`tpl-n8n-always-on`](TEMPLATES.md#tpl-n8n-always-on) — `n8n/kaggle-submission-poller.json` + its builder |

Sections with no template entry — "Anatomy of a config", "When declarative is
not enough: a Python source", "Choosing rails", "Running it", "Before you arm a
watch" — are explanatory, not application forms. There is no `templates/`
directory in this tool; see the header of `TEMPLATES.md` for what does and does
not count as a template here.

---

### Implementation entries (appended 2026-09-01)

The guide above predates PROCESS.md: its level-2 headings are section titles, not
entry ids, and this file is append-only (§5.2) so they cannot be rewritten. The
six entries below are therefore **appended**, each with a bare-id heading
(`process.yaml` → `definitions.entry`), each naming the guide section it
formalises and citing its reciprocal `TEMPLATES.md` id. This is what makes the §7
Track-B reciprocity check verifiable by grep in both directions.

## impl-kaggle-submissions

**Use case.** Watch a Kaggle competition's submission queue and report each
submission that settles, on file, Slack and Telegram rails.
**Guide section.** "Worked example: Kaggle competition submissions" (above).
**Template.** [`TEMPLATES.md#tpl-kaggle-submissions`](TEMPLATES.md#tpl-kaggle-submissions) — `Tooling/v2.1.0/examples/kaggle-submissions.json`

## impl-kaggle-fallback

**Use case.** The same watch, armed so it outlives the session that started it:
a supervisor probe plus a headless `claude_code` rail that fires only after
`supervisor_lost`.
**Guide sections.** "Surviving the session that launched it" and "The
headless-session rail" (above).
**Template.** [`TEMPLATES.md#tpl-kaggle-fallback`](TEMPLATES.md#tpl-kaggle-fallback) — `Tooling/v2.1.0/examples/kaggle-with-fallback.json`

## impl-kaggle-v15scar

**Use case.** One named single-purpose watch on a final submission slot, seeded
on first run so history is not reported.
**Guide section.** "Worked example: Kaggle competition submissions" → step 5,
"Arm it" (above).
**Template.** [`TEMPLATES.md#tpl-kaggle-v15scar`](TEMPLATES.md#tpl-kaggle-v15scar) — `Tooling/v2.1.0/examples/kaggle-v15scar-final.json`

## impl-github-actions

**Use case.** Watch a repository's GitHub Actions runs declaratively over
`http_json` and report each run that reaches a terminal conclusion.
**Guide section.** "Recipe: GitHub Actions runs" (above).
**Template.** [`TEMPLATES.md#tpl-github-actions`](TEMPLATES.md#tpl-github-actions) — `Tooling/v2.1.0/examples/github-actions.json`

## impl-generic-http

**Use case.** Any REST endpoint that returns a list of rows with a status field —
the minimum viable config, and the auth schemes it supports.
**Guide sections.** "Recipe: a generic REST job queue" and "Auth schemes"
(above).
**Template.** [`TEMPLATES.md#tpl-generic-http`](TEMPLATES.md#tpl-generic-http) — `Tooling/v2.1.0/examples/generic-http.json`

## impl-n8n-always-on

**Use case.** The deliberately less capable always-on tier: the poll loop as an
n8n workflow on a VPS, for watches that must not die with the host that armed
them (KI-22).
**Guide section.** "Where n8n fits" (above).
**Template.** [`TEMPLATES.md#tpl-n8n-always-on`](TEMPLATES.md#tpl-n8n-always-on) — `Tooling/v2.1.0/n8n/` (workflow JSON + its builder)
