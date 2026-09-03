# Test results — Packages/Sentinel v1.0.0

Recorded evidence for `v1.0.0`, per PROCESS.md §4 and invariant 5. Every file
named here is the actual output of the run described, not a restatement of it.

**Declared runner:** `./run-tests.sh` (from `Tooling/v1.0.0/`) —
`python3 -m unittest discover -s tests -t .`, stdlib only.

| Evidence | File | Result |
|---|---|---|
| Suite, verbose | [`run-tests.log`](run-tests.log) | **55 passed, 0 failed** |
| Boundary guard, live | [`boundary-guard-2026-09-03.log`](boundary-guard-2026-09-03.log) | **refused, exit 2**, both in-repo paths |
| Live sweep, real fleet | [`live-sweep-2026-09-03.log`](live-sweep-2026-09-03.log) | **clean, exit 0**, 2 hosts |
| Track B conformance | [`track-b.log`](track-b.log) | **5 of 5 checks PASS** |

## What the suite corroborates

Every logged issue is exercised by a test that fails without its fix
(PROCESS.md §7 Track A — "a green suite that does not exercise the failure is
not corroboration"):

| Issue | Test |
|---|---|
| [`aide-check-exits-non-zero…_d4ecdc86`](../../KNOWN_ISSUES.md#aide-check-exits-non-zero-when-it-succee_d4ecdc86) | `TestAideExitCodes` — 0, all of 1–7, error floor 14, unmapped 8/13/99/−1 |
| [`host-baselines-were-committed…_9d09c448`](../../KNOWN_ISSUES.md#host-baselines-were-committed-into-the-t_9d09c448) | `TestBoundaryGuard` — 5 cases, plus the live log |
| [`the-not-installed-heuristic…_a90badf2`](../../KNOWN_ISSUES.md#the-not-installed-heuristic-matched-not_a90badf2) | `test_missing_file_output_is_not_mistaken_for_an_absent_tool` |
| [`the-ssh-runner-had-no-way…_86ed9055`](../../KNOWN_ISSUES.md#the-ssh-runner-had-no-way-to-name-an-ide_86ed9055) | `TestSshIdentity`, plus the live sweep it made possible |

The sweep path is driven end to end through `runner.FakeRunner`, so the paths a
real host rarely shows — unreachable host, swapped database, unbaselined host,
absent tool, unmapped exit code — are all exercised. Two of those matter
particularly, and both are asserted directly: an **unreachable host never
renders as clean**, and an **empty sweep never renders as clean**.

## The live run, and what it did not do

`live-sweep-2026-09-03.log` is a real run against the two production hosts:
config → SSH → `sha256sum` → classify → report. Both `aide.db` fingerprints
matched their records taken 2026-09-01. Host identifiers are redacted in the
log for the same reason the baselines are not in this repo.

**It ran `--only aide_db_fingerprint`.** The full sweep — `aide --check` over
~88,000 entries, plus `debsums`, plus `rkhunter` — is minutes of CPU on each
host, and one of them holds 4.4 GB of a 7.9 GB machine in a Java process. Those
three checks are therefore covered by the suite against recorded output, **not**
by a production run. That is a real limit on this evidence and it is stated here
rather than implied: the classification of their output is proven, the
end-to-end invocation of them against a live host is not.

## Environment

- Container at `/studio`, `python3` stdlib only (no pip, no third-party imports).
- The suite needs no host, no SSH key and no network. The two live logs need
  both, and a baselines directory outside the repository.
