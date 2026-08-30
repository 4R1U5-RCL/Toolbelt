# The always-on tier — running the poll loop on n8n

## Why this exists

The Python engine runs wherever you start it. Started in a container on a
laptop, it inherits that laptop's availability: **if the host goes flat or
crashes, the container stops and the watch is simply gone.** Nothing restarts
it, and the heartbeat that would have proved it alive stops with everything
else. A dead-man's-switch elsewhere can *tell* you the watch died; it cannot
bring it back.

So for a watch that must not lapse — a competition deadline, an overnight
migration, anything where "we found out on Monday" is the failure — the clock
belongs on hardware you are not carrying around. Here that is the Hetzner VPS,
and the always-on process already on it is n8n.

This is a real correction to an earlier version of this guide, which argued the
poll loop should not live on n8n because the engine needs a durable ledger. That
reasoning was about *state*, and it missed the binding constraint, which is
*availability*. n8n solves state adequately (see below) and solves availability
completely.

## The two tiers

| | Local engine (`poller run`) | n8n workflow (this directory) |
|---|---|---|
| Availability | Dies with its host | Survives any client machine going down |
| State | JSON ledger, per-sink delivery tracking | `$getWorkflowStaticData('global')`, persisted in the workflow record |
| Retry of a failed rail | Per-sink, across restarts | n8n's own execution retry |
| Staleness SLA, degraded alarms, lifecycle events | Yes | No |
| Headless-session fallback | Yes | No |
| Cost of a change | Edit a JSON config | Edit a workflow |

Use the n8n tier when the watch must not lapse. Use the local engine when you
want the richer behaviour, or for anything short-lived and supervised. Running
both against the same source is fine and is not double-reporting insurance —
they keep independent dedup state, so both will report, which for a deadline
watch is usually what you want.

## What the workflow does

`kaggle-submission-poller.json`, deployed to `n8n.arius.au`:

```
Schedule (*/3 * * * *)
   └─▶ HTTP GET  competitions/submissions/list/<slug>     (httpHeaderAuth: Kaggle bearer)
         └─▶ Code  classify + dedup against static data
               ├─▶ Telegram   ([STUDIO] Telegram Bot credential, already present)
               └─▶ HTTP POST  slack chat.postMessage      (httpHeaderAuth: Slack bearer)
```

The Code node deliberately mirrors `poller/sources/kaggle.py` and
`poller/engine.py`:

* status is matched case-insensitively as a substring, **failed before settled**,
  so an ambiguous word errs toward the louder outcome;
* `complete` with a null `publicScore` is held as **pending** — reporting it
  would announce a settle with no score *and* burn the dedup key (KI-04);
* identity is the immutable `ref`, never the description (KI-01);
* dedup is `ref:state`, so pending→settled reports exactly once (KI-06);
* the first production run **seeds** — it records what already exists and
  reports nothing (KI-15);
* the seen-set is pruned to the most recent 500 keys.

### Parity is a maintenance obligation

Two implementations of the same classification can drift, and a drift means the
two tiers disagree about what a settle is. If you change the state mapping in
one, change it in the other. `build_kaggle_workflow.py` regenerates the JSON,
and the classification block is the part to keep in sync.

**Known gap:** the workflow is not yet *generated* from a poller config — it is
a hand-maintained sibling of one. Emitting it from the same JSON (`poller
emit-n8n`) is the right fix and is not built.

## Deploying it

```bash
# regenerate the workflow JSON from the builder
python3 n8n/build_kaggle_workflow.py > n8n/kaggle-submission-poller.json

# deploy (inactive)
curl -s -X POST -H "X-N8N-API-KEY: $N8N_API_KEY" -H "Content-Type: application/json" \
     --data-binary @n8n/kaggle-submission-poller.json \
     "$N8N_BASE_URL/api/v1/workflows"
```

### The two credentials it needs — owner action

The workflow ships with its HTTP nodes set to `httpHeaderAuth` and **no
credential attached**, deliberately: the secrets are entered by their owner in
the n8n UI rather than transiting a script. Create both as **Header Auth**
credentials:

| Node | Credential name | Header | Value |
|---|---|---|---|
| Fetch Submissions | `[STUDIO] Kaggle API bearer` | `Authorization` | `Bearer <KAGGLE_API_TOKEN>` |
| Slack | `[STUDIO] Slack bot bearer` | `Authorization` | `Bearer <SLACK_BOT_TOKEN>` |

Both values are already in `/studio/.env` under those names. The Telegram node
reuses the existing `[STUDIO] Telegram Bot` credential and needs nothing.

### Then

1. Open the workflow, attach the two credentials.
2. **Execute once manually** and confirm the Code node returns 0 items — a
   manual run does not persist static data, so this proves the fetch and the
   classification without seeding or posting.
3. **Activate.** The first scheduled run seeds silently; every new settle or
   error after that is reported once.
4. Confirm it is alive later: the workflow's execution list on n8n, or
   `GET /api/v1/executions?limit=5`.

## Where the channel and chat id come from

`$env.SLACK_ARIUS_CHANNEL_ID` (falling back to the literal `C0BRE9369KL`) and
`$env.TELEGRAM_DEFAULT_CHAT` — the same pattern `[OPERORCH] Runner Watcher`
uses. Set them in the n8n environment to override.

## The full layering

Outermost first, each layer noticing the failure of the one inside it:

```
n8n schedule (VPS, always on)  ──▶ the watch itself, immune to your laptop
   └── local poller process    ──▶ richer engine: SLA, degraded alarms, ledger
         └── headless fallback ──▶ agency when the launching session ends
```

The n8n tier is the one that survives everything else going dark. It is also the
least capable, which is the right trade for a layer whose only job is to not be
absent.
