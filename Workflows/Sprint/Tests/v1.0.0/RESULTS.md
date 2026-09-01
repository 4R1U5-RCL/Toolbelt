# Test results — Workflows/Sprint v1.0.0

## Outcome: NOT TESTED — no test suite exists

**Run at:** 2026-08-31T15:24:15Z (UTC)
**Run from:** `Workflows/Sprint/` (tool root), after the code was moved to `Tooling/v1.0.0/`
**Captured output:** [`run-tests.log`](run-tests.log)

## What was attempted

1. Looked for a `run-tests.sh` — **there is none**, at the tool root or anywhere
   under `Tooling/v1.0.0/`.
2. Looked for a `tests/` directory to run directly (per PROCESS.md §4) —
   **there is none**. This tool has never shipped test code.
3. With no runner available, the only executable verification possible was a
   `bash -n` syntax parse of the four shipped shell scripts, to confirm the move
   into `Tooling/v1.0.0/` left them intact.

## Verbatim outcome

```
$ find . -name 'run-tests.sh' -o -type d -name tests
(no output above = neither a run-tests.sh nor a tests/ directory exists)

=== FALLBACK: bash -n syntax check of the shipped scripts (NOT a test suite) ===
Tooling/v1.0.0/fleet-kit/fleet-board.sh: syntax OK
Tooling/v1.0.0/fleet-kit/fleet-doctor.sh: syntax OK
Tooling/v1.0.0/fleet-kit/fleet-mbox.sh: syntax OK
Tooling/v1.0.0/fleet-kit/fleet-triage-guard.sh: syntax OK
```

`bash --version`: GNU bash, version 5.2.15(1)-release (x86_64-pc-linux-gnu)

## What this does and does not establish

**Establishes:** all four shell scripts parse cleanly from their new location,
and no script in this tool resolves a sibling path relatively — each takes its
targets from arguments (`<WT>`) or environment (`FLEET_ROOT`, `FLEET_SESSION`),
so the move could not have broken an internal path. That was verified by reading
every script, not inferred.

**Does not establish:** that the tool works. A syntax check is not a test. No
behaviour of `fleet-mbox`, `fleet-board`, `fleet-doctor` or `fleet-triage-guard`
was exercised.

## Standing gap

`README.md` claims a smoke-test history — "base 17/17 · hardenings 17/17 · live
triage 10/10 · addrow+doctor 14/14 · triage-guard 14/14 · hardened-triage 4/4".
**None of that test code is in this repository**, and no output from those runs
was ever recorded. Those numbers are therefore unverifiable here; they are
reproduced as a claim in the README, not as evidence. Recovering or rewriting
that suite is future work and is recorded in `KNOWN_ISSUES.md`.
