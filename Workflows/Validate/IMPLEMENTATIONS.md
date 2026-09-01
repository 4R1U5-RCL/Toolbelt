# IMPLEMENTATIONS — Workflows/Validate

How this tool is actually used. Every entry cites its form in
[`TEMPLATES.md`](TEMPLATES.md) (PROCESS.md §3 reciprocity).

**Append-only** (PROCESS.md §5.2). A new use case is appended; an existing entry is never
replaced.

Each entry below is derived from artifacts that exist in this directory —
[`README.md`](README.md), the `bin/validate` docstring and argument parser, and
`Tooling/v1.0.0/config/panel.json`. No use case is recorded here that the repo does not
demonstrate.

Common to all: `OPENROUTER_API_KEY` must be in the environment. Output defaults to
`~/.claude/data/validate/` when that directory exists, otherwise the current working directory,
as `validate_<topic>_<UTC>.md`; override with `--out <file|dir>`.

---

## `i-inline-content` — stress-test a short plan passed inline

The quickest form: the content to validate is a command-line argument. Suited to a paragraph or
a short decision statement rather than a long document.

The panel (GPT-5, Gemini 2.5 Pro, Grok 4.6 with a DeepSeek R1 fallback) reviews the content
independently and in parallel; each returns STRENGTHS / RISKS / ALTERNATIVES plus a STANCE, and
the confidence label is computed in code from those stances. The label reports **inter-model
agreement, not correctness**.

Template: [`TEMPLATES.md#t-inline-content`](TEMPLATES.md#t-inline-content)

---

## `i-file-input` — stress-test a document on disk

The primary use case per `README.md`: point the tool at a plan, analysis, proposal or decision
document with `--input <file>` and give a one-line `--subject`. `--topic <slug>` overrides the
slug used in the output filename.

Template: [`TEMPLATES.md#t-file-input`](TEMPLATES.md#t-file-input)

---

## `i-stdin-pipe` — stress-test piped content

`--input -` reads the content from stdin, so the tool composes with any generator of text
(`cat`, a heredoc, another command's output) without a temporary file.

Template: [`TEMPLATES.md#t-stdin-pipe`](TEMPLATES.md#t-stdin-pipe)

---

## `i-web-factcheck` — add an external fact-check pass

`--web` adds Perplexity Sonar as a separate role that fact-checks the content against the public
web. Per the honesty invariants in `README.md` it is opt-in, it does **not** vote, and it cannot
change the confidence label. Use it when the content makes external factual claims; leave it off
when the run must stay off the public internet.

Template: [`TEMPLATES.md#t-web-factcheck`](TEMPLATES.md#t-web-factcheck)

---

## `i-panel-subset` — run fewer models

`--panel <keys>` restricts the run to named reasoner keys — for a cheaper or faster pass, or to
route around a model whose provider is unavailable. Note the honesty floor: with fewer than two
reasoners responding the confidence is `unknown`.

Template: [`TEMPLATES.md#t-panel-subset`](TEMPLATES.md#t-panel-subset)

---

## `i-panel-config` — repoint the panel at different models

The panel is configuration, not code. Editing `config/panel.json` (or passing `--config`) swaps
models, labels, per-slot fallbacks and the `max_tokens`/`timeout` defaults without touching
`lib/validate_core.py`. `README.md` records the two live constraints on this: the OpenRouter
account's provider allowlist decides which model IDs resolve at all, and using a Claude model as
a reasoner weakens the cross-check because this tool usually validates Claude-authored work.

Template: [`TEMPLATES.md#t-panel-config`](TEMPLATES.md#t-panel-config)

---

## `i-offline-selftest` — verify the orchestration without network or secrets

`tests/selftest.py` injects a fake `call_model` and exercises the scoring, fallback and honesty
logic end to end — consensus→HIGH, dissent→LOW, failed model→`FAILED`, single responder→
`unknown`, unparseable stance→non-responding, fenced stance ignored, web-tier gating. It proves
the deterministic layer; it cannot test the models' non-deterministic answers. Run it after any
change to the tool, and before releasing a version.

Template: [`TEMPLATES.md#t-offline-selftest`](TEMPLATES.md#t-offline-selftest)
