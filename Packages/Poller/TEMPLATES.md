# Templates — production application forms

The production-ready forms a new watch is copied from. Every entry here is a
file that actually exists in the repository at `Tooling/v2.1.0/`; nothing below
is aspirational.

**There is no `templates/` directory in this tool.** The templating that exists
is of two kinds, and both are catalogued here:

1. **Config templates** — the shipped example configs under
   `Tooling/v2.1.0/examples/`. A new watch is a copy of one of these with the
   URL, ids and rails changed; the engine itself never changes (KI-16,
   "config, not code"). They are load-tested by
   `tests/test_config.py::test_shipped_examples_all_load`, so a broken template
   fails the suite.
2. **A workflow template** — the always-on n8n tier under
   `Tooling/v2.1.0/n8n/`, emitted by a builder script rather than hand-edited.

There is a third, unrelated sense of "template" inside the tool: the
`"templates"` key *inside* a config, which is report text rendered by
`poller/render.py`. That is a config field, not a file, and is documented in
`IMPLEMENTATIONS.md` ("Report text"). It is not catalogued as a template here.

Each entry cites the `IMPLEMENTATIONS.md` section that uses it, per PROCESS.md §3.

---

<a name="tpl-kaggle-submissions"></a>
## TPL-01 — Kaggle competition submissions

**File.** `Tooling/v2.1.0/examples/kaggle-submissions.json`
**Implementation.** `IMPLEMENTATIONS.md` → "Worked example: Kaggle competition submissions"

Source `kaggle_submissions` against competition
`ai-agent-security-multi-step-tool-attacks`. Three rails: a `file` sink named
`findings`, a `slack` sink, and a `notify_webhook` sink named `telegram`. Carries
the full production dial-set — `interval_seconds`, `jitter_seconds`,
`max_duration_hours`, `stale_after_seconds`, `degraded_after_failures`,
`notify_states`, `state_dir`, and per-reason `templates`.

Copy this one when the watch is a Kaggle submission queue.

---

<a name="tpl-kaggle-fallback"></a>
## TPL-02 — Kaggle submissions with a supervised headless fallback

**File.** `Tooling/v2.1.0/examples/kaggle-with-fallback.json`
**Implementation.** `IMPLEMENTATIONS.md` → "Surviving the session that launched it" / "The headless-session rail"

TPL-01 plus a `supervisor` block and a fourth sink of type `claude_code`, named
`headless-fallback` and gated `"when": "fallback"` — it fires only after
`supervisor_lost`. Copy this one when the watch will outlive the session that
armed it and somebody still has to act on the report (KI-19/KI-20/KI-21).

---

<a name="tpl-kaggle-v15scar"></a>
## TPL-03 — Kaggle final-slot watch (v15scar)

**File.** `Tooling/v2.1.0/examples/kaggle-v15scar-final.json`
**Implementation.** `IMPLEMENTATIONS.md` → "Worked example: Kaggle competition submissions" (arming steps)

A named single-purpose instance of TPL-01 (`"name": "v15scar-final"`) that also
sets `seed_on_first_run`. It is the worked form of "one config per watch, never
a second script": the shape is TPL-01's, only the identity and seeding differ.

---

<a name="tpl-github-actions"></a>
## TPL-04 — GitHub Actions workflow runs

**File.** `Tooling/v2.1.0/examples/github-actions.json`
**Implementation.** `IMPLEMENTATIONS.md` → "Recipe: GitHub Actions runs"

Declarative `http_json` source against
`https://api.github.com/repos/OWNER/REPO/actions/runs`, with `notify_states` and
report `templates` set, reporting to `stdout` and a `file` sink. `OWNER/REPO` is
a placeholder to substitute.

---

<a name="tpl-generic-http"></a>
## TPL-05 — Generic REST job queue

**File.** `Tooling/v2.1.0/examples/generic-http.json`
**Implementation.** `IMPLEMENTATIONS.md` → "Recipe: a generic REST job queue" and "Auth schemes"

The minimum viable shape: `http_json` source against a placeholder
`https://api.example.com/v1/jobs`, `file` and `webhook` sinks, and only
`interval_seconds` / `max_duration_hours` beyond the required keys. Start here
for any API that fits the declarative shape.

---

<a name="tpl-n8n-always-on"></a>
## TPL-06 — Always-on n8n tier (workflow template)

**Files.** `Tooling/v2.1.0/n8n/kaggle-submission-poller.json` (the workflow),
`Tooling/v2.1.0/n8n/build_kaggle_workflow.py` (the builder that emits it),
`Tooling/v2.1.0/n8n/README.md` (the tier's own guide)
**Implementation.** `IMPLEMENTATIONS.md` → "Where n8n fits"

The poll loop as an n8n workflow on an always-on VPS, with dedup state in
`$getWorkflowStaticData('global')`. Deliberately the less capable tier — no
per-sink ledger, no staleness SLA, no fallback rail — because its only job is to
not be absent (KI-22). The builder declares `httpHeaderAuth` and leaves the
credential unset for the owner to attach in the n8n UI, so no secret passes
through the template.

Regenerate rather than hand-edit the JSON: the builder is the template, the JSON
is its output.

---

## Adding a template

A new API that fits the declarative shape is a new config in
`Tooling/v<version>/examples/` and an entry here citing the `IMPLEMENTATIONS.md`
section that explains it — and the reciprocal citation added there. An entry in
one file that does not cite its counterpart is incomplete (PROCESS.md §3).
