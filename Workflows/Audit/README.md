# Workflows/Audit

**Current version: `v1.0.0`** — see [`Tooling/v1.0.0/`](Tooling/v1.0.0/), which
holds no code, for the reason.

> This folder contains the audit workflow.

That sentence, preserved above exactly as written, was the entire content of this
file — and of this tool — until 2026-08-31. It is the only authored statement
about `Workflows/Audit` anywhere in the repository.

## What is actually here

**No implementation of any kind.** No script, no `bin/`, no `lib/`, no
`commands/`, no `examples/`, no `templates/`, no `n8n/`, no config, no `tests/`
and no `run-tests.sh`. Before the conformance migration recorded in
[`CHANGE_LOG.md`](CHANGE_LOG.md) this directory contained exactly one file: this
README. The verbatim `find` output establishing that is kept in
[`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log).

## What the audit workflow does

**Unknown from this repository.** The sentence above does not say which audit is
meant, what it inspects, what triggers it, what it produces, or which tools or
agents take part. A full-text search for "audit" across the Toolbelt repo turns
up only this file, the `Workflows/Audit` row of the PROCESS.md §9 backlog table,
and unrelated uses of the phrase "audit trail" in `Packages/Poller`,
`Packages/Telegram` and `Workflows/Sprint`.

Nothing further is claimed here, because anything further would be invented.
PROCESS.md §1 notes that this repo is v2.0 of `operand-packages` and that not
every tool has been transferred yet — an audit workflow may well exist elsewhere,
but it has not landed here, and this README describes only what has.

## Status

**A reserved name awaiting its first implementation.** There is nothing here to
run, copy or follow. If you came looking for a working audit workflow, this is
not one yet — that gap is logged as
[`KNOWN_ISSUES.md#workflows-audit-failed-track-b-conforman_fb119cc2`](KNOWN_ISSUES.md#workflows-audit-failed-track-b-conforman_fb119cc2)
and closing it needs an owner decision about what this workflow should be.

## Files

| Path | Holds |
|---|---|
| [`README.md`](README.md) | This file |
| [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) | Empty-but-valid — no implementation exists to describe |
| [`TEMPLATES.md`](TEMPLATES.md) | Empty-but-valid — no `templates/` directory and no template file exists |
| [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) | One entry: the Track B conformance failure found on 2026-08-31 |
| [`CHANGE_LOG.md`](CHANGE_LOG.md) | One entry: the migration that created these documents |
| [`Tooling/v1.0.0/`](Tooling/v1.0.0/) | The version anchor. Holds an explanatory note, not code, because no code exists |
| [`Tests/v1.0.0/`](Tests/v1.0.0/) | The recorded result of trying to test `v1.0.0`: **NOT RUN**, nothing runnable exists |
