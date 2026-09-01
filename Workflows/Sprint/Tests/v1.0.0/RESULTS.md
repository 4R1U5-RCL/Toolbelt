# Test results — Workflows/Sprint v1.0.0

## Outcome: NOT TESTED — no executable suite exists. Track-B conformance run in its place: ALL FIVE PASS

**Run at:** 2026-09-01T04:37:37Z (UTC)
**Run from:** `Workflows/Sprint/` (tool root)
**Branch:** `smoke/fix-workflows-sprint`
**Captured output:** [`run-tests.log`](run-tests.log) — verbatim, unedited
**Checker used:** [`trackb-check.py`](trackb-check.py) (kept beside the output so a
human can re-run it and confirm; it is a Track-B conformance checker, **not** this
tool's test suite, and it is deliberately not under `Tooling/` because it is not
part of what the tool ships)

This supersedes the 2026-08-31 record, which captured the same "no suite" finding
but did not name the Track-B checks run in its place, as PROCESS.md §4 requires
for a code-less tool.

## 1. Executable suite — there is none

This tool ships `agents/`, `commands/`, `docs/` and `fleet-kit/` under
`Tooling/v1.0.0/`. There is:

- no `run-tests.sh` — searched the whole tool, at the old root and the new
  version directory;
- no `tests/` directory (PROCESS.md §4's expected home for test code);
- no `Makefile` and no `package.json`.

**Nothing could be run, so no green result is recorded.** That is the literal
finding, per invariant 6 (never falsify a test result). PROCESS.md §4 covers this
case explicitly: a tool that *is* its documentation is not exempt from the layout,
and its `RESULTS.md` records that no executable suite exists and names the
Track-B checks run in its place. Those checks are §2 below. No marker file was
invented.

## 2. Track-B conformance — the evidence run in place of a suite

PROCESS.md §7 Track B, five checks, run against the tool as it stands on this
branch. Verbatim output in [`run-tests.log`](run-tests.log) STEP 2.

| Check | Result | What was actually verified |
|---|---|---|
| Canonical files | **PASS** | `README.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md`, `CHANGE_LOG.md` all exist at the tool root and are non-empty. |
| Reciprocity | **PASS** | 1 `KNOWN_ISSUES` entry ↔ 1 `CHANGE_LOG` entry, citing each other by id; 5 `IMPLEMENTATIONS` entries ↔ 6 `TEMPLATES` entries, every entry on each side citing at least one id on the other. Entries were located by the §13/`definitions.entry` rule — a level-2 heading whose text is the bare id — and **every** level-2 heading in all four documents is a bare id, so no entry was skipped by the parser. No entry here is `legacy`; none was exempted. |
| Code layout | **PASS** | All implementation files sit under `Tooling/v1.0.0/`; nothing but the five canonical documents, `Tooling/` and `Tests/` remains at the tool root. |
| Test layout | **PASS** | `Tests/v1.0.0/` exists and holds recorded results for the current version (`RESULTS.md`, `run-tests.log`, `trackb-check.py`). Read the check honestly: it asks that *results are recorded*, and this document records them. It does **not** assert that a suite ran — §1 above records that none exists. |
| Version agreement | **PASS** | `README.md` names `v1.0.0`; the newest (and only) `Tooling/` directory is `v1.0.0`; the newest `CHANGE_LOG.md` entry names `v1.0.0`. |

## 3. Identity checks — the ids reproduce

Run because the previous record shipped a change-id that reproduced from nothing.
Verbatim output in [`run-tests.log`](run-tests.log) STEP 3–4.

| Id | Canonical string hashed | Digest (first 8) | Verdict |
|---|---|---|---|
| change-id | ``conform the tool at `v1.0.0` per process.md §9 without touching behaviour`` | `a832777d` | reproduces — entry corrected to `conform-the-tool-at-v1-0-0-per-process-m_a832777d` |
| issue-id | `workflows/sprint failed track b conformance: four canonical documents missing, code not under tooling/, no recorded results under tests/, and readme named no version` | `e81c9e76` | reproduces — `workflows-sprint-failed-track-b-conforma_e81c9e76` was already correct, unchanged |

Both descriptions are the same canonical string through `slug_rule`; both hit the
40-character truncation and neither left a trailing hyphen to strip. The retired
id `..._695ac22d` has no heading, no anchor, no `id` field and no link anywhere —
grep for it in a citing position returns nothing (`run-tests.log` STEP 4). It
survives only as quoted prose in the `CHANGE_LOG.md` note that retires it, and in
this sentence.

## 4. Fallback sanity check — NOT a test

`bash -n` parse of the four shipped shell scripts from their location under
`Tooling/v1.0.0/`:

```
Tooling/v1.0.0/fleet-kit/fleet-board.sh: syntax OK
Tooling/v1.0.0/fleet-kit/fleet-doctor.sh: syntax OK
Tooling/v1.0.0/fleet-kit/fleet-mbox.sh: syntax OK
Tooling/v1.0.0/fleet-kit/fleet-triage-guard.sh: syntax OK
```

`bash --version`: GNU bash, version 5.2.15(1)-release (x86_64-pc-linux-gnu)

**A syntax check is not a test.** It establishes only that the four scripts parse
from their new location. No behaviour of `fleet-mbox`, `fleet-board`,
`fleet-doctor` or `fleet-triage-guard` was exercised.

## 5. What this does and does not establish

**Establishes:** the tool is Track-B conformant at `v1.0.0`; both ids reproduce
from their identity fields; the four scripts parse; and no script in this tool
resolves a sibling by relative path — each takes its target from an argument
(`<WT>`) or the environment (`FLEET_ROOT`, `FLEET_SESSION`), verified by reading
every script, so the move into `Tooling/v1.0.0/` could not have broken an
internal path.

**Does not establish:** that the tool works. There is no evidence in this
repository that `/fleet` spins up a sprint, that the mailbox delivers, that the
board writes atomically, or that the triage guard blocks a write.

## 6. Standing gap

`README.md` claims a smoke-test history — "base 17/17 · hardenings 17/17 · live
triage 10/10 · addrow+doctor 14/14 · triage-guard 14/14 · hardened-triage 4/4".
**None of that test code is in this repository**, and no output from those runs
was ever recorded. Those numbers are unverifiable here; the README now labels
them a claim rather than evidence. Recovering or rewriting that suite is future
work, recorded as residual on the `KNOWN_ISSUES.md` entry — it is a separate
issue and is not closed by this iteration.
