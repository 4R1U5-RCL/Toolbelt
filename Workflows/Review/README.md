# Review — workflow (stub)

This folder contains the review workflow.

**Current version: `v1.0.0`.** That version establishes the document layout only —
[`Tooling/v1.0.0/`](Tooling/v1.0.0/) contains **no implementation**, and
[`Tests/v1.0.0/`](Tests/v1.0.0/) records that no test could be run because none
exists. Canonical documents: [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md),
[`TEMPLATES.md`](TEMPLATES.md), [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md),
[`CHANGE_LOG.md`](CHANGE_LOG.md).

## State of this tool

The sentence above is, verbatim, everything this tool has ever documented about
itself. Before the 2026-08-31 conformance migration the directory held exactly
one file — this `README.md`, 42 bytes — and nothing else: no `bin/`, no `lib/`,
no `commands/`, no `examples/`, no `templates/`, no `tests/`, no `run-tests.sh`,
no config of any kind.

So the following are **not** documented anywhere in this repo, and are not
invented here:

- what the review workflow reviews, or who runs it;
- its steps, inputs, outputs, or decision points;
- any command, script, or template that implements it.

`PROCESS.md` §9 lists `Workflows/Review` in the migration backlog with `README`
present and every other column absent — consistent with what is on disk.

**Related but not part of this tool:** the repo's only other review material is
the independent reviewer role in [`../Sprint/`](../Sprint/) (`fleet-kit/README.md`,
"Review protocol"). It belongs to the Sprint workflow. It is *not* evidence of
what this workflow is or is meant to be, and nothing in the repo connects the two.

## What would close the gap

Writing the workflow itself: the procedure, the artefacts it produces, and a
test that exercises it. That is a build, not a migration, and it is out of scope
for the change recorded in [`CHANGE_LOG.md`](CHANGE_LOG.md) — which moved no code
because there was none to move.
