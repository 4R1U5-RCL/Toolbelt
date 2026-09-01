# Test results — Workflows/Audit v1.0.0

**Verdict: no executable test suite exists for this tool, and none can — it has
no program. The evidence recorded here in its place is a Track-B conformance
result, run 2026-09-01: all five checks pass.**

Read both halves of that sentence. This document is not a passing test suite and
must not be cited as one. It is what PROCESS.md §4 requires of a code-less tool —
a record that no executable suite exists, naming the Track-B checks run instead —
and what §5 invariant 5 and §8 now accept as the recorded evidence a PR needs.

| Field | Value |
|---|---|
| Tool | `Workflows/Audit` |
| Version | `v1.0.0` |
| Kind | Code-less tool (PROCESS.md §4) — the documents that constitute it are under [`../../Tooling/v1.0.0/`](../../Tooling/v1.0.0/) |
| Executable suite | **none exists.** No `run-tests.sh`, no `Tooling/v1.0.0/tests/`, no test file of any kind |
| Evidence in its place | Track-B conformance run, 2026-09-01T04:38:41Z, branch `smoke/fix-workflows-audit` at `51d7ae8` |
| Track-B verbatim log | [`track-b-2026-09-01.log`](track-b-2026-09-01.log) |
| Id recomputation log | [`id-recompute-2026-09-01.log`](id-recompute-2026-09-01.log) |
| Pre-migration capture | [`run-tests.log`](run-tests.log) — 2026-08-31T15:25:02Z |

## Track B — the five checks, run 2026-09-01

Commands and output are preserved verbatim in
[`track-b-2026-09-01.log`](track-b-2026-09-01.log). Nothing below is asserted
without a corresponding block in that file.

| # | Check (PROCESS.md §7) | Result | What was measured |
|---|---|---|---|
| 1 | Canonical files | **PASS** | All five exist and are non-empty: `README.md` 3517 B, `IMPLEMENTATIONS.md` 2464 B, `TEMPLATES.md` 1705 B, `KNOWN_ISSUES.md` 13271 B, `CHANGE_LOG.md` 14756 B |
| 2 | Reciprocity | **PASS** | Two issue entries and two change entries. Each issue id is cited once by `CHANGE_LOG.md`; each change id is cited twice by `KNOWN_ISSUES.md` (in `resolved_by` and in the iteration prose). `IMPLEMENTATIONS.md` and `TEMPLATES.md` hold **zero** entries each, so that pair passes vacuously — there is no uncited entry on either side. **No entry claims a `legacy` exemption**; the check was run at full strength on all four entries |
| 3 | Code layout | **PASS** | `find Tooling -type f` → `Tooling/v1.0.0/WORKFLOW.md`. What constitutes this tool sits under `Tooling/v<version>/` as §4 requires of a code-less tool. Everything outside it is one of the five canonical root documents, which belong at the root |
| 4 | Test layout | **PASS** | Recorded results exist under `Tests/v1.0.0/` for the current version: this file plus two verbatim logs |
| 5 | Version agreement | **PASS** | README says `v1.0.0`; newest `Tooling/` directory is `v1.0.0`; newest `CHANGE_LOG.md` entry names version `v1.0.0`. Three places, one version |

Two further conformance properties were measured in the same run:

| Property | Result | Measured |
|---|---|---|
| Status vocabulary | **PASS** | Both `status` values are `in-progress` — inside the closed set of seven (`process.yaml → definitions.issue-status`). No `resolved` is written: both change entries have an empty `merge_commit`, and the settled rule is that an approved-but-unmerged fix stays `in-progress` |
| Id reproducibility | **PASS** | All four ids recomputed from their identity fields with `sha256sum`, reading the field values out of the live files. All four reproduce their headings exactly — see [`id-recompute-2026-09-01.log`](id-recompute-2026-09-01.log) |

## What check 3 does and does not mean

The code-layout check passes **as written**. It does not mean the tool works.
`Tooling/v1.0.0/WORKFLOW.md` holds this workflow's complete authored substance,
and that substance is one sentence — *"This folder contains the audit
workflow."* — which names the workflow without describing it. The check asks
where the tool's constituting documents live, and they live in the right place.
It does not ask whether they say anything useful, and here they do not.

The gap is logged as
[`workflows-audit-failed-track-b-conforman_fb119cc2`](../../KNOWN_ISSUES.md) and
remains open on its second cause: nobody has written what this workflow is.

## The 2026-08-31 attempt to run a suite

Preserved for its evidential value in [`run-tests.log`](run-tests.log). Four
commands were run from the tool directory; all are verbatim in that file.

| Command | Outcome |
|---|---|
| `find . -type f` | one file: `./README.md`. Nothing else existed in the tool directory |
| `ls -la` | confirms the same |
| `./run-tests.sh` | `No such file or directory`, `exit_code=127` — there is no test runner |
| `ls tests/` | `No such file or directory`, `exit_code=2` — there is no test directory |
| `python3 -m unittest discover -v` | `Ran 0 tests in 0.000s / OK`, `exit_code=0` |

### Read the last line correctly

`python3 -m unittest discover` printed `OK` and exited `0`. **That is not a
passing suite.** It collected `Ran 0 tests` because there are no test files to
collect; an empty discovery is reported by Python as success regardless. It is
included as evidence that the directory is genuinely empty of tests, not as a
result. There is no green suite for this tool and no red one — there is no suite.

The same absence was re-confirmed on 2026-09-01: `ls run-tests.sh
Tooling/v1.0.0/tests` → `No such file or directory` for both, `exit_code=2`.

## When this document changes

If `Workflows/Audit` ever gains an implementation, it gains a real suite under
`Tooling/v<version>/tests/`, and `Tests/v<version>/RESULTS.md` for that version
records an actual run. Until then a Track-B result is the only honest evidence
this tool can produce, and PROCESS.md §8 is explicit that it is enough: *"A
code-less tool is never unmergeable for want of a suite it cannot have."*
