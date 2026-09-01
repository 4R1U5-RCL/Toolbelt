# Known issues — Workflows/Audit

Every issue found with this tool, each citing the iteration that addressed it in
[`CHANGE_LOG.md`](CHANGE_LOG.md) (PROCESS.md §3).

**Append-only** (PROCESS.md §5.1). Entries are never edited or removed; a fix
appends a new entry carrying the version that resolved it. Ids follow
`process.yaml` → `definitions.issue-id`: `<description>_<hash8>`.

**Note on history.** This file was created on 2026-08-31 by the entry below,
which is therefore the first entry in it. No earlier issue history was
reconstructed, because none was recorded and none is recoverable from the
repository — the tool consisted of a single README.

| Id | Summary | Status |
|---|---|---|
| [workflows-audit-failed-track-b-conforman_fb119cc2](#workflows-audit-failed-track-b-conforman_fb119cc2) | Failed Track B conformance: four of five canonical documents missing, no `Tooling/` or `Tests/`, no version, no implementation | open |

---

<a name="workflows-audit-failed-track-b-conforman_fb119cc2"></a>
## workflows-audit-failed-track-b-conforman_fb119cc2

| Field | Value |
|---|---|
| **id** | `workflows-audit-failed-track-b-conforman_fb119cc2` |
| **summary** | Workflows/Audit failed Track B conformance: four of five canonical documents missing, no Tooling/ or Tests/ directories, README states no version and no implementation exists |
| **status** | open — the document half of the iteration is executed on this branch; it closes on merge per PROCESS.md §6 step 7. The implementation half cannot be executed at all (see *Honest limits*) |
| **resolved_by** | [`CHANGE_LOG.md#brought-workflows-audit-into-track-b-con_be1c5a4b`](CHANGE_LOG.md#brought-workflows-audit-into-track-b-con_be1c5a4b), fix-version `v1.0.0` |
| **occurrences** | 1 — detected 2026-08-31 during the Track B sweep recorded in PROCESS.md §9 |

**Id derivation.** `hash8` = first 8 hex chars of
`sha256("workflows/audit failed track b conformance: four of five canonical documents missing, no tooling/ or tests/ directories, readme states no version and no implementation exists")`
— the summary, trimmed, lowercased, whitespace runs collapsed to one space — =
`fb119cc2`. `description` = that same summary slugified per
`process.yaml → slug_rule` and truncated to 40 characters.

### Outcome (X) — what the failure resulted in

The tool cannot release a version: PROCESS.md §7 blocks a Track B failure until
it is logged and fixed. Measured at the tool root on 2026-08-31, all five checks
of the §7 Track B table are involved:

| Check | Result | What was actually found |
|---|---|---|
| Canonical files | **failed** | `README.md` present and non-empty (41 bytes, one sentence). `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md`, `CHANGE_LOG.md` — **all four missing** |
| Reciprocity | **vacuous** | With no `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` or `CHANGE_LOG.md` there were no entries on any side to cite or fail to cite |
| Code layout | **failed, vacuously** | No `Tooling/` directory existed — and no code existed to put in one. The tool directory contained exactly one file: `README.md` |
| Test layout | **failed** | No `Tests/` directory, no recorded results, and no `run-tests.sh` or `tests/` to produce any. The tool's test state was unknowable from the repository, and remains untestable |
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
genuinely exists, establish the `Tooling/v1.0.0/` and `Tests/v1.0.0/` version
anchors, record the verbatim result of attempting to test the tool (nothing
runnable exists), and state `v1.0.0` in the README. No code is written and no
version is bumped — nothing was moved, because there was nothing to move.
Planned and recorded in
[`CHANGE_LOG.md#brought-workflows-audit-into-track-b-con_be1c5a4b`](CHANGE_LOG.md#brought-workflows-audit-into-track-b-con_be1c5a4b).

### Honest limits — what this entry does not fix

This iteration closes cause (1) and **cannot** close cause (2). After it:

- The tool still has no implementation, so `IMPLEMENTATIONS.md` and
  `TEMPLATES.md` remain empty-but-valid rather than useful.
- `Tests/v1.0.0/` records a **NOT RUN** verdict, not a pass — there is no suite
  to run, and PROCESS.md §5.6 forbids recording it as anything else.
- `Tooling/v1.0.0/` holds a note explaining an absence, not code. The code-layout
  check is therefore vacuous, not passed.

Writing the audit workflow is a separate piece of work needing the one input the
repository does not contain: what this workflow is supposed to do. That input is
an owner decision, not something an agent can derive, and it is the reason this
entry's status is `open` rather than closed by its own iteration.

**Still your job.** Decide what `Workflows/Audit` is meant to be — or record
that the folder should be removed. Until then this tool is a reserved name, and
anyone reaching for it should know that before they reach.
