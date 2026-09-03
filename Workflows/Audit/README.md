# Workflows/Audit — retired

**Current version: `v1.1.0`** — the document that constitutes this tool is
[`Tooling/v1.1.0/WORKFLOW.md`](Tooling/v1.1.0/WORKFLOW.md).

> **This name is retired. The capability lives at
> [`Packages/Sentinel`](../../Packages/Sentinel).**

## What was here

Nothing that ran. From this directory's creation until the conformance migration
of 2026-08-31, its entire content was one file containing one sentence:

> This folder contains the audit workflow.

That sentence named a folder rather than describing a process. It specified no
audit target, no trigger, no standard, no output and no steps, and no other
statement about this workflow existed anywhere in the repository. It is
preserved verbatim at [`Tooling/v1.0.0/WORKFLOW.md`](Tooling/v1.0.0/WORKFLOW.md),
which is immutable under PROCESS.md §4.

The migration recorded in [`CHANGE_LOG.md`](CHANGE_LOG.md) made the tool
conformant at `v1.0.0` — five canonical documents, version anchors, a recorded
Track-B result — and deliberately authored no workflow logic, because composing
steps from a sentence that names none would have been inventing a method and
publishing it as a proven one. That left the tool conformant and inert, which is
what `v1.1.0` resolves.

## Why it was retired instead of implemented

"Audit" named three unrelated capabilities:

| The thing | Where it lives |
|---|---|
| Host integrity / rootkit sweeping | [`Packages/Sentinel`](../../Packages/Sentinel) |
| App-surface security review — RLS, response headers, dependency scanning | a separate tool outside this repo |
| Conformance of a tool against PROCESS.md | the Track-B checks of §7, run per tool |

No single implementation could honour a name all three answer to, and a reader
who found this directory could not tell which of the three they had found.
Sentinel is also a program, and `Workflows/` is for processes rather than
programs (PROCESS.md §2). The reasoning in full:
[`Tooling/v1.1.0/WORKFLOW.md`](Tooling/v1.1.0/WORKFLOW.md).

## If you want a workflow-shaped audit

Open a new tool under a name that says which audit it is, and start at `v1.0.0`
via PROCESS.md §6 step 1. Do not revive this directory — a live tool behind a
document that says "retired" reads as a reversal rather than a supersession.

## Status

Retired at `v1.1.0`, superseded by `Packages/Sentinel`. Nothing here runs, and
nothing here is expected to. The directory is kept because the record of a
reserved name that was never built is the finding that produced the retirement.

## Files

| Path | Holds |
|---|---|
| [`README.md`](README.md) | This file |
| [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) | Empty-but-valid — no implementation ever existed to describe |
| [`TEMPLATES.md`](TEMPLATES.md) | Empty-but-valid — no `templates/` directory and no template file exists |
| [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) | Three entries: the Track B failure, the defects in its migration, and the retirement |
| [`CHANGE_LOG.md`](CHANGE_LOG.md) | Three entries: the migration, the correction of its records, and the retirement |
| [`Tooling/v1.0.0/`](Tooling/v1.0.0/) | The tool's complete authored substance before retirement — one sentence. Immutable |
| [`Tooling/v1.1.0/`](Tooling/v1.1.0/) | The retirement, and why the name was not filled in |
| [`Tests/v1.0.0/`](Tests/v1.0.0/) | Recorded evidence for v1.0.0 — no executable suite exists; Track-B checks stand in |
| [`Tests/v1.1.0/`](Tests/v1.1.0/) | Recorded evidence for v1.1.0 — same, for the retirement |
