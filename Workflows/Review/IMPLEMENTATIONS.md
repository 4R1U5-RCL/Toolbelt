# Implementations — Workflows/Review

How this tool is used in each different use case, each entry linking to its
template in [`TEMPLATES.md`](TEMPLATES.md) (PROCESS.md §3).

Append-only (PROCESS.md §5.2).

| Implementation | Template | Status |
|---|---|---|
| — | — | none recorded |

### No implementations are recorded

**This file is empty-but-valid** (PROCESS.md §9): it exists so the Track B
canonical-files check has something to check, and it records the absence honestly
rather than inventing content.

There is no implementation to describe. As of the 2026-08-31 migration the tool
directory contained one file, `README.md`, whose entire body is:

> This folder contains the review workflow.

There is no `bin/`, `lib/`, `commands/`, `examples/`, `templates/`, `n8n/`,
`tests/` or `run-tests.sh`, and no configuration file of any kind. Nothing in
this repo states what the review workflow does, what it is invoked with, or what
it produces — so no use case can be derived from the repo, and none is asserted
here.

Being code-less does not exempt the tool from PROCESS.md §3 or §4 (§10 decision
9): the document that constitutes it lives at
[`Tooling/v1.0.0/REVIEW.md`](Tooling/v1.0.0/REVIEW.md). But that document records
a stub, and a stub yields no use case — so this file stays empty of entries on
the facts, not on an exemption.

**The first entry can be written when the workflow itself exists.** At that point
it names the use case, the invocation, and cites its `TEMPLATES.md` entry; the
template entry cites it back.

*(The section heading above is level 3 deliberately. `process.yaml`
`definitions.entry` makes any level-2 heading an entry, so a level-2 prose
heading in this file would be read as a malformed entry with a non-id name and
would fail the reciprocity check. This file has zero entries.)*
