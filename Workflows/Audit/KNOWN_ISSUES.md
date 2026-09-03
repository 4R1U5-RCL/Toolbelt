# Known issues — Workflows/Audit

Every issue found with this tool, each citing the iteration that addressed it in
[`CHANGE_LOG.md`](CHANGE_LOG.md) (PROCESS.md §3).

**Append-only** (PROCESS.md §5.1). Entries are never removed; a fix appends a new
entry carrying the version that resolved it. Ids follow `process.yaml` →
`definitions.issue-id`: `<description>_<hash8>`, hashed over the `summary` field
alone (PROCESS.md §10.3).

**Note on history.** This file was created on 2026-08-31 by the first entry
below. No earlier issue history was reconstructed, because none was recorded and
none is recoverable from the repository — the tool consisted of a single README.
No entry in this file is `legacy`: both predate no conformant version, they
*are* the conformance work, so both are bound by the §7 reciprocity check.

| Id | Summary | Status |
|---|---|---|
| [workflows-audit-failed-track-b-conforman_fb119cc2](#workflows-audit-failed-track-b-conforman_fb119cc2) | Failed Track B conformance: four of five canonical documents missing, no `Tooling/` or `Tests/`, no version, no implementation | in-progress |
| [the-2026-08-31-conformance-migration-of_0b111e47](#the-2026-08-31-conformance-migration-of_0b111e47) | The migration's own records violated the amended spec: invented marker file, change-id off the wrong field, prose status, untrue branch claim | in-progress |
| [workflows-audit-is-a-reserved-name-carry_1ec09cf6](#workflows-audit-is-a-reserved-name-carry_1ec09cf6) | A reserved name with one sentence and no implementation, while the capability it named was built as `Packages/Sentinel` | in-progress |

---

## workflows-audit-failed-track-b-conforman_fb119cc2

| Field | Value |
|---|---|
| **id** | `workflows-audit-failed-track-b-conforman_fb119cc2` |
| **summary** | Workflows/Audit failed Track B conformance: four of five canonical documents missing, no Tooling/ or Tests/ directories, README states no version and no implementation exists |
| **outcome** | The tool cannot release a version, and — more damaging — the repository gave a reader no way to tell whether this workflow was working, broken, superseded or never built |
| **cause** | Two: the tool predates PROCESS.md and was never migrated to the `Tooling/`/`Tests/` layout (the §9 backlog), and separately no implementation was ever written for it |
| **iteration** | A documents-only conformance migration at v1.0.0: create the four missing canonical documents as empty-but-valid records, establish the Tooling/v1.0.0 and Tests/v1.0.0 version anchors, state v1.0.0 in the README, and author no workflow logic, script, prompt, template or test |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#a-documents-only-conformance-migration-a_27d16c95`](CHANGE_LOG.md#a-documents-only-conformance-migration-a_27d16c95), fix-version `v1.0.0` |
| **occurrences** | 1 — detected 2026-08-31 during the Track B sweep recorded in PROCESS.md §9 |

**Why `in-progress` and not `resolved`.** `merge_commit` in the cited change
entry is empty: the work sits unmerged on branch `smoke/fix-workflows-audit`.
`process.yaml → definitions.issue-status` is explicit — "`resolved` is never
written while merge_commit is empty; an approved-but-unmerged fix is still
`in-progress`". It moves to `resolved` at PROCESS.md §6 step 7, on merge.

**Id derivation.** `hash8` = first 8 hex chars of `sha256` over the canonical
form of the **summary field alone** — trimmed, lowercased, whitespace runs
collapsed to one space, trailing punctuation stripped. Recomputed on 2026-09-01
with `sha256sum`: `fb119cc2`. Unchanged from the migration. `description` = that
summary slugified per `process.yaml → slug_rule`, truncated to 40 characters.
The verbatim recomputation is in
[`Tests/v1.0.0/id-recompute-2026-09-01.log`](Tests/v1.0.0/id-recompute-2026-09-01.log).

### Outcome (X) — what the failure resulted in

The tool cannot release a version: PROCESS.md §7 blocks a Track B failure until
it is logged and fixed. Measured at the tool root on 2026-08-31, all five checks
of the §7 Track B table are involved:

| Check | Result | What was actually found |
|---|---|---|
| Canonical files | **failed** | `README.md` present and non-empty (41 bytes, one sentence). `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md`, `CHANGE_LOG.md` — **all four missing** |
| Reciprocity | **vacuous** | With no `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` or `CHANGE_LOG.md` there were no entries on any side to cite or fail to cite |
| Code layout | **failed** | No `Tooling/` directory existed. The tool directory contained exactly one file: `README.md`, which held the workflow's entire authored substance outside `Tooling/` |
| Test layout | **failed** | No `Tests/` directory and no recorded results of any kind |
| Version agreement | **failed** | `README.md` named no version; there was no `Tooling/` directory and no `CHANGE_LOG.md` entry to agree with it. Three places that must name one version named it in zero |

The compounding effect is the one PROCESS.md §1 warns about: **staleness was
invisible.** From the repository alone a reader could not tell whether this
workflow was working, broken, superseded or never built — the last of which turns
out to be the truth. The §9 backlog row for `Workflows/Audit`
(`README ✅` and everything else `❌`) matches the finding exactly.

### Cause (Y) — the mechanism

Two distinct causes, and they should not be conflated:

1. **The four missing documents and the missing directories** are the PROCESS.md
   §9 backlog: the tool predates the convention, was created in the flat
   pre-`Tooling/` shape the whole repo used, and was never migrated. This is the
   same cause as every other row of that table.
2. **The missing implementation is not a migration gap at all.** No code was left
   behind in the old layout; none was ever written. The directory was created as
   a placeholder — a name reserved for a workflow, with a one-line README
   describing the folder rather than the tool — and nothing was ever added to it.
   PROCESS.md §1 notes this repo is v2.0 of `operand-packages` and that "absence
   here does not mean a tool does not exist", so an audit workflow may exist
   outside this repo; what is certain is that it has not landed in this one.

### Iteration (Z) — what is planned to resolve it

Bring the tool into document conformance at `v1.0.0` without inventing anything:
create the four missing canonical documents as empty-but-valid records of what
genuinely exists, move the workflow's authored substance into `Tooling/v1.0.0/`
where PROCESS.md §4 requires a code-less tool's constituting documents to live,
record the tool's test state under `Tests/v1.0.0/`, and state `v1.0.0` in the
README. No workflow logic, script, prompt, template or test is authored. Planned
and recorded in
[`CHANGE_LOG.md#a-documents-only-conformance-migration-a_27d16c95`](CHANGE_LOG.md#a-documents-only-conformance-migration-a_27d16c95).

### Honest limits — what this entry does not fix

This iteration closes cause (1) and **cannot** close cause (2). After it:

- The tool still has no implementation, so `IMPLEMENTATIONS.md` and
  `TEMPLATES.md` remain empty-but-valid rather than useful.
- `Tooling/v1.0.0/WORKFLOW.md` holds the workflow's entire authored substance —
  one sentence naming the folder. The code-layout check passes on its §4 terms
  (what constitutes the tool sits under `Tooling/v<version>/`) while the tool
  itself remains unspecified. Do not read the passing check as a working tool.
- `Tests/v1.0.0/` records that **no executable suite exists** and carries the
  Track-B conformance result in its place, per PROCESS.md §4 and §5.5. It is not
  a passing test suite, and there is no suite to pass.

Writing the audit workflow is a separate piece of work needing the one input the
repository does not contain: what this workflow is supposed to do. That input is
an owner decision, not something an agent can derive.

**Still your job.** Decide what `Workflows/Audit` is meant to be — or record
that the folder should be removed. Until then this tool is a reserved name, and
anyone reaching for it should know that before they reach.

---

## the-2026-08-31-conformance-migration-of_0b111e47

| Field | Value |
|---|---|
| **id** | `the-2026-08-31-conformance-migration-of_0b111e47` |
| **summary** | The 2026-08-31 conformance migration of Workflows/Audit produced records that violate the amended spec: an invented Tooling marker file, a change-id derived from the summary instead of the iteration, a prose status outside the closed set of seven, and a branch claim that was untrue when written |
| **outcome** | Four conformance defects in the tool's own records: an unmergeable code-layout story built on an invented marker, an unreproducible change-id, an unparseable status, and a false statement about where the work sat |
| **cause** | The migration ran against the pre-amendment PROCESS.md, which had no rule for a code-less tool (decision 9), no identity for `change-id` (decision 8), no closed status set (decision 11) and no evidence path that a code-less tool could satisfy (decision 10); the agent filled each gap by invention rather than escalating |
| **iteration** | Correct the migration records in place at v1.0.0, which was never released: remove the invented Tooling marker file and place the tool constituting document under Tooling/v1.0.0, recompute the change-id from its iteration field, replace the prose status with a closed-set value, name the real branch, and record the Track-B checks in Tests/v1.0.0/RESULTS.md as the evidence invariant 5 now requires |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#correct-the-migration-records-in-place-a_531c29b0`](CHANGE_LOG.md#correct-the-migration-records-in-place-a_531c29b0), fix-version `v1.0.0` |
| **occurrences** | 1 — detected 2026-09-01 by the audit of the smoke-test migration, by an agent that did not perform the migration |

**Id derivation.** `hash8` = `sha256` over the canonical summary alone =
`0b111e47`, recomputed with `sha256sum` on 2026-09-01; verbatim in
[`Tests/v1.0.0/id-recompute-2026-09-01.log`](Tests/v1.0.0/id-recompute-2026-09-01.log).

### Outcome (X) — what the defects resulted in

| Defect | What it produced |
|---|---|
| Invented marker file | `Tooling/v1.0.0/README.md` existed only to declare that the directory was empty and to justify the anchor. It put a statement *about* the tool where §4 requires the documents that *constitute* it, and it told the reader to delete itself later — a workaround, not a record |
| `change-id` off the wrong field | `brought-workflows-audit-into-track-b-con_be1c5a4b` hashes the entry's `summary`. `summary` is not a `change-entry` field at all (`process.yaml → definitions.change-entry`), so the id could not be reproduced from any field the entry is required to carry |
| Prose status | `status` read "open — the document half of the iteration is executed on this branch; it closes on merge…". Not one of the seven values, so no checker could read it, and the index table disagreed with the entry body |
| Untrue branch claim | Both root documents asserted the work "sits on a branch". At the time they were written the migration was committed as `7fc023f`, and no `smoke/fix-*` branch existed. The claim was false when made |

### Cause (Y) — the mechanism

The migration ran against a specification with four holes in it, and closed each
hole by inventing rather than escalating. PROCESS.md §5 is explicit that "an
agent that cannot proceed without breaking one stops and reports"; the marker
file is what happens when it does not. The holes themselves are now closed —
decisions 8, 9, 10, 11, 13 and 14 in PROCESS.md §10, settled 2026-09-01 by the
audit that opened this entry. The defects are therefore genuinely the migration's
and genuinely the spec's, in that order.

### Iteration (Z) — what is planned to resolve it

Correct the records in place at `v1.0.0`. **No version bump**: `v1.0.0` has never
merged to `main`, so it is not a released version directory, and PROCESS.md §4
immutability does not yet bind it. Concretely — delete the marker and write the
constituting document in its place; recompute both entry ids from their identity
fields with `sha256sum` and repair every citation; replace the prose status with
`in-progress` on both entries; name branch `smoke/fix-workflows-audit`
explicitly wherever the branch is referenced; rewrite `Tests/v1.0.0/RESULTS.md`
to record that no executable suite exists and to carry the Track-B checks run in
its place. Recorded in
[`CHANGE_LOG.md#correct-the-migration-records-in-place-a_531c29b0`](CHANGE_LOG.md#correct-the-migration-records-in-place-a_531c29b0).

### Honest limits — what this entry does not fix

- It does not implement the workflow. Issue
  `workflows-audit-failed-track-b-conforman_fb119cc2` cause (2) stays open on
  the owner.
- It does not merge anything. Both entries stay `in-progress` until a human
  approves the PR and the merge commit is recorded (PROCESS.md §6 steps 6–7).
- Editing an entry's `status` and normalising its fields into the form
  `process.yaml → definitions.entry` requires is not a violation of the
  append-only invariant: `status` is explicitly mutable (`close_issue` writes
  it), and the identity fields `id` and `summary` of the first entry were not
  touched — its id still recomputes to `fb119cc2`.

---

## workflows-audit-is-a-reserved-name-carry_1ec09cf6

| Field | Value |
|---|---|
| **id** | `workflows-audit-is-a-reserved-name-carry_1ec09cf6` |
| **summary** | Workflows/Audit is a reserved name carrying one sentence and no implementation, and the auditing capability it named has now been built elsewhere, so the empty name leaves the repository ambiguous about where auditing lives |
| **outcome** | The repository holds a tool directory that conforms to every convention and does nothing, next to a package that does the work — a reader looking for "the audit tool" finds the wrong one first |
| **cause** | The directory was created as a reserved name and never implemented; separately, "audit" names three unrelated capabilities in the system this repo serves, so no single implementation could have honoured the name |
| **iteration** | Retire Workflows/Audit at v1.1.0: keep the directory as a signpost whose Tooling document records that the name is retired and where the capability went, and author no workflow logic for it |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#retire-workflows-audit-at-v1-1-0-keep-th_add8a5e2`](CHANGE_LOG.md#retire-workflows-audit-at-v1-1-0-keep-th_add8a5e2), fix-version `v1.1.0` |
| **occurrences** | 1 — raised 2026-09-03, when the host-integrity capability was built as `Packages/Sentinel` |

**Why `in-progress` and not `resolved`.** `merge_commit` is empty in the cited
change entry: the work sits unmerged on branch `feat/packages-sentinel`. It moves
to `resolved` at PROCESS.md §6 step 7, on merge.

### Outcome (X) — what the gap resulted in

The 2026-09-01 conformance work left this directory fully conformant and
completely inert, and PROCESS.md recorded the result plainly:

> `Workflows/Audit` and `Workflows/Review` are one sentence each. Both conform.
> Neither is useful. What they are meant to be is not written down anywhere in
> this repository.

Conformance had made the emptiness *legible*, which was the point — but legible
emptiness sitting under the most obvious name still misdirects. The
[`v1.0.0` issue](#workflows-audit-failed-track-b-conforman_fb119cc2) closed the
documentation gap and explicitly left the capability question open for an owner
decision. This entry is that decision.

### Cause (Y) — the mechanism

Two causes, and only the second is interesting.

1. The directory was created as a reserved name and no implementation followed.
2. **"Audit" was never one capability.** It named host integrity sweeping,
   app-surface security review, and PROCESS.md conformance — three unrelated
   things with three different shapes. Any implementation placed here would have
   claimed a name the other two also answer to. The name could not be filled in
   correctly, only occupied.

### Iteration (Z) — the retirement

`v1.1.0` records the retirement in `Tooling/v1.1.0/WORKFLOW.md` and points at
[`Packages/Sentinel`](../../Packages/Sentinel), where the host-integrity
capability was built. `v1.0.0` is untouched and remains the rollback point. The
directory is not deleted: the record of a reserved name that was never built is
the finding that produced this entry.
