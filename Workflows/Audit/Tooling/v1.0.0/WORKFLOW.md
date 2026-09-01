# Workflows/Audit — the workflow, v1.0.0

This is the document that **constitutes** `Workflows/Audit`. PROCESS.md §4: a
tool with no executable code is not exempt from the versioned-directory rule —
"the documents that constitute the tool live under `Tooling/v<version>/` exactly
as code would". This is that document, and it is the tool's substance at
`v1.0.0`, not a note about the directory.

## The workflow, in full

> This folder contains the audit workflow.

That sentence is the complete authored specification of this workflow, quoted
verbatim and unabridged. It was the entire content of the tool's `README.md`
from the directory's creation until the conformance migration of 2026-08-31, and
no other statement about this workflow exists anywhere in the repository.

## What v1.0.0 therefore specifies

**The name, and nothing else.** The sentence names no audit target, no trigger,
no standard to audit against, no output, no participating agent or tool, and no
sequence of steps. It describes a folder rather than a process, so a reader
cannot run this workflow from this document.

Nothing has been added to it. Composing steps from a sentence that names none
would be inventing the workflow, and this repository exists so its contents can
be copied as **proven** method (PROCESS.md §1) — an invented method copied as a
proven one is precisely the harm the conventions are written to prevent.

## What is not here, and why that is a property of the tool

`Workflows/Audit` ships no program: no script, `bin/`, `lib/`, `commands/`,
`examples/`, `templates/`, `n8n/`, config or test suite. That is not a migration
gap. Nothing was left behind in the old flat layout — the `find` capture in
[`../../Tests/v1.0.0/run-tests.log`](../../Tests/v1.0.0/run-tests.log) shows the
tool directory holding exactly one file before the migration. No implementation
was ever written. This tool is a reserved name whose process description has not
been authored.

That gap is logged as
[`workflows-audit-failed-track-b-conforman_fb119cc2`](../../KNOWN_ISSUES.md) and
closing it needs an owner decision about what this workflow is meant to be.

## Extending this version

When the process is written, PROCESS.md §6 applies from step 1: log the work in
`KNOWN_ISSUES.md` and `CHANGE_LOG.md` first, branch, then seed
`Tooling/v1.1.0/` from this directory and write the process there. `v1.0.0` is
not edited once it has merged — §4 makes a released version directory immutable,
and that immutability is what makes it the rollback point.
