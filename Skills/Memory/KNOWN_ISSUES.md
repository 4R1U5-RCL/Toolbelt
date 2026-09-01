# Known issues — Skills/Memory

Append-only (PROCESS.md §5.1). Every entry carries the fields `process.yaml`
defines under `issue-entry`, and cites the iteration that addresses it in
[`CHANGE_LOG.md`](CHANGE_LOG.md).

Entries are delimited by a level-2 heading whose text is the bare id
(`process.yaml: definitions.entry`) — no backticks, nothing else on the line, so
that a `KNOWN_ISSUES.md#<id>` citation resolves against the heading.

Ids are `<description>_<hash8>` (`process.yaml: definitions.issue-id`): the
description is the summary slugified, the hash is the first 8 hex characters of
sha256 over the canonicalised summary. Canonicalisation is trim → lowercase →
collapse whitespace runs to a single space → strip trailing punctuation
(`. , ; : ! ?`). Identity is the `summary` field alone (PROCESS.md §10.3).

`status` is drawn from the closed set of seven in
`process.yaml: definitions.issue-status` — `open, planned, in-progress,
resolved, escalated, legacy, wont-fix`. No entry in this file is `legacy`: this
tool had only a `README.md` before its first conformant version, so every entry
here was written under PROCESS.md and is bound by the reciprocity check.

---

## skills-memory-failed-track-b-conformance_6cdef98b

| Field | Value |
|---|---|
| **id** | `skills-memory-failed-track-b-conformance_6cdef98b` |
| **summary** | Skills/Memory failed Track B conformance: four canonical documents missing, code not under Tooling/, no recorded results under Tests/, README named no version |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#migrated-skills-memory-to-the-tooling-v1_16012fef`](CHANGE_LOG.md#migrated-skills-memory-to-the-tooling-v1_16012fef) at fix-version-id `v1.0.0` |
| **branch** | `smoke/fix-skills-memory` |
| **occurrences** | 1 — 2026-08-31, found by the Track B conformance check run against `Skills/Memory` during this migration |

The status is `in-progress`, not `resolved`: the iteration has been executed on
the branch above but the change is not merged, and
`process.yaml: definitions.issue-status` states that `resolved` is never written
while `merge_commit` is empty. It becomes `resolved` at §6 step 7, citing the
merge commit.

### Outcome (X) — what it resulted in

`Skills/Memory` failed four of the five Track B checks in PROCESS.md §7:

- **Canonical files** — FAIL. Only `README.md` existed. `IMPLEMENTATIONS.md`,
  `TEMPLATES.md`, `KNOWN_ISSUES.md` and `CHANGE_LOG.md` were all absent, which
  matches the `Skills/Memory` row of the §9 migration-backlog table.
- **Code layout** — FAIL. The tool's code sat at the tool root as `templates/`
  and `tests/`; there was no `Tooling/` directory at all.
- **Test layout** — FAIL. No `Tests/` directory existed. `tests/verify.sh` was
  runnable and passing, but nothing in the repo recorded that it had been run or
  what it produced; the only claim was the `18/18` line in `README.md`, which is
  a claim rather than a captured result.
- **Version agreement** — FAIL. `README.md` named no version anywhere (the word
  "version" appeared once, inside a caveat about stale entries), and there was
  no `Tooling/` directory and no `CHANGE_LOG.md` entry to agree with.
- **Reciprocity** — vacuously passing, since there were no entries in any of the
  paired files to be non-reciprocal.

The consequence is the one PROCESS.md §1 exists to prevent: staleness was
invisible. Nothing recorded which version of this tool was current, no rollback
point existed, and there was no place to log an issue against it — so the tool
could not release a new version (§7, "a tool failing Track B cannot release a
new version").

### Cause (Y) — the mechanism

The tool predates the layout PROCESS.md §3/§4 requires. It was authored as a
flat package — `README.md` plus `templates/` plus `tests/` — under the earlier
`operand-packages` convention, and was carried into this repo unchanged. No
process step existed at authoring time to demand the five documents or the
versioned directories, and nothing since has touched the tool through the §6 fix
procedure, which is the step that would have brought it into conformance (§9,
"on next touch"). The absence is inherited, not a regression: no change was made
to this tool that removed anything.

Because the tool had never been versioned, §9 applies its rule directly — its
current code becomes `Tooling/v1.0.0/` regardless of any version the README
claims, and the README is corrected to match.

### Iteration (Z) — what is planned

Migrated Skills/Memory to the Tooling/v1.0.0 and Tests/v1.0.0 layout and created
the four missing canonical documents. Concretely, at `v1.0.0`, without changing
any tool behaviour:

1. Move `templates/` and `tests/` into `Tooling/v1.0.0/`, leaving the canonical
   `.md` files at the tool root.
2. Repair any path broken by the move, then run `tests/verify.sh` from its new
   location and capture the real output.
3. Record that output under `Tests/v1.0.0/` as `run-tests.log` plus `RESULTS.md`.
4. Create the four missing canonical documents, `TEMPLATES.md` and
   `IMPLEMENTATIONS.md` reciprocal to each other, and this file reciprocal to
   `CHANGE_LOG.md`.
5. State `v1.0.0` in `README.md` and repoint its `templates/` and `tests/` paths.

Recorded in
[`CHANGE_LOG.md#migrated-skills-memory-to-the-tooling-v1_16012fef`](CHANGE_LOG.md#migrated-skills-memory-to-the-tooling-v1_16012fef),
whose `iteration` field is the first sentence above — the string this change-id
is derived from.
