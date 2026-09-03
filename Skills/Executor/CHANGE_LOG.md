# Change log — Skills/Executor

Every iteration made in response to an issue in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), each citing the issue it resolves
(PROCESS.md §3).

Ids follow `process.yaml` → `definitions.change-id`: `<description>_<hash8>`,
hashed over the `iteration` field alone.

| Id | Iteration | Resolves | Version |
|---|---|---|---|
| [rename-the-placeholder-to-readme-md-and_2049c2a8](#rename-the-placeholder-to-readme-md-and_2049c2a8) | Rename the placeholder and write the real README | [the-executor-placeholder-was-committed-a_e6332913](KNOWN_ISSUES.md#the-executor-placeholder-was-committed-a_e6332913) | `v1.0.0` |
| [report-approval-as-defer-rather-than-pas_5c19c849](#report-approval-as-defer-rather-than-pas_5c19c849) | Approval reports DEFER, never PASS | [process-gate-cannot-enforce-the-approval_de559760](KNOWN_ISSUES.md#process-gate-cannot-enforce-the-approval_de559760) | `v1.0.0` |

Both carry an empty `merge_commit`: the work is on branch `feat/skills-executor`
and has not merged. PROCESS.md §6 step 7 fills these in and moves the issues to
`resolved`.

---

## rename-the-placeholder-to-readme-md-and_2049c2a8

| Field | Value |
|---|---|
| **id** | `rename-the-placeholder-to-readme-md-and_2049c2a8` |
| **resolves** | [`KNOWN_ISSUES.md#the-executor-placeholder-was-committed-a_e6332913`](KNOWN_ISSUES.md#the-executor-placeholder-was-committed-a_e6332913) |
| **iteration** | Rename the placeholder to README.md and write the tool's real README in the same change |
| **expected_result** | `Skills/Executor` passes Track B canonical-files: all five of §3 exist and are non-empty, and no file named `README` without an extension remains |
| **change** | `Skills/Executor/README` deleted; `Skills/Executor/README.md` written with the tool's documentation. The other four canonical files created in the same change |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because the GitHub web UI writes a bare `README` when it
creates a folder (cause Y), the tool was non-conformant from the moment it
existed and every relative link into it pointed at a missing file (outcome X).
Iteration Z renames it and writes the real documentation in the same change, so
the tool is never in a state where a placeholder is its README.

**Evidence.** `Tests/v1.0.0/RESULTS.md` records the Track B check: five canonical
files present and non-empty, reciprocity resolving in both directions.

---

## report-approval-as-defer-rather-than-pas_5c19c849

| Field | Value |
|---|---|
| **id** | `report-approval-as-defer-rather-than-pas_5c19c849` |
| **resolves** | [`KNOWN_ISSUES.md#process-gate-cannot-enforce-the-approval_de559760`](KNOWN_ISSUES.md#process-gate-cannot-enforce-the-approval_de559760) |
| **iteration** | Report approval as DEFER rather than PASS, and state in the conformance table that the check is reported and never enforced |
| **expected_result** | The approval check never returns PASS under any input, and both the prose §11 and the README say the check is reported and not enforced |
| **change** | `bin/process-gate` — the `approval` check is added unconditionally as `DEFER` with its reason; `templates/EXECUTOR_PROCESS.md.template` §11 carries the paragraph explaining why it is absent from the enforceable table; `README.md` caveat 1. Pinned by `Checks.test_approval_always_defers` |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because branch protection is unavailable on a free private
repo (cause Y), a conformance table listing approval alongside six mechanical
checks would assert review that nothing enforces (outcome X). Iteration Z reports
the check as deferred with its reason attached, which is the same rule INV-5
applies to test results turned on the gate's own output: an unanswerable check is
recorded as unanswered, never as passed.

**Evidence.** `Tests/v1.0.0/run-tests.log` — `test_approval_always_defers`
asserts `DEFER` for an otherwise fully-conformant T1 change.
