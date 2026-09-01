# Known issues — Sprint

Every issue found with this tool, each citing the iteration that addressed it in
[`CHANGE_LOG.md`](CHANGE_LOG.md).

**Append-only** (PROCESS.md §5.1). Entries are never rewritten; a fix appends,
carrying the version of the iteration that resolved it.

| ID | Summary | Status |
|---|---|---|
| [workflows-sprint-failed-track-b-conforma_e81c9e76](#workflows-sprint-failed-track-b-conforma_e81c9e76) | Track B conformance failure found on first touch | in-progress |

---

<a name="workflows-sprint-failed-track-b-conforma_e81c9e76"></a>
## workflows-sprint-failed-track-b-conforma_e81c9e76

- **id:** `workflows-sprint-failed-track-b-conforma_e81c9e76`
- **summary:** Workflows/Sprint failed Track B conformance: four canonical documents missing, code not under Tooling/, no recorded results under Tests/, and README named no version
- **source:** PROCESS.md §7 Track B, run on first touch of this tool (§9, "on next touch")
- **occurred_at:** 2026-08-31
- **tool:** `Workflows/Sprint`
- **status:** in-progress
- **status_note:** the fix is written and committed on branch `smoke/fix-workflows-sprint`,
  not merged to `main`. `merge_commit` on the change entry is therefore empty, and
  `resolved` may not be written while it is (`process.yaml: definitions.issue-status`).
  The PR and the merge are the owner's gate (PROCESS.md §8).
- **resolved_by:** [`CHANGE_LOG.md#conform-the-tool-at-v1-0-0-per-process-m_a832777d`](CHANGE_LOG.md#conform-the-tool-at-v1-0-0-per-process-m_a832777d), version `v1.0.0`
- **occurrences:** 1 — 2026-08-31, found by conformance sweep

### outcome — what the failure resulted in

Four of the five Track B checks failed. Measured before any change:

| Check | Result | Detail |
|---|---|---|
| Canonical files | **FAIL** | Only `README.md` existed. `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and `CHANGE_LOG.md` were all absent. |
| Reciprocity | **N/A** | Vacuous — with no `IMPLEMENTATIONS.md`/`TEMPLATES.md`/`KNOWN_ISSUES.md`/`CHANGE_LOG.md` there were no entries to cross-cite. |
| Code layout | **FAIL** | `agents/`, `commands/`, `docs/` and `fleet-kit/` sat directly at the tool root; no `Tooling/` directory existed. |
| Test layout | **FAIL** | No `Tests/` directory. No recorded output from any run existed anywhere in the tool. |
| Version agreement | **FAIL** | `README.md` named no version at all, and there was no `Tooling/` directory or `CHANGE_LOG.md` entry to agree with it. |

The observable effect: the tool was unversioned and unrollbackable. There was no
released version directory to serve as the rollback point PROCESS.md §5
safeguard 1 requires, no record of how it is applied beyond a prose README, and
nothing to make staleness visible — the exact failure §1 of PROCESS.md exists to
prevent. The README's smoke-test claim ("base 17/17 · hardenings 17/17 · live
triage 10/10 · addrow+doctor 14/14 · triage-guard 14/14 · hardened-triage 4/4")
was unverifiable, because neither the test code nor its output was in the repo.

### cause — why it happened

`Workflows/Sprint` predates PROCESS.md. It was imported from `operand-packages`
(this repo's v1.0, PROCESS.md §1) as a flat drop of its working directory, and
the conventions in §3 and §4 were written afterwards. No mechanism has ever run
Track B against imported tools, so the gap persisted silently rather than being
caught — it is listed as an open row in the PROCESS.md §9 migration backlog, and
this is the first touch of the tool since that backlog was written.

### iteration — what was planned to resolve it

Bring the tool into Track B conformance at `v1.0.0` per PROCESS.md §9, without
changing behaviour: move the implementation under `Tooling/v1.0.0/`, create the
four missing canonical documents, record an actual verification attempt under
`Tests/v1.0.0/`, and state the version in `README.md`. Recorded as
[`CHANGE_LOG.md#conform-the-tool-at-v1-0-0-per-process-m_a832777d`](CHANGE_LOG.md#conform-the-tool-at-v1-0-0-per-process-m_a832777d).

### residual — not closed by this iteration

**This tool has no test suite.** There is no `run-tests.sh`, no `tests/`
directory, no `Makefile` and no `package.json` — at the old root or the new
version directory — so nothing could be run and nothing green could honestly be
recorded. `Tests/v1.0.0/RESULTS.md` therefore records **NOT TESTED**, names the
five Track-B checks run in its place (all five pass) and keeps a `bash -n` syntax
parse of the four shell scripts explicitly labelled *not a test*. Writing a real
suite is future work; it is a separate issue and is not covered by this entry.

Amended PROCESS.md §5.5 and §8 (decisions 9 and 10) make this mergeable: the
requirement is **recorded evidence**, not test files, and a recorded Track-B
conformance result satisfies it for a code-less tool. What is still *not*
established is that the tool works — `RESULTS.md` §5 states that limit directly,
and the README's smoke-test counts remain an unverifiable claim because neither
that test code nor its output is in this repository.
