# Known issues — how pollers actually break

Every entry below is a failure that happened, not a hypothetical. Each one names
the signature you would see, why it happened, what this package does about it,
and — the important column — **what is still your job**. A guard in code cannot
fix a config that points at the wrong thing.

Read this before writing a new poller config, and add to it when a new failure
class shows up. The IDs are referenced from the source, so `grep -rn KI-07
poller/` finds the code that exists because of an incident.

**On `status: legacy`** (added 2026-09-01). Entries `KI-01` – `KI-22` were
written before PROCESS.md existed. They have no reciprocal `CHANGE_LOG.md` entry and one cannot
be manufactured without inventing a change history that never happened, so they
are grandfathered under PROCESS.md §9: each carries `status: legacy` and is
exempt from the §7 Track-B reciprocity check. Adding that one field is the only
edit made to them — nothing else in those entries has been touched (§5.1).

| ID | Failure | Prevented by | Still your job |
|---|---|---|---|
| [KI-01](#ki-01) | Watch pinned to one hard-coded item; a different item settled unwatched | Collection-wide watching keyed on an immutable id | Pick a `key_field` that is an id, not a description |
| [KI-02](#ki-02) | Watch ended silently; nothing was watching afterwards | Every exit path emits an event | Act on the "poller stopped" message |
| [KI-03](#ki-03) | Two instances of the same watch double-posted | PID lock with liveness check | Use `poller status` instead of relaunching blind |
| [KI-04](#ki-04) | Reported a settle whose result field was still null | `settled_requires` holds the row as pending | Name the result field in `settled_requires` |
| [KI-05](#ki-05) | A dead credential was retried for hours instead of failing | 401/403/404 are fatal; startup preflight | Run `poller check` before a long watch |
| [KI-06](#ki-06) | One rail delivered, the other lost — or duplicated on restart | Per-sink delivery ledger | Give each sink a stable `name` |
| [KI-07](#ki-07) | A truncated state file reset the whole memory of the watch | Atomic writes; corrupt files quarantined | Put the state file on a real disk, not a tmpfs |
| [KI-08](#ki-08) | Only successes were reported; errored rows vanished | `failed` is a first-class reportable state | Map the API's error words in `state.map.failed` |
| [KI-09](#ki-09) | "Is it still running?" was unanswerable | Heartbeat file + `poller status`; no `ps` needed | Watch the heartbeat from cron, not by eye |
| [KI-10](#ki-10) | A report rail needed Node and an absolute path into another repo | Signing reimplemented in the standard library | Keep the package dependency-free |
| [KI-11](#ki-11) | Secrets risk leaking into logs, argv and URLs | Redacting formatter; stdin for commands; query strings stripped | Never put a token in a config file — use `@env:` |
| [KI-12](#ki-12) | Rate limits and N pollers stampeding one API | Backoff with full jitter, `Retry-After`, poll jitter | Set a sane `interval_seconds` |
| [KI-13](#ki-13) | Local-time stamps made cross-host evidence unorderable | Everything is UTC ISO-8601 | Read timestamps as UTC |
| [KI-14](#ki-14) | SIGTERM ignored for minutes; laptop sleep killed the watch | Interruptible sleep; signal handlers | Run long watches on an always-on host |
| [KI-15](#ki-15) | First run spammed every historical item | Seed-and-suppress on first run, logged | Use `--no-seed` deliberately, never by accident |
| [KI-16](#ki-16) | Copies of a poller script drifted from each other | Config, not code | Add a config file, never a second script |
| [KI-17](#ki-17) | Concurrent pollers overwrote each other's scratch files | Per-event templated paths; no fixed temp files | Template `{key}` into file sink paths |
| [KI-18](#ki-18) | A slow item was indistinguishable from a broken poller | Staleness SLA event | Set `stale_after_seconds` to your real SLA |
| [KI-19](#ki-19) | The watch survived its launching session; the attention did not | Supervisor probe + fallback rails | Name a supervisor, or accept nobody is reading |
| [KI-20](#ki-20) | Item text from a third-party API reaching an agent's prompt | Untrusted-data fence + preamble | Keep `allowed_tools` narrow; write the task narrowly |
| [KI-21](#ki-21) | An unattended process spawning agents costs real money | `max_spawns_per_run`, fallback-only by default | Budget it; do not set `when: always` casually |
| [KI-22](#ki-22) | The host went down and took the watch with it | An n8n-resident tier on an always-on VPS | Put deadline-critical watches on that tier |

---

<a name="ki-01"></a>
## KI-01 — The watch was pinned to one hard-coded item

**status.** legacy

**Signature.** A result lands. Nothing fires. You find it by hand later, and the
poller log looks perfectly healthy — it was watching something else.

**What happened.** 2026-08-30: a submission settled at 04:17Z with a real score.
No report chain fired. The armed poller matched on one notebook slug baked into
a copied script; the settle belonged to a different submission, so as far as the
poller was concerned nothing had happened. It was caught by a manual API pull
hours later.

**Cause.** Identity was a *human-typed description substring*, and the watch was
scoped to a single expected item rather than to the collection.

**Prevented by.** A source returns every row of the watched collection, and each
row is identified by an immutable id (`key_field`). The engine reports any item
reaching a terminal state — it has no notion of "the one we care about".
Dedup is `key:state`, so items are independent of each other.

**Still your job.** Choose `key_field` correctly: a submission `ref`, a run `id`,
a job uuid. If you find yourself pointing it at a title, a description or a
filename, stop. If you genuinely want to narrow a watch, use `filter` — that
narrows *which rows are watched*, and still watches all of them.

**Code.** `poller/model.py` (`Item.dedup_key`), `poller/sources/kaggle.py`.
**Test.** `tests/test_engine.py::test_a_different_item_settling_is_also_reported`

---

<a name="ki-02"></a>
## KI-02 — The watch ended and nobody knew

**status.** legacy

**Signature.** Silence that looks exactly like "nothing has happened yet".

**What happened.** The previous poller was one-shot: it watched until its item
settled, wrote a `.done` sentinel, reported, and exited. That is correct
behaviour for one submission and catastrophic as a habit — the next submission
went out with nothing watching it, and the gap was invisible because a healthy
poller and a dead poller produce identical output: none.

**Cause.** Termination was treated as success rather than as an event.

**Prevented by.** Every exit path emits a report: `watch_ended` on a clean stop
(duration reached, signal received), `watch_failed` on a fatal error, and
`degraded` after N consecutive fetch failures. The end-of-watch message names
what is no longer being watched. Crashes are caught and reported before the
process dies.

**Still your job.** Read those messages as instructions. "Poller stopped" means
*arm the next watch*. Better still, set `max_duration_hours: 0` and run one
long-lived watch, or run `--once` from cron so there is no long-lived process to
die in the first place.

**Code.** `poller/engine.py` (`run`, `_emit_lifecycle`).
**Test.** `tests/test_engine.py::test_the_end_of_a_watch_is_always_announced`

---

<a name="ki-03"></a>
## KI-03 — Two instances, every report twice

**status.** legacy

**Signature.** Duplicate Slack posts and duplicate Telegram pings, seconds apart.

**Cause.** Nobody could tell whether the existing watch was alive, so a second
one was launched "to be safe". Both then reported the same settle.

**Prevented by.** A lock file holding the pid and the launching command line.
A second launch refuses with the pid and start time of the incumbent. Liveness
is `os.kill(pid, 0)` plus a `/proc` command-line comparison, so a recycled pid
after a reboot does not block a legitimate launch forever, and a crashed poller's
lock is reclaimed automatically.

**Still your job.** Answer "is it running?" with `poller status`, not by
launching another one. Use `--force` only when you have decided to take over.

**Code.** `poller/lock.py`. **Test.** `tests/test_lock.py`

---

<a name="ki-04"></a>
## KI-04 — Reported a settle that had not produced a result yet

**status.** legacy

**Signature.** A report that says "settled" with an empty score.

**Cause.** Kaggle marks a submission `complete` a moment before `publicScore`
is populated. Any watcher that treats the status word alone as terminal will
occasionally win that race and announce a result that does not exist yet — and
because the item is then in the seen-set, the *real* score is never reported.

**Prevented by.** `state.settled_requires` lists fields that must carry a value
before a row counts as settled. Until they do, the row stays `pending` and is
re-examined on the next tick. Zero counts as a value; empty string, null and
empty containers do not.

**Still your job.** Name the result field for your API — for Kaggle the preset
already sets `["publicScore"]`.

**Code.** `poller/sources/http_json.py` (`classify`, `_blank`).
**Test.** `tests/test_sources.py::test_complete_without_a_score_is_still_pending`

---

<a name="ki-05"></a>
## KI-05 — A dead credential was retried instead of reported

**status.** legacy

**Signature.** Hours of log lines, no reports, and a 401 buried in every one.

**What happened.** Kaggle's legacy Basic `username:key` token silently expired.
Callers that kept using it got 401 on every request. A retry loop treats that
exactly like a network blip, so the poller stayed "up" and reported nothing.
The current auth is `KAGGLE_API_TOKEN` as a **Bearer** header.

**Prevented by.** 401, 403, 404, 400 and 422 raise `HttpFatal` and are never
retried. A fatal source error emits `watch_failed`, names the status, and exits
non-zero. `preflight` performs one real fetch before the loop starts, so bad
credentials fail in seconds rather than after the first interval.

**Still your job.** Run `poller check --config …` before arming a long watch —
it resolves every credential, calls the endpoint, and prints what it would
report on, without sending anything or writing state.

**Code.** `poller/http.py` (`RETRYABLE_STATUS`), `poller/sources/base.py`.
**Test.** `tests/test_http.py::test_auth_failure_is_fatal_and_not_retried`

---

<a name="ki-06"></a>
## KI-06 — One rail fired, the other was lost (or duplicated)

**status.** legacy

**Signature.** The Slack post exists, the Telegram ping never came. Or the
restart re-sent a report that had already gone out.

**Cause.** A single "reported: yes/no" flag per event. Mark-then-send loses a
report when delivery fails; send-then-mark duplicates one when the process dies
between the two, and neither can express "Slack got it, Telegram did not".

**Prevented by.** A delivery ledger per event *per sink*. Each tick drains the
outstanding set: sinks that already have the report are skipped, sinks that
failed are retried, and sinks that failed *fatally* (revoked token, bot not in
channel) are dropped from the retry set instead of consuming the budget. After
`max_delivery_attempts` sweeps the record is marked abandoned and logged loudly.
Because the rendered report is stored in the ledger, a retry works even if the
source no longer returns the row.

**Still your job.** Give every sink a stable `name` in the config — the name is
the ledger key. Renaming a sink makes its past deliveries invisible, and the
next tick will re-deliver recent events to the new name.

**Code.** `poller/state.py` (`Record`), `poller/engine.py` (`_dispatch`).
**Test.** `tests/test_engine.py::test_a_failed_rail_is_retried_and_a_delivered_one_is_not`

---

<a name="ki-07"></a>
## KI-07 — A truncated state file wiped the watch's memory

**status.** legacy

**Signature.** After a container stop, the poller re-reports things it already
reported — or reports nothing because it re-seeded.

**Cause.** State written in place. A stop mid-write leaves half a JSON document,
and the next start reads a parse error as "no state".

**Prevented by.** Writes go to a temp file, are flushed and fsynced, then
`os.replace`d — an atomic rename — and the containing directory is fsynced too.
A reader therefore sees either the old document or the new one. If a state file
*is* unreadable it is copied aside as `.corrupt-<timestamp>` and the run starts
clean **and seeds**, so a corrupt file causes silence about old items rather
than a flood of duplicate reports. A schema-version mismatch is handled the same
way rather than being misread.

**Still your job.** Keep `state_dir` on persistent storage. A state file in a
container's ephemeral layer is a state file you will lose.

**Code.** `poller/state.py` (`write_json_atomic`, `Store._load`).
**Test.** `tests/test_state.py::test_corrupt_state_is_preserved_and_the_store_starts_clean`

---

<a name="ki-08"></a>
## KI-08 — Errored rows were dropped instead of reported

**status.** legacy

**Signature.** A submission fails, a slot is spent, and nothing says so.

**Cause.** Watchers written around "wait for success" treat everything else as
"not yet", and an error state is not a success — so it waits forever.

**Prevented by.** `failed` is a first-class terminal state with its own template,
its own `error` severity, and its own place in `notify_states`. Ambiguous status
words resolve toward `failed` rather than `settled`, because a false alarm is
recoverable and a missed failure is not.

**Still your job.** Populate `state.map.failed` with your API's error vocabulary
(`failure`, `cancelled`, `timed_out`, `aborted`…) and put the error-detail field
in `fields` so the report can say what went wrong.

**Code.** `poller/model.py` (`ItemState`), `poller/sources/http_json.py`
(`_STATE_ORDER`).
**Test.** `tests/test_engine.py::test_failed_items_are_reported_distinctly_from_settled_ones`

---

<a name="ki-09"></a>
## KI-09 — "Is it still running?" had no answer

**status.** legacy

**Signature.** You want to know whether to relaunch. You cannot tell. (In the
/studio container there is no `ps` binary at all, so the usual reflex fails
outright.)

**Prevented by.** A heartbeat file rewritten every tick — pid, run id, tick
count, last error, consecutive failures, source, sinks, state stats — plus
`poller status`, which compares its age against three polling intervals and
prints `ALIVE` / `STALE` / `STOPPED` / `NEVER_RAN`. Exit code 0 means alive, so
a cron watchdog is one line. Liveness probing never shells out.

**Still your job.** Point something at it. `poller status --config … || alert`
in cron turns a silent death into a message.

**Code.** `poller/engine.py` (`_write_heartbeat`), `poller/cli.py` (`cmd_status`).
**Test.** `tests/test_engine.py::test_the_heartbeat_file_makes_liveness_observable_from_outside`

---

<a name="ki-10"></a>
## KI-10 — The report rail depended on another repo's file layout

**status.** legacy

**Signature.** The poller works in the container and nowhere else:
`Cannot find module '/studio/packages/notify/src/client.mjs'`.

**Cause.** The Telegram rail shelled out to Node, which imported the signing
client by absolute path from a different repository. Moving the poller to the
host — the whole point of a long watch — broke it.

**Prevented by.** The signed notify envelope is reimplemented in the Python
standard library (`hmac`, `hashlib`, `json`) and is byte-compatible with the
reference client: same field order, same compact separators, same HMAC over
`"<unix-ms>.<body>"`. A frozen vector generated from the Node implementation is
asserted in the test suite, so drift in either direction fails a test rather
than a delivery. The package as a whole has no third-party dependencies and no
paths into other repos.

**Still your job.** If the upstream envelope ever changes, regenerate the vector
and update it — do not loosen the assertion.

**Code.** `poller/sinks.py` (`NotifyWebhookSink.build_request`).
**Test.** `tests/test_sinks.py::test_envelope_is_byte_identical_to_the_node_client`

---

<a name="ki-11"></a>
## KI-11 — Secrets leaking into logs, argv and URLs

**status.** legacy

**Signature.** A token in a log file, a process list, or a pasted traceback.

**Prevented by.** Every credential read through the env resolver is registered
with a redacting log formatter, which masks it in messages *and* in exception
text. Logged URLs are stripped of their query string, so a key-in-query API does
not leak through a retry warning. The command sink passes reports on **stdin**,
never in argv. Config files carry `@env:NAME` references, not values.

**Still your job.** Put values in the env file, names in the config. Never
`echo` a token to check it — `poller check` tells you whether it works without
printing it.

**Code.** `poller/log.py`, `poller/envfile.py`, `poller/http.py` (`_safe_url`).

---

<a name="ki-12"></a>
## KI-12 — Rate limits, and N pollers stampeding one API

**status.** legacy

**Signature.** HTTP 429, or several pollers hitting the same endpoint on the
same second because they were all started by the same script.

**Prevented by.** Retries use exponential backoff with **full jitter**, floored
by any `Retry-After` the server sends and capped by `backoff_cap`. The poll
interval itself takes optional `jitter_seconds`, so parallel watches drift apart
instead of synchronising.

**Still your job.** Choose an interval that respects the API. Polling a
submission list every 5 seconds does not make results arrive sooner.

**Code.** `poller/http.py` (`_backoff`), `poller/engine.py` (`_next_delay`).

---

<a name="ki-13"></a>
## KI-13 — Local time in the evidence trail

**status.** legacy

**Signature.** Two hosts' logs cannot be interleaved; an SLA calculation is off
by the timezone offset.

**Prevented by.** Every timestamp written — log lines, state, heartbeat, report
headers — is UTC ISO-8601. Parsing accepts `Z`, explicit offsets, fractional
seconds and naive strings (assumed UTC), so an API's format quirks cannot make
staleness arithmetic silently wrong.

**Code.** `poller/clock.py`, `poller/log.py`.

---

<a name="ki-14"></a>
## KI-14 — Sleeping through the stop signal

**status.** legacy

**Signature.** `kill` appears to do nothing for three minutes. Or a watch dies
when a laptop sleeps.

**Prevented by.** The inter-tick wait is `threading.Event.wait`, not
`time.sleep`, so SIGTERM/SIGINT wake it immediately, finish the tick, emit
`watch_ended`, and exit cleanly.

**Still your job.** Run long watches somewhere that stays awake — a VPS, or the
container on an always-on host — or use `--once` from a scheduler so there is no
long-lived process at all. `nohup … &` on a laptop is not a survivable watch.

**Code.** `poller/clock.py` (`sleep`), `poller/engine.py`
(`_install_signal_handlers`).

---

<a name="ki-15"></a>
## KI-15 — The first run reported the entire history

**status.** legacy

**Signature.** Fifty Slack posts about submissions from three weeks ago.

**Prevented by.** On a first run (no state file) the poller seeds: it records
everything currently visible as already-seen and suppresses it, then logs how
many items it seeded and how many terminal ones it suppressed. The seed
timestamp is stored, so "did this poller ever seed?" is answerable later.

**Still your job.** Know which mode you want. `--no-seed` reports everything
already terminal, which is right when you are back-filling deliberately and
wrong every other time.

**Code.** `poller/engine.py` (`_seed`).
**Test.** `tests/test_engine.py::test_seeding_suppresses_history_and_records_the_count`

---

<a name="ki-16"></a>
## KI-16 — Copies of the script drifted

**status.** legacy

**Signature.** Three near-identical `*_poller.sh` files, each with slightly
different logic, and no way to tell which one is current.

**Cause.** The previous template was explicitly copy-and-edit: two blocks marked
`### EDIT PER SUBMISSION ###` had to be hand-edited per run. Every fix therefore
had to be applied N times and never was.

**Prevented by.** The engine is a package; a watch is a JSON config. Nothing
about a particular API, item or report text lives in code. Unknown config keys
are warned about, so a typo'd key does not silently keep a default.

**Still your job.** When a config cannot express what you need, add a capability
to the package (or a `python` source) — do not fork the engine.

**Code.** `poller/config.py`.

---

<a name="ki-17"></a>
## KI-17 — Concurrent pollers overwrote each other's files

**status.** legacy

**Signature.** A report containing another watch's content.

**Cause.** The previous template composed its payloads through fixed paths
(`/tmp/poll_slack.txt`). Two pollers running at once clobbered each other.

**Prevented by.** Reports are composed in memory. The file sink's path is a
template, so `{key}` gives every event its own file, and state, lock and
heartbeat paths are all derived from the poller's unique `name`.

**Still your job.** Give each poller a distinct `name`, and template `{key}`
into the file sink path when you want one file per event.

**Code.** `poller/sinks.py` (`FileSink`), `poller/config.py`.

---

<a name="ki-18"></a>
## KI-18 — A slow item looks exactly like a broken poller

**status.** legacy

**Signature.** Six hours of nothing. Is the API slow, or is the watch dead?

**What happened.** A submission sat `pending` for over six hours — genuinely
unusual, genuinely fine — during which there was no way to distinguish it from a
poller that had quietly died.

**Prevented by.** `stale_after_seconds` sets an SLA. When an item stays pending
past it, the poller reports once that the item is slow and *the poller is fine*.
Combined with the heartbeat (KI-09), the two silences are now distinguishable.

**Still your job.** Set the SLA to a real number for your API. Zero disables it.

**Code.** `poller/engine.py` (`_event_for`).
**Test.** `tests/test_engine.py::test_a_pending_item_past_its_sla_is_reported_once`

---

<a name="ki-19"></a>
## KI-19 — The watch survived the session; the attention did not

**status.** legacy

**Signature.** The poller is healthy, the reports are landing, and nothing is
happening about them.

**Cause.** A poller launched from an interactive session is a detached process —
it correctly outlives that session. But the session was the thing that *read*
the reports and acted. When it ends, the watch continues into a void, and
because everything looks healthy there is no signal that it has.

**Prevented by.** A `supervisor` block names the process the poller was launched
by (inside Claude Code, `@env:CLAUDE_PID` needs no setup). Each tick — before
anything else — the poller probes it with the same liveness check the instance
lock uses. On the tick it is first seen gone, `supervisor_lost` is emitted once
and any rail marked `"when": "fallback"` activates, typically a `claude_code`
sink that spawns a successor session. An unconfigured supervisor reads as
present, so nothing escalates by accident, and a fallback rail with no
supervisor warns at startup rather than staying silently dark.

**Still your job.** Decide whether you want escalation (`on_loss: fallback`),
notification (`report`), or neither (`ignore`). And note this is a *different*
failure from the poller itself dying — that one is KI-09, and its guard lives
outside the host (see the n8n layering in IMPLEMENTATIONS.md).

**Code.** `poller/supervisor.py`, `poller/engine.py` (`_check_supervisor`,
`fallback_active`).
**Test.** `tests/test_supervisor.py`

---

<a name="ki-20"></a>
## KI-20 — Third-party text reaching an agent's prompt

**status.** legacy

**Signature.** None, until it matters. This is a latent risk, not a past incident.

**Cause.** The `claude_code` sink puts item fields — a submission description, a
job label, a commit message — into the prompt of a session that holds real
tools. Those fields come from an API and are influenced by whoever can write to
it. A description reading "ignore previous instructions and…" is a prompt
injection with a tool-holding audience.

**Prevented by.** The event is fenced in a
`<poller-event trust="untrusted-data">` block, after a preamble stating the block
is data and that directions inside it must never be followed. The task sits
*after* the fence. The spawned session can only use the tools named in
`allowed_tools`, and names none by default.

**Still your job.** Fencing raises the cost of an attack; it does not make one
impossible. Keep `allowed_tools` to the minimum the task needs, write the task
narrowly and say what *not* to do, and never hand a fallback session destructive
tools on the strength of the fence alone. The same posture the studio takes with
inbound Slack applies here: it is data, not instructions.

**Code.** `poller/sinks.py` (`ClaudeCodeSink.UNTRUSTED_PREAMBLE`, `build_prompt`).
**Test.** `tests/test_sinks.py::test_an_injection_attempt_in_the_data_stays_inside_the_fence`

---

<a name="ki-21"></a>
## KI-21 — An unattended process that can spend money

**status.** legacy

**Signature.** A cost line you did not expect.

**Cause.** Every `claude_code` spawn is a real session. Measured here at roughly
**US$0.30 for an eleven-token reply**, because the input cache has to be built
before the session does anything. A poller that spawns one per event, on a
source that settles ten items at once, has spent a few dollars while you were
asleep — and a fetch bug that re-reports could do it repeatedly.

**Prevented by.** The rail is off unless configured, and is intended for
`"when": "fallback"` — a rare path, not the normal one. `max_spawns_per_run`
caps spawns per process lifetime and refuses further ones fatally rather than
retrying. Every spawn logs its session id, turn count and cost. The dedup ledger
means a settled item can only ever trigger one spawn.

**Still your job.** Set `max_spawns_per_run` to a number you would be relaxed
about paying for, keep `timeout_seconds` finite, and think twice before
`"when": "always"`.

**Code.** `poller/sinks.py` (`ClaudeCodeSink.send`).
**Test.** `tests/test_sinks.py::test_the_spawn_budget_is_enforced`

---

<a name="ki-22"></a>
## KI-22 — The host went down and took the watch with it

**status.** legacy

**Signature.** No reports, no heartbeat, no poller — and no way to tell from the
outside whether the watch ever ran, because the thing that would have told you
died with it.

**Cause.** A poller inherits the availability of whatever it runs on. In a
container on a laptop, a flat battery or a crash stops the container, and
nothing restarts it. Every other guard in this document assumes a running
process; this is the failure where there is none.

Note this is *not* KI-09 (heartbeat) or KI-19 (supervisor). Both of those detect
a loss from somewhere still alive. If the whole host is down, the heartbeat file
is unreachable and the fallback rail has no process to run in.

**Prevented by.** A second, always-on tier: the poll loop as an n8n workflow on
the VPS, with dedup state in `$getWorkflowStaticData('global')`. It is
deliberately less capable than the Python engine — no per-sink ledger, no
staleness SLA, no fallback rail — because its only job is to not be absent. See
[`n8n/README.md`](n8n/README.md).

**Still your job.** Decide which watches are deadline-critical enough to put on
that tier, and keep the two classifications in parity — two implementations of
"what counts as settled" can drift, and a drift means the tiers disagree.

**Code.** `n8n/kaggle-submission-poller.json`, `n8n/build_kaggle_workflow.py`.

---

### Adding an entry

New failure? Append it here in the same shape — signature first, so a future
session can grep for the symptom — and reference the ID from the code that
guards it. An entry with no code reference is a warning; an entry with one is a
guard.

---

# Process issues (PROCESS.md ids)

Entries below use the `<description>_<hash8>` id scheme defined in
`process.yaml` → `definitions.issue-id`, not the `KI-` scheme above. The `KI-`
ids annotate code guards (`grep -rn KI-07 poller/`); a process issue has no code
guard, so it gets no `KI-` number and the summary table above is left untouched.
This file is append-only (PROCESS.md §5.1).

---

## packages-poller-failed-track-b-conforman_8f776048

| Field | Value |
|---|---|
| **id** | `packages-poller-failed-track-b-conforman_8f776048` |
| **summary** | Packages/Poller failed Track B conformance: TEMPLATES.md and CHANGE_LOG.md missing, code not under Tooling/, no results under Tests/, README states no version |
| **iteration** | Conformance-only migration of the existing v2.1.0 code: relocate, verify, and document. Full statement below under **Iteration (Z)** |
| **status** | in-progress |
| **resolved_by** | [`CHANGE_LOG.md#conformance-only-migration-of-the-existi_18d24e7c`](CHANGE_LOG.md#conformance-only-migration-of-the-existi_18d24e7c), fix-version `v2.1.0` |
| **branch** | `smoke/fix-packages-poller` |
| **occurrences** | 1 — detected 2026-08-31 during the Track B sweep recorded in PROCESS.md §9 |

**Id derivation.** `hash8` = first 8 hex chars of
`sha256("packages/poller failed track b conformance: templates.md and change_log.md missing, code not under tooling/, no results under tests/, readme states no version")`
(the summary, trimmed, lowercased, whitespace collapsed) = `8f776048`.
`description` = that same summary slugified and truncated to 40 characters.

**Outcome (X).** The tool could not release a new version: PROCESS.md §7 Track B
says a failing tool is blocked until the failure is logged and fixed. Concretely,
as measured on 2026-08-31 at the tool root:

- `TEMPLATES.md` — **missing**. The application forms existed as files
  (`examples/*.json`, `n8n/`) but were catalogued nowhere, so `IMPLEMENTATIONS.md`
  had no counterpart to cite and the §3 reciprocity check failed in both
  directions.
- `CHANGE_LOG.md` — **missing**. Twenty-two `KI-` entries described fixes with no
  reciprocal iteration record, so no issue in this file could cite the change
  that closed it.
- `README.md`, `IMPLEMENTATIONS.md`, `KNOWN_ISSUES.md` — present and non-empty.
- **Code layout — failed.** `poller/`, `bin/`, `tests/`, `examples/`, `n8n/` and
  `run-tests.sh` sat at the tool root, not under `Tooling/v<version>/`. There was
  therefore no immutable released-version directory, i.e. no in-repo rollback
  point (PROCESS.md §5, safeguard 1).
- **Test layout — failed.** No `Tests/` directory existed. The suite ran green
  (187 tests) but nothing recorded that it had, so from the repository alone the
  tool's test state was unknowable.
- **Version agreement — failed.** `README.md` states no version anywhere. The
  code declares `__version__ = "2.1.0"` (`poller/__init__.py`) and the merged PR
  title `feat/poller-n8n-tier` puts the current version at `v2.1.0`, so three
  places that must name one version named it in two and omitted it in the one a
  reader looks at first.

**Cause (Y).** The tool predates PROCESS.md. It was authored in the flat
`<Tool>/{code,tests,docs}` shape that the whole repository used before the
`Tooling/`/`Tests/` convention existed, and version identity was carried in
Python source and in PR titles — the two places the convention does not read —
rather than in the documents. Nothing in the old shape was wrong when written;
it simply was never migrated. PROCESS.md §9 records this as a known backlog for
all eleven tools, and Poller's row (`TEMPLATES ❌ CHANGE_LOG ❌ Tooling ❌
Tests ❌`) matches what was found exactly.

**Iteration (Z).** Bring the tool into conformance on its current version
without touching its behaviour: move the implementation tree to
`Tooling/v2.1.0/` (test *code* moving with it, per §4), repair anything the move
broke, run the suite from the new location and record the real output under
`Tests/v2.1.0/`, create the two missing canonical documents, and state `v2.1.0`
in the README. No version bump — the code moved, it did not change. Planned and
recorded in
[`CHANGE_LOG.md#conformance-only-migration-of-the-existi_18d24e7c`](CHANGE_LOG.md#conformance-only-migration-of-the-existi_18d24e7c).

**Still your job.** The status above reads `in-progress` deliberately. The entry
was appended in the same turn as the iteration (§5.7); the iteration is executed
and committed on branch `smoke/fix-packages-poller`, but no PR exists and nothing
is merged, so `merge_commit` is empty and `resolved` may not be written
(`process.yaml` → `definitions.issue-status.note`). Whoever merges it appends the
closing entry citing `v2.1.0` and the merge commit — this entry is never
overwritten.

*Correction, 2026-09-01.* Two fields of this entry were wrong when written and
have been corrected on this branch, before any merge or release. `status` read
`open — iteration executed on this branch; …`, which is neither a member of the
closed set of seven statuses (`process.yaml` →
`definitions.issue-status`) nor accurate — an executed, unmerged iteration is
`in-progress`. `resolved_by` cited the change-id
`migrated-packages-poller-code-to-tooling_39621062`, which was derived from a
`summary` field rather than from `iteration`; the change entry's id was
recomputed as `conformance-only-migration-of-the-existi_18d24e7c` and the
citation follows it. The `id` and `summary` fields — the immutable, identity-
bearing ones — are unchanged, so the issue-id itself did not move.

---

### Path note (appended 2026-08-31, v2.1.0 migration)

Every code path referenced above — `poller/…`, `tests/…`, `n8n/…` — now lives
under `Tooling/v2.1.0/`. So `grep -rn KI-07 poller/` reads
`grep -rn KI-07 Tooling/v2.1.0/poller/`, and the KI-22 link to `n8n/README.md`
resolves at `Tooling/v2.1.0/n8n/README.md`. The entries themselves are left
exactly as written: this file is append-only, and rewriting twenty-two recorded
incidents to fix link targets would edit history to fix a path.

---

## packages-poller-failed-the-track-b-recip_d4d59cb2

| Field | Value |
|---|---|
| **id** | `packages-poller-failed-the-track-b-recip_d4d59cb2` |
| **summary** | Packages/Poller failed the Track B reciprocity check: fourteen level-2 headings across its entry documents are neither bare ids nor marked legacy |
| **iteration** | Mark the nine pre-conformance implementation sections legacy under PROCESS.md §9 and demote the five prose sections to level 3 under decision 18 |
| **status** | in-progress |
| **resolved_by** | [`CHANGE_LOG.md#mark-the-nine-pre-conformance-implementa_42ed561b`](CHANGE_LOG.md#mark-the-nine-pre-conformance-implementa_42ed561b), fix-version `v2.1.0` |
| **branch** | `fix/legacy-poller` |
| **occurrences** | 1 — detected 2026-09-01 by `python3 bin/trackb-check.py Packages/Poller` |

**Id derivation.** `hash8` = first 8 hex chars of `sha256` over the canonicalised
`summary` field (`process.yaml` → `definitions.issue-id.hash8`, canonical steps
1–5 including the decision-19 markup strip):

```
packages/poller failed the track b reciprocity check: fourteen level-2 headings across its entry documents are neither bare ids nor marked legacy
```

= `d4d59cb2`. `description` = that same summary slugified and truncated to 40
characters.

**Outcome (X).** `python3 bin/trackb-check.py Packages/Poller` reported
**FAIL Reciprocity** with 28 problems, from 14 level-2 headings that are neither
bare ids (§10.13) nor marked `legacy` (§9) — each therefore counted twice, once
for heading form and once as a counterpart-less entry:

- `IMPLEMENTATIONS.md` — nine guide sections: "Anatomy of a config", "Worked
  example: Kaggle competition submissions", "Recipe: GitHub Actions runs",
  "Recipe: a generic REST job queue", "When declarative is not enough: a Python
  source", "Choosing rails", "Surviving the session that launched it", "Running
  it", "Before you arm a watch".
- `IMPLEMENTATIONS.md` — two 2026 section headings: "Template index (appended
  2026-08-31, v2.1.0 migration)" and "Implementation entries (appended
  2026-09-01)".
- `KNOWN_ISSUES.md` — "Adding an entry" and "Path note (appended 2026-08-31,
  v2.1.0 migration)".
- `TEMPLATES.md` — "Adding a template".

**Cause (Y).** Two distinct causes, which is why one remedy does not cover all
fourteen:

1. The nine `IMPLEMENTATIONS.md` guide sections predate PROCESS.md. They are
   pre-conformance entries of the kind §9 grandfathers, but decision 17 — which
   extended the grandfather from `KNOWN_ISSUES.md` to all four entry documents —
   was settled after the v2.1.0 migration was written, so no `status` field was
   ever added to them. The change entry
   [`CHANGE_LOG.md#conformance-only-migration-of-the-existi_18d24e7c`](CHANGE_LOG.md#conformance-only-migration-of-the-existi_18d24e7c)
   states under "Honest limits" that these sections stay uncited because
   invariant 2 forbids rewriting them; correct as far as it goes, but adding
   `status: legacy` is the one edit §9 permits and it was not taken.
2. The other five are prose sections, not entries. Decision 18 puts prose
   sections at level 3 or lower; all five were written at level 2, where any
   heading IS an entry (`process.yaml` → `definitions.entry.not_an_entry`).

**Iteration (Z).** Documents only, no behavioural change and no version bump —
add `status: legacy` to the nine pre-conformance sections in the form
`Packages/Scrape` already uses, and demote the five prose sections from level 2
to level 3. Planned and recorded in
[`CHANGE_LOG.md#mark-the-nine-pre-conformance-implementa_42ed561b`](CHANGE_LOG.md#mark-the-nine-pre-conformance-implementa_42ed561b).

**Why this is a new entry rather than an edit.** Decision 22, settled 2026-09-01:
a correction to an unmerged entry is **appended** as a new issue↔change pair,
never written into the existing entry as a dated note. The
`…_18d24e7c` change entry above is left exactly as written, including the
"Honest limits" paragraph this entry corrects.

**Still your job.** `status` reads `in-progress`: the iteration is executed and
committed on `fix/legacy-poller`, but no PR exists and nothing is merged, so
`merge_commit` is empty and `resolved` may not be written (`process.yaml` →
`definitions.issue-status.note`). Whoever merges appends the closing entry.
