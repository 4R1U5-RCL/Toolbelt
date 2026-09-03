# Workflows/Audit — retired, v1.1.0

This is the document that **constitutes** `Workflows/Audit` at `v1.1.0`. Under
PROCESS.md §4 a tool with no executable code is not exempt from the versioned
directory rule, so the retirement is written here rather than only in the README.

## The workflow is retired

`Workflows/Audit` never had an implementation. Its entire authored substance at
`v1.0.0` was one sentence — "This folder contains the audit workflow." — which
named a folder rather than describing a process. That is recorded verbatim and
unabridged at [`../v1.0.0/WORKFLOW.md`](../v1.0.0/WORKFLOW.md), which remains
immutable and is this version's rollback point.

**The capability moved to [`Packages/Sentinel`](../../../../Packages/Sentinel).**

## Why the name is retired rather than filled in

Three unrelated things were called "audit" across the system this repo serves:

| The thing | Where it actually lives |
|---|---|
| Host integrity / rootkit sweeping | `Packages/Sentinel` (this retirement's replacement) |
| App-surface security review — RLS, response headers, dependency scanning | a separate tool outside this repo |
| Conformance of a tool against PROCESS.md | the Track-B checks of §7, run per tool |

A reserved name that could plausibly mean any of the three is worse than no name
at all: a reader who finds `Workflows/Audit` cannot tell which one they have
found, and PROCESS.md §1 exists to make exactly that ambiguity visible. Filling
the name in with one of the three would have left the other two silently
excluded by a directory that looks general.

It is also the wrong shelf. Sentinel ships a program, and `Workflows/` is for
multi-step processes rather than programs (§2). Building it here would have
required either mis-filing it or loosening the taxonomy to fit one tool.

## What this version does and does not change

**Does:** records the retirement, names the replacement, and states the reason
so the decision is not re-litigated from an empty directory.

**Does not:** delete anything. `v1.0.0` stays exactly as released — the sentence,
its Track-B result, and the issue that logged it. The history of a name that was
reserved and never built is itself the useful record here, and PROCESS.md §4
makes a released version directory immutable regardless.

## If a workflow-shaped audit is ever wanted

Open a new tool with a name that says which audit it is, and start at `v1.0.0`
with PROCESS.md §6 step 1. Do not revive this directory: reusing a retired name
would put a live tool behind a document that says it is retired, and the
version history would read as though the retirement had been reversed rather
than superseded.
