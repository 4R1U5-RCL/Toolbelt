# Review — the workflow document, v1.0.0

`Workflows/Review` ships no program. Under PROCESS.md §4, "Tools with no
executable code", such a tool is **not exempt** from the versioned layout: the
documents that constitute the tool live here, under `Tooling/v<version>/`,
exactly as code would. This file is that document at v1.0.0.

It is not a marker file. It is not here to explain that the directory is empty —
it carries the tool's own text, and it is the file the next version directory is
seeded from when the workflow is written.

---

## The workflow, as documented

Everything this repository has ever recorded about the review workflow is one
sentence. It was the entire contents of `Workflows/Review/README.md` — 42 bytes,
one line — from the directory's creation until the 2026-08-31 conformance
migration:

> This folder contains the review workflow.

That is the complete text of the tool at v1.0.0. It is reproduced verbatim and
nothing has been added to it.

## What this document does not contain

The procedure itself has never been written. The following are not recorded
anywhere in this repository, and are deliberately **not** invented here:

- what the review workflow reviews, who runs it, and when it runs;
- its steps, inputs, outputs, artefacts and decision points;
- any command, script, template or configuration that carries it out.

Writing them is a build, not a migration. It is out of scope for the iterations
recorded in [`CHANGE_LOG.md`](../../CHANGE_LOG.md), neither of which had a
workflow to move or a procedure to transcribe.

## Version status

v1.0.0 is the tool's first version (PROCESS.md §9: a tool that has never been
versioned starts at `v1.0.0`). It establishes the document layout and nothing
else.

This directory has **not** been released — no PR carrying it has merged to
`main`, where `Workflows/Review` is still the single 42-byte `README.md`. It
therefore is not yet the immutable rollback point of §4; it becomes one on
merge. When the workflow is written, §4 applies normally: v1.0.0 freezes as the
rollback point and the work happens in `Tooling/v1.0.1/` or later.

Recorded in:

- [`KNOWN_ISSUES.md#workflows-review-fails-track-b-conforman_0b0b4b59`](../../KNOWN_ISSUES.md#workflows-review-fails-track-b-conforman_0b0b4b59)
- [`KNOWN_ISSUES.md#workflows-review-v1-0-0-migration-output_d18c44d1`](../../KNOWN_ISSUES.md#workflows-review-v1-0-0-migration-output_d18c44d1)
- [`CHANGE_LOG.md#create-the-process-md-section-3-document_cddfd0f4`](../../CHANGE_LOG.md#create-the-process-md-section-3-document_cddfd0f4)
- [`CHANGE_LOG.md#repair-the-workflows-review-v1-0-0-migra_23ca8994`](../../CHANGE_LOG.md#repair-the-workflows-review-v1-0-0-migra_23ca8994)
