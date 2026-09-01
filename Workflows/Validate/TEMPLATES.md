# TEMPLATES — Workflows/Validate

Production-ready application forms for this tool. Each entry is cited by its counterpart in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) (PROCESS.md §3 reciprocity).

Entry headings are the **bare id** — no backticks, no title text on the heading line
(`process.yaml` `definitions.entry`). The heading text is the anchor that `TEMPLATES.md#<id>` citations
resolve against, so anything else on the line breaks the citation and makes reciprocity
unverifiable by grep. Each entry's one-line title is the first line of its body instead.

> **Scope note (honest gap).** This tool has **no `templates/` directory**. Nothing was invented
> to fill this file: every form below is copied verbatim from an artifact that actually exists in
> the repo — the invocation forms in [`README.md`](README.md) and the `bin/validate` docstring, and
> the shipped panel config at `Tooling/v1.0.0/config/panel.json`. If a `templates/` directory is
> added later, it is documented here and this note is replaced.

All paths below are relative to `Tooling/v1.0.0/`. Every form requires `OPENROUTER_API_KEY` in the
environment; `bin/validate` exits with an error if it is unset.

---

## t-inline-content

**Validate content passed as an argument.**

Source: `README.md` "Install & use"; `bin/validate` docstring.

```sh
set -a; . /studio/.env; set +a          # or: export OPENROUTER_API_KEY=...

bin/validate "the plan text..."
```

Implementation: [`IMPLEMENTATIONS.md#i-inline-content`](IMPLEMENTATIONS.md#i-inline-content)

---

## t-file-input

**Validate a document on disk.**

Source: `README.md` "Install & use".

```sh
bin/validate --input plan.md --subject "one-line"
```

`--subject` is a one-line description of what is being stress-tested; it also seeds the output
filename when `--topic` is not given.

Implementation: [`IMPLEMENTATIONS.md#i-file-input`](IMPLEMENTATIONS.md#i-file-input)

---

## t-stdin-pipe

**Validate piped content.**

Source: `README.md` "Install & use".

```sh
cat plan.md | bin/validate --input -
```

Implementation: [`IMPLEMENTATIONS.md#i-stdin-pipe`](IMPLEMENTATIONS.md#i-stdin-pipe)

---

## t-web-factcheck

**Add the opt-in Perplexity web fact-check.**

Source: `README.md` "Install & use" and "Honesty invariants".

```sh
bin/validate --input plan.md --web
```

Reaches the public internet (Perplexity Sonar). Off by default. The web tier fact-checks and does
**not** cast a stance vote, so it never moves the confidence label.

Implementation: [`IMPLEMENTATIONS.md#i-web-factcheck`](IMPLEMENTATIONS.md#i-web-factcheck)

---

## t-panel-subset

**Run a subset of the panel.**

Source: `README.md` "Install & use".

```sh
bin/validate --input plan.md --panel gpt5,grok
```

Keys are matched against the `key` field of each reasoner in the panel config. A `--panel` value
matching no reasoner is a hard error.

> Caveat carried from `README.md`: fewer than two reasoners responding yields confidence
> `unknown`, so a one-key subset can never produce a confidence label.

Implementation: [`IMPLEMENTATIONS.md#i-panel-subset`](IMPLEMENTATIONS.md#i-panel-subset)

---

## t-panel-config

**The panel definition.**

Source: `Tooling/v1.0.0/config/panel.json` (verbatim), also quoted in `README.md`
"Configuration". This is the default `--config` value; swap models here rather than in code.

```json
{
  "reasoners": [
    { "key": "gpt5",   "model": "openai/gpt-5",          "label": "GPT-5 (OpenAI)" },
    { "key": "gemini", "model": "google/gemini-2.5-pro", "label": "Gemini 2.5 Pro (Google)" },
    { "key": "grok", "model": "x-ai/grok-4.6", "label": "Grok 4.6 (xAI)",
      "fallback": { "model": "deepseek/deepseek-r1", "label": "DeepSeek R1 (DeepSeek)" } }
  ],
  "web": { "key": "perplexity", "model": "perplexity/sonar", "label": "Perplexity Sonar" },
  "defaults": { "max_tokens": 6000, "timeout": 220 }
}
```

Point at an alternative file with `--config <panel.json>`.

Implementation: [`IMPLEMENTATIONS.md#i-panel-config`](IMPLEMENTATIONS.md#i-panel-config)

---

## t-offline-selftest

**Run the offline self-test.**

Source: `README.md` "Verified" — *"Run the self-test any time: `cd Tooling/v1.0.0 && python3 tests/selftest.py`"*.

```sh
cd Tooling/v1.0.0
python3 tests/selftest.py
```

No network and no secrets — the suite injects a fake `call_model`. Recorded output for v1.0.0:
[`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md).

> **Runner trap.** `tests/selftest.py` is a **Python** script, not a shell script, and this tool
> ships no `run-tests.sh`. Invoking it as `bash tests/selftest.py` fails with shell syntax errors
> (`import: command not found`, `syntax error near unexpected token`) that look like a broken
> suite but are only the wrong interpreter. Always run it with `python3`.

Implementation: [`IMPLEMENTATIONS.md#i-offline-selftest`](IMPLEMENTATIONS.md#i-offline-selftest)
