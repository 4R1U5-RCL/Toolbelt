# Test results — Workflows/Review v1.0.0

**Verdict: NO EXECUTABLE SUITE EXISTS. Track-B conformance was run in its place,
and it PASSES on all five checks.**

`Workflows/Review` ships no program, so there is nothing to execute and no
executable test was run. That is recorded here as the fact it is — never as a
pass (PROCESS.md §5 invariant 6). Under §4's code-less rule and §5 invariant 5
as amended (§10 decisions 9 and 10), the recorded Track-B result below **is** the
evidence this tool's PR needs. A code-less tool is not unmergeable for want of a
suite it cannot have.

| Field | Value |
|---|---|
| Tool | `Workflows/Review` |
| Version | `v1.0.0` |
| Branch | `smoke/fix-workflows-review` |
| Run at | 2026-09-01 (UTC) |
| Executable suite | **none exists** — no `run-tests.sh`, no `tests/`, no source file of any kind |
| Executable result | **not run** — there is nothing to run |
| Evidence run in its place | PROCESS.md §7 Track B, all five checks |
| Track-B verdict | **PASS (5/5)** |
| Raw transcript | [`track-b-checks.log`](track-b-checks.log) |

## Part 1 — establishing that no suite exists

Three probes, recorded verbatim in the transcript: no `run-tests.sh` at the tool
root or under `Tooling/v1.0.0/`; no `tests/` directory in either place; and a
`find` for `*.py *.sh *.ts *.js *.rb *.go` across the whole tool returning
nothing. The tool contains no executable file.

## Part 2 — the Track-B checks run in its place

| # | Check (PROCESS.md §7) | Result | What was observed |
|---|---|---|---|
| 1 | Canonical files | **PASS** | All five of §3 exist at the tool root and are non-empty |
| 2 | Reciprocity | **PASS** | Both `KNOWN_ISSUES.md` entries cite their `CHANGE_LOG.md` counterpart and both are cited back. Neither is `legacy`, so the §9 exemption applies to neither. `IMPLEMENTATIONS.md` and `TEMPLATES.md` hold zero entries each — see the honesty note below |
| 3 | Code layout | **PASS in form** | `Tooling/v1.0.0/REVIEW.md` is the document that constitutes the tool (§4 code-less rule). No marker file. See the substance note below |
| 4 | Test layout | **PASS** | `Tests/v1.0.0/` holds this file and `track-b-checks.log` |
| 5 | Version agreement | **PASS** | `README.md` says `v1.0.0`, the newest `Tooling/` directory is `v1.0.0`, and the newest `CHANGE_LOG.md` entry records `v1.0.0` |

## Part 3 — vocabulary, heading form, ids, branch claims

| Check | Result | What was observed |
|---|---|---|
| Entry heading form | **PASS** | Every level-2 heading in `KNOWN_ISSUES.md` and `CHANGE_LOG.md` matches `^## [a-z0-9]+(-[a-z0-9]+)*_[0-9a-f]{8}$`. No standalone `<a name>` tags remain |
| Status vocabulary | **PASS** | Both statuses read `in-progress`; nothing falls outside the closed set of seven |
| `resolved` with empty `merge_commit` | **PASS** | No status reads `resolved`. Both `merge_commit` fields are empty, and both issues are `in-progress` accordingly |
| Branch claims | **PASS** | Every branch claim in the tool names `smoke/fix-workflows-review`. The round-1 sentence "No branch was created" survives only as a quotation inside the defect record |
| Id reproduction | **PASS (4/4)** | Each id recomputed with `sha256sum` over its canonicalised identity field — `summary` for issue-ids, `iteration` for change-ids |

Recomputed ids, first 8 hex of `sha256`:

| Entry | Identity field | Reproduces as |
|---|---|---|
| issue 1 | `summary` | `workflows-review-fails-track-b-conforman_0b0b4b59` — unchanged from the migration |
| issue 2 | `summary` | `workflows-review-v1-0-0-migration-output_d18c44d1` — new entry |
| change 1 | `iteration` | `create-the-process-md-section-3-document_cddfd0f4` — **moved**, was `migrate-workflows-review-to-the-track-b_abb4adaf` |
| change 2 | `iteration` | `repair-the-workflows-review-v1-0-0-migra_23ca8994` — new entry |

## Two things this result does not claim

**Check 2 passes vacuously on one pair.** `IMPLEMENTATIONS.md` and `TEMPLATES.md`
have zero entries, so no entry there can fail reciprocity — but neither is
anything demonstrated to work. That is stated as vacuity rather than dressed up
as a pass, and the check's wording was not narrowed to reach it. Nothing was
invented to populate either file, because the tool has no use case and no
template to record.

**Check 3 passes in form, not in substance.** `Tooling/v1.0.0/REVIEW.md` holds
the document that constitutes the tool, which is what §4 requires of a code-less
tool — and that document records a single sentence, because a single sentence is
all the review workflow has ever had written about it. The layout conforms. The
workflow does not exist. Those are different statements and this file makes both.

## Note on the superseded log

The migration recorded `run-tests.log`, which has been replaced by
`track-b-checks.log`. Two reasons, both recorded in
[`../../CHANGE_LOG.md#repair-the-workflows-review-v1-0-0-migra_23ca8994`](../../CHANGE_LOG.md#repair-the-workflows-review-v1-0-0-migra_23ca8994):
it captured a `python3 -m unittest discover` over an empty directory — a `Ran 0
tests ... OK` that corroborates nothing, exactly the vacuous green
`process.yaml` `branches.test_decision` warns about — and its closing directory
listing no longer matched the tree. Nothing true was discarded: the new
transcript re-runs the same absence probes and records the result of every one.

## One thing this result cannot settle — escalated, not decided

`process.yaml` `branches.test_decision` was **not** amended alongside PROCESS.md
§5.5 and §8. It still reads:

> test: "`./run-tests.sh` exits 0 AND the suite includes an end-to-end test that
> exercises the logged failure" … on_unknown: escalate # suite crashed, timed
> out, never ran

Taken literally, a code-less tool can only ever reach `on_unknown` there, and
`on_unknown` escalates — which is exactly the deadlock §10 decision 10 was
settled to remove. PROCESS.md §5 invariant 5 and §8 now say plainly that a
recorded Track-B conformance result is the evidence, and this document is that
result; but PROCESS.md's own preamble says `process.yaml` is authoritative where
the two disagree.

This result is recorded on the §5.5/§8 reading, because that is the reading §10
decisions 9 and 10 were adopted to produce. The conflict itself is **not**
resolved here and is not logged as an issue against this tool — it is a gap in
the spec, not in `Workflows/Review`, and the fix belongs in `process.yaml`. It is
escalated to the owner as the one open question this run could not answer.
