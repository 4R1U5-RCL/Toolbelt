# Change log — Skills/Memory

One entry per iteration made in response to an entry in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Fields are those `process.yaml` defines
under `change-entry`; ids follow the same `<description>_<hash8>` rule as issue
ids.

---

<a name="migrated-skills-memory-to-the-tooling-v1_16012fef"></a>
## `migrated-skills-memory-to-the-tooling-v1_16012fef` — v1.0.0

| Field | Value |
|---|---|
| **id** | `migrated-skills-memory-to-the-tooling-v1_16012fef` |
| **summary** | Migrated Skills/Memory to the Tooling/v1.0.0 and Tests/v1.0.0 layout and created the four missing canonical documents |
| **resolves** | [`KNOWN_ISSUES.md#skills-memory-failed-track-b-conformance_6cdef98b`](KNOWN_ISSUES.md#skills-memory-failed-track-b-conformance_6cdef98b) |
| **version** | `v1.0.0` — **no bump.** The code did not change, it moved. PROCESS.md §9: a tool that has never been versioned starts at `v1.0.0`, and its current code becomes `Tooling/v1.0.0/` |
| **merge_commit** | not yet merged — this change was prepared on a working tree; all git operations (branch, commit, PR, merge) are performed by the orchestrator, not by this run |
| **date** | 2026-08-31 |

### Cause (Y)

`Skills/Memory` predates PROCESS.md §3/§4. It was authored as a flat package —
`README.md`, `templates/`, `tests/` — under the earlier `operand-packages`
convention and carried into this repo unchanged, and no §6 fix procedure had
ever run against it to bring it into conformance.

### Outcome (X)

The tool failed four of the five Track B checks: only one of the five canonical
documents existed, the code sat at the tool root instead of under `Tooling/`,
nothing under `Tests/` recorded any run, and `README.md` named no version. With
no recorded version and no rollback point, the tool could not release a new
version and its staleness was invisible.

### Iteration (Z)

A conformance-only migration at `v1.0.0`: relocate the code and test code into
`Tooling/v1.0.0/`, run and record the existing suite under `Tests/v1.0.0/`, and
author the four missing canonical documents from what is actually in the tool.

### Expected result (V)

Checkably, after this change:

- All five canonical files exist at the tool root and are non-empty.
- `Tooling/v1.0.0/` holds `templates/` and `tests/`; nothing but the five `.md`
  files, `Tooling/` and `Tests/` remains at the tool root.
- `Tooling/v1.0.0/tests/verify.sh` runs from its new location and exits 0.
- `Tests/v1.0.0/` holds the verbatim output of that run.
- `README.md`, the newest `Tooling/` directory and this entry all name `v1.0.0`.
- Every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` anchor and vice versa;
  this entry and its issue cite each other.

### Change (W) — what changed, where, how it was verified

| What | Where | Verification |
|---|---|---|
| `templates/` and `tests/` relocated | → `Tooling/v1.0.0/templates/`, `Tooling/v1.0.0/tests/` | `find` over the tool directory; tool root now holds only the five `.md` files plus `Tooling/` and `Tests/` |
| Path repair after the move | none was required | `verify.sh` resolves its own directory from `BASH_SOURCE` and reads templates as `$PKG/templates/` where `PKG="$HERE/.."`; moving `tests/` and `templates/` together preserved that. `mem_tool.py` does no `sys.path` manipulation and takes every path as an argument |
| Test results recorded | `Tests/v1.0.0/run-tests.log`, `Tests/v1.0.0/RESULTS.md` | Captured verbatim: `== memory smoke: 18 passed, 0 failed ==`, `exit=0`. Identical before the move, after the move from `Tooling/v1.0.0/`, and from the tool root |
| `TEMPLATES.md` created | tool root | Documents the two real files in `Tooling/v1.0.0/templates/`, quoted verbatim; each cites its `IMPLEMENTATIONS.md` anchor |
| `IMPLEMENTATIONS.md` created | tool root | Three implementations derived from `README.md` and the files present; each cites a `TEMPLATES.md` anchor |
| `KNOWN_ISSUES.md` created | tool root | Header plus the first entry, `…_6cdef98b`, citing this change |
| `CHANGE_LOG.md` created | tool root | This file; this entry cites that issue |
| `README.md` updated | tool root | Adds a "Current version: `v1.0.0`" line; repoints the two `templates/…` rows and the `bash tests/verify.sh` self-check line at `Tooling/v1.0.0/`. No other prose changed |

### Deviations from §6 to note

This run executed the iteration directly on the working tree. It did **not**
create a branch, seed a next version directory, open a PR or merge — steps 3, 5
and 6 of §6 — because the code did not change and all git operations are the
orchestrator's. Consequently the issue entry remains `open`; it closes when the
merge is recorded (§6 step 7).
