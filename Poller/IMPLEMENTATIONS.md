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
cd Poller

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

| Sink | Use it for | Notes |
|---|---|---|
| `file` | The audit trail. Always include one. | Works with no network. Template `{key}` into the path for one file per event |
| `slack` | Team-visible reports | Needs `chat:write` and the bot invited to the channel; `not_in_channel` is fatal, not retried |
| `notify_webhook` | Telegram via the signed n8n seam | Byte-compatible with `packages/notify`; needs `NOTIFY_WEBHOOK_URL` + `NOTIFY_TOKEN` |
| `webhook` | Discord, Teams, an internal collector | `field` names the JSON key the text goes in |
| `command` | Anything with an existing CLI | Message arrives on **stdin**, never argv |
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

## Running it

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
