# Validate — OpenRouter cross-model validation

Stress-test a plan, analysis, proposal, or decision across **multiple independent frontier models
in parallel**, and get back a confidence label derived from how much they **agree** — plus each
model's full critique and the points where they disagree. One OpenRouter key reaches every model;
the package is pure-stdlib Python, so it installs anywhere with no dependencies.

This is the portable, OpenRouter-backed, parallel-panel evolution of the studio's `consult`/`validate`
methodology. See **`Tooling/v1.0.0/docs/topology.html`** for the flow.

**Current version: `v1.0.0`.** The code lives in [`Tooling/v1.0.0/`](Tooling/v1.0.0/); recorded test
results for it are in [`Tests/v1.0.0/`](Tests/v1.0.0/). Use cases are in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md), their application forms in
[`TEMPLATES.md`](TEMPLATES.md), and issues/iterations in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) and
[`CHANGE_LOG.md`](CHANGE_LOG.md).

## Panel & flow

```
input (the output to stress-test)
 ├─ openai/gpt-5           ┐
 ├─ google/gemini-2.5-pro  ├─ independent, parallel — each returns STRENGTHS / RISKS / ALTERNATIVES + a STANCE
 ├─ x-ai/grok-4.6          ┘   (→ deepseek/deepseek-r1 automatically if Grok fails)
 → synthesize: consensus vs disagreements   (confidence computed in code from stances)
 → [--web, opt-in] perplexity/sonar web fact-check   (a separate role — it does not vote)
 → write a structured validation doc
```

The reasoners are deliberately **non-Claude**: this tool usually validates Claude-authored work, and
a Claude reviewer would share the author's blind spots (the whole point of *cross*-model validation).

## Install & use

All commands below are relative to `Tooling/v1.0.0/`.

```sh
cd Tooling/v1.0.0
# needs OPENROUTER_API_KEY in the environment
set -a; . /studio/.env; set +a          # or: export OPENROUTER_API_KEY=...

bin/validate "the plan text..."                    # content as an argument
bin/validate --input plan.md --subject "one-line"  # from a file
cat plan.md | bin/validate --input -               # from stdin
bin/validate --input plan.md --web                 # + Perplexity web fact-check (external hop)
bin/validate --input plan.md --panel gpt5,grok     # a subset of the panel
```

Options: `--topic <slug>` · `--out <file|dir>` · `--max-tokens N` · `--timeout S` ·
`--config <panel.json>` · `--print`. Output defaults to `~/.claude/data/validate/` when it exists,
else the current directory: `validate_<topic>_<UTC>.md`.

## Honesty invariants (enforced in code, not just documented)

- **Confidence = inter-model AGREEMENT, not correctness.** A `HIGH` means the panel concurred — it
  does **not** mean the answer is true. The caveat is printed in every doc.
- **Never a single-model verdict.** Fewer than two reasoners responding ⇒ confidence `unknown`.
- **An unparseable/missing STANCE is non-responding, not a default.** The strict parser (anchored,
  code-fence-aware) returns *no stance* rather than silently assuming "concerns", so a garbled review
  can't inflate the panel. The reviewer prompt also treats the reviewed content as **untrusted**
  (ignores any instructions embedded in it).
- **The web tier is opt-in and separate.** Perplexity only runs with `--web`, and it fact-checks —
  it does not cast a stance vote.
- **A model that errors is recorded `FAILED`,** never silently dropped or faked. Confidence is
  computed only from the models that actually answered.

## Configuration

`Tooling/v1.0.0/config/panel.json` defines the panel — swap models without touching code. A reasoner may declare a
`fallback` used automatically when its primary errors:

```json
{ "reasoners": [
    {"key":"gpt5",  "model":"openai/gpt-5"},
    {"key":"gemini","model":"google/gemini-2.5-pro"},
    {"key":"grok",  "model":"x-ai/grok-4.6",
      "fallback": {"model":"deepseek/deepseek-r1", "label":"DeepSeek R1 (DeepSeek)"}}
  ],
  "web": {"key":"perplexity","model":"perplexity/sonar"},
  "defaults": {"max_tokens":6000,"timeout":220} }
```

## Known issues / caveats

1. **Provider allowlist gates which models resolve — an OpenRouter *account* setting.** A model ID
   like `x-ai/grok-4.6` or `deepseek/deepseek-r1` only works if the account behind
   `OPENROUTER_API_KEY` permits the provider that actually *serves* it (Grok → `xai`, DeepSeek-R1 →
   `novita`) in its dashboard allowlist (Settings → Privacy/Providers). When a provider isn't
   allowed, the call returns `HTTP 404 "No allowed providers are available"` and the model shows
   `FAILED` in the doc — the run still completes with the models that did resolve. On a **fresh
   install with a different key**, enable the providers you need first. On this repo's account,
   `xai` and `novita` are enabled, so both Grok and DeepSeek resolve.
2. **The 4th reasoner is Grok 4.6, with DeepSeek R1 as an automatic fallback.** If `x-ai/grok-4.6`
   errors (provider outage, allowlist), the slot silently falls back to `deepseek/deepseek-r1` and
   the doc labels it `(fallback)`. Note **DeepSeek R1 is a slow reasoner** (a run that falls back can
   take a couple of minutes; per-call timeout defaults to 220s). To use **Claude** as the 4th
   instead, set `anthropic/claude-opus-4.6` in `Tooling/v1.0.0/config/panel.json` — it works, but shares the
   author's lab (the weakest cross-check). Lower `--timeout`/`--max-tokens` for quicker, cheaper runs.
3. **GPT-5 spends tokens on hidden reasoning.** With a small `max_tokens` it can return empty content
   with `finish_reason: length`; the client uses a generous default and retries once with a larger
   budget. Keep `--max-tokens` ≥ ~4000.
4. **Confidence is non-deterministic at the model layer.** The orchestration (parallel fan-out,
   scoring, doc) is deterministic and self-tested; the models' *answers* are not — re-runs vary.
5. **`--web` reaches the public internet** (Perplexity). It is off by default; turn it on only when
   external fact-checking is wanted.

## Verified

- **Offline self-test** (`Tooling/v1.0.0/tests/selftest.py`, injected fake `call_model`, no network/secrets):
  **28/28** — consensus→HIGH, dissent→LOW, mixed→disagreements, failed-model→`FAILED`, single
  responder→`unknown`, web-tier gating, the honesty caveat, the primary→fallback path, and the
  hardening from a cross-model self-review: unparseable stance→non-responding (the honesty
  regression), fenced-stance ignored, stance counts + resolved-model manifest in the doc, the
  injection guardrail, and the corrected MEDIUM wording.
- **Live smoke** against OpenRouter: GPT-5 + Gemini + Grok 4.6 respond in parallel (3/3) and a doc is
  written.

This package was itself validated (LiteLLM GPT-5 + Gemini, a deliberately different backend) and the
resulting action items were applied — see the hardening above.

Run the self-test any time: `cd Tooling/v1.0.0 && python3 tests/selftest.py`. It is a **Python**
script and this tool ships no `run-tests.sh` — running it under `bash` produces shell syntax errors
that look like a broken suite but are only the wrong interpreter.

Recorded results for `v1.0.0` are in [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md):
28 passed, 0 failed on 2026-08-31 (migration agent), and 28 passed, 0 failed again on 2026-09-01
when the suite was re-run from the post-move location.
