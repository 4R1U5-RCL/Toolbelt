# Test results — Packages/Sentinel v1.0.0

Recorded evidence for `v1.0.0`, per PROCESS.md §4 and invariant 5. Every file
named here is the actual output of the run described, not a restatement of it.

**Declared runner:** `./run-tests.sh` (from `Tooling/v1.0.0/`) —
`python3 -m unittest discover -s tests -t .`, stdlib only.

| Evidence | File | Result |
|---|---|---|
| Suite, verbose | [`run-tests.log`](run-tests.log) | **72 passed, 0 failed** |
| Boundary guard, live | [`boundary-guard-2026-09-03.log`](boundary-guard-2026-09-03.log) | **refused, exit 2**, both in-repo paths |
| Fingerprint sweep, real fleet | [`live-sweep-2026-09-03.log`](live-sweep-2026-09-03.log) | **clean, exit 0**, 2 hosts |
| **First full production sweep** | [`sweep-2026-09-03-first-full-run.log`](sweep-2026-09-03-first-full-run.log) | **found 2 defects in this tool** |
| rkhunter record format | [`rkhunter-format-2026-09-03.log`](rkhunter-format-2026-09-03.log) | the shape the parser was rebuilt against |
| **Corrected AIDE run** | [`aide-corrected-2026-09-03.log`](aide-corrected-2026-09-03.log) | AIDE executes; **exit 7**, fully attributed; found the timeout defect |
| Track B conformance | [`track-b.log`](track-b.log) | **5 of 5 checks PASS** |

## The first full sweep, and what it cost

The most important file here is `sweep-2026-09-03-first-full-run.log`, and it is
not a passing result. On its first contact with both production hosts, v1.0.0:

- **never ran AIDE at all**, on either host — the command lacked `--config`, which
  Debian and Ubuntu require, so AIDE exited 17
  ([`…_7932f6e0`](../../KNOWN_ISSUES.md#aide-check-was-invoked-without-config-so_7932f6e0));
- **reported 22 rkhunter warnings as 22 identical lines** naming no file
  ([`…_f8ba0431`](../../KNOWN_ISSUES.md#rkhunter-evidence-captured-only-the-warn_f8ba0431)).

The corrected AIDE run that followed then found a third: the fixed **900-second
timeout was shorter than a full walk on the larger host**, and a slow check would
have been reported as an unreachable one
([`…_b1115836`](../../KNOWN_ISSUES.md#the-runner-s-fixed-900-second-command-ti_b1115836)).

**55 tests passed over both.** Every AIDE test called `classify_aide` with an exit
code supplied by the test, so the suite proved the classifier and proved nothing
about what the tool ran. That is the general lesson, not a detail of this bug: *a
test that supplies its own inputs to a pure function cannot fail for the reason
the tool is about to fail.* `tests/test_checks.py` (12 new tests) asserts on the
command strings and exists to close that class. The timeout defect is the same
shape again: `FakeRunner` returns instantly by construction, so no number of
tests could have shown that 900 seconds was the wrong limit. **Three of the seven
logged issues were only findable by running the tool against a real host.**

**What kept it from being a false all-clear.** `classify_aide` maps unrecognised
and error-range codes to `error`, never `clean`. The broken check therefore
surfaced as a loud `ERROR` on both hosts rather than a passing check that never
executed. That default was written for exactly this case and is the reason a
broken v1.0.0 could not have reported a clean host.

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
| [`aide-check-was-invoked-without-config…_7932f6e0`](../../KNOWN_ISSUES.md#aide-check-was-invoked-without-config-so_7932f6e0) | `TestCommands`, `TestAideConfigError` |
| [`rkhunter-evidence-captured-only…_f8ba0431`](../../KNOWN_ISSUES.md#rkhunter-evidence-captured-only-the-warn_f8ba0431) | `TestRootkitRecordParsing`, against the real captured format |
| [`the-runner-s-fixed-900-second…_b1115836`](../../KNOWN_ISSUES.md#the-runner-s-fixed-900-second-command-ti_b1115836) | `TestTimeout` — timeout ≠ unreachable, and does not end the sweep |

The sweep path is driven end to end through `runner.FakeRunner`, so the paths a
real host rarely shows — unreachable host, swapped database, unbaselined host,
absent tool, unmapped exit code — are all exercised. Two of those matter
particularly, and both are asserted directly: an **unreachable host never
renders as clean**, and an **empty sweep never renders as clean**.

## Coverage limits, stated

`live-sweep-2026-09-03.log` ran `--only aide_db_fingerprint` — one `sha256sum`
per host. The full sweep is minutes of CPU on each host, and one of them holds
4.4 GB of a 7.9 GB machine in a Java process.

After the `--config` fix, **AIDE's own end-to-end run against production is
recorded outside this suite**, in the report it was run for. The classification
of AIDE, debsums and rkhunter output is proven here against recorded output; the
`--config` fix is proven by `TestCommands` and by a hand-run of the corrected
command on both hosts.

## Environment

- Container at `/studio`, `python3` stdlib only (no pip, no third-party imports).
- The suite needs no host, no SSH key and no network. The live logs need both,
  and a baselines directory outside the repository.
