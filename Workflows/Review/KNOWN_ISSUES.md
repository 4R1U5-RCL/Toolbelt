# Known issues — Workflows/Review

Every issue found with this tool. Append-only (PROCESS.md §5.1). Ids are computed
per `process.yaml` `definitions.issue-id`; each entry cites the
[`CHANGE_LOG.md`](CHANGE_LOG.md) entry that resolves it.

| id | Summary | Status |
|---|---|---|
| [`workflows-review-fails-track-b-conforman_0b0b4b59`](#workflows-review-fails-track-b-conforman_0b0b4b59) | Track B conformance failure found at migration | partially resolved |

---

<a name="workflows-review-fails-track-b-conforman_0b0b4b59"></a>
## `workflows-review-fails-track-b-conforman_0b0b4b59`

| Field | Value |
|---|---|
| **id** | `workflows-review-fails-track-b-conforman_0b0b4b59` |
| **summary** | Workflows/Review fails Track B conformance: four canonical documents missing, no Tooling/ or Tests/ directories, README names no version, and the tool has no implementation at all |
| **source** | PROCESS.md §7 Track B check run against `Workflows/Review` during the 2026-08-31 migration of this tool |
| **occurred_at** | 2026-08-31 |
| **tool** | `Workflows/Review` |
| **status** | partially resolved — the document layout is fixed at v1.0.0; the missing implementation is **not** fixed and remains open |
| **resolved_by** | [`CHANGE_LOG.md#migrate-workflows-review-to-the-track-b_abb4adaf`](CHANGE_LOG.md#migrate-workflows-review-to-the-track-b_abb4adaf) at fix-version **v1.0.0** — documents only |
| **occurrences** | 1 — 2026-08-31, the migration run |

**outcome (X).** Every Track B check of PROCESS.md §7 failed, and one of them
cannot be made to pass by a migration at all:

| Check | Result before the migration |
|---|---|
| Canonical files | **FAIL** — only `README.md` existed. `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and `CHANGE_LOG.md` were all absent |
| Reciprocity | **FAIL (vacuous)** — none of the four files existed, so no pair could cite anything |
| Code layout | **FAIL** — no `Tooling/` directory. The deeper problem: there is no code anywhere in the tool to put under one |
| Test layout | **FAIL** — no `Tests/` directory, and no `tests/` or `run-tests.sh` to produce results from |
| Version agreement | **FAIL** — `README.md` named no version; there was no `Tooling/` directory and no `CHANGE_LOG.md` entry to agree with |

The observable effect: the tool announces itself as "the review workflow" and
supplies nothing a reader can use, run, or copy. Its staleness is invisible in
the exact way PROCESS.md §1 exists to prevent — there is no issue log to consult,
no change log to date it, and no recorded test result to contradict. Verbatim,
the entire tool was:

```
$ find . -mindepth 1
./README.md

$ cat README.md
This folder contains the review workflow.
```

**cause (Y).** Two distinct causes, and they are not the same failure:

1. *The document gap.* The directory was created — or transferred from
   `operand-packages` — as a placeholder and never taken through PROCESS.md §9's
   conformance step. The §3/§4 conventions postdate it, and nothing in the repo
   forced the gap shut: §9's backlog table records exactly this state for
   `Workflows/Review` (`README ✅`, all six other columns `❌`).
2. *The implementation gap.* No one has written the workflow. This is not drift
   away from a working tool and not a defect in one — there has never been code
   here to break. The single-sentence README is a stub that was never filled in.

Cause 1 is a missing migration. Cause 2 is missing work, and no migration can
close it.

**iteration (Z).** Bring the tool to the §3/§4 **document** layout at **v1.0.0**
per §9 ("a tool that has never been versioned starts at v1.0"): create the four
missing canonical documents stating honestly that no implementation, use case or
template exists; create `Tooling/v1.0.0/` and `Tests/v1.0.0/` recording the same;
and state `v1.0.0` in `README.md`. Explicitly **not** in scope: writing the review
workflow. Planned and recorded in
[`CHANGE_LOG.md#migrate-workflows-review-to-the-track-b_abb4adaf`](CHANGE_LOG.md#migrate-workflows-review-to-the-track-b_abb4adaf).

**What remains open after this iteration.** The Code-layout and Test-layout
checks of §7 still do not pass in substance: `Tooling/v1.0.0/` holds no code and
`Tests/v1.0.0/` holds no test output, because neither exists to hold. Under §7
this tool therefore still cannot release a new version on the strength of a
passing conformance run — the honest reading is that the *documents* now conform
and the *tool* does not yet exist. Closing that requires building the workflow
and its test, which is a new issue and a new iteration under §6, not this one.
