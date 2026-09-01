# Review — workflow (stub)

This folder contains the review workflow.

**Current version: `v1.0.0`.** That version establishes the document layout only.
`Workflows/Review` has no executable code, so under PROCESS.md §4 the document
that constitutes the tool lives in
[`Tooling/v1.0.0/REVIEW.md`](Tooling/v1.0.0/REVIEW.md) exactly as code would, and
[`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) records that no executable
suite exists and names the Track-B conformance checks run in its place. Canonical
documents: [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md),
[`TEMPLATES.md`](TEMPLATES.md), [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md),
[`CHANGE_LOG.md`](CHANGE_LOG.md).

## State of this tool

The sentence at the top is, verbatim, everything this tool has ever documented
about itself. Before the 2026-08-31 conformance migration the directory held
exactly one file — this `README.md`, 42 bytes — and nothing else: no `bin/`, no
`lib/`, no `commands/`, no `examples/`, no `templates/`, no `tests/`, no
`run-tests.sh`, no config of any kind.

So the following are **not** documented anywhere in this repo, and are not
invented here:

- what the review workflow reviews, or who runs it;
- its steps, inputs, outputs, or decision points;
- any command, script, or template that implements it.

`PROCESS.md` §9 lists `Workflows/Review` in the migration backlog with `README`
present and every other column absent — consistent with what was on disk.

**Related but not part of this tool:** the repo's only other review material is
the independent reviewer role in [`../Sprint/`](../Sprint/) (`fleet-kit/README.md`,
"Review protocol"). It belongs to the Sprint workflow. It is *not* evidence of
what this workflow is or is meant to be, and nothing in the repo connects the two.

## What conformance did and did not settle

The tool now carries the §3 documents and the §4 version directories, and under
PROCESS.md §10 decisions 9 and 10 a code-less tool conforms on those terms: its
documents are its `Tooling/` contents, and a recorded Track-B result is the
invariant-5 evidence a PR needs. Being code-less is no longer a reason this tool
cannot merge.

What that does **not** settle is the tool itself. `Tooling/v1.0.0/REVIEW.md`
records one sentence because one sentence is all that has ever been written.
Closing that gap means writing the workflow — the procedure, the artefacts it
produces, and a test that exercises it. That is a build, not a migration, and it
is out of scope for both iterations in [`CHANGE_LOG.md`](CHANGE_LOG.md), neither
of which had a workflow to move.
