# Test results — v1.0.0

Recorded verbatim per PROCESS.md §5 invariant 6. Full captured output:
[`run-tests.log`](run-tests.log).

| | |
|---|---|
| Version under test | `v1.0.0` (`Tooling/v1.0.0/`) |
| Command | `cd Packages/Telegram/Tooling/v1.0.0 && ./run-tests.sh -v` |
| Run at | 2026-08-31T15:23:20+00:00 (container local time) |
| Runner | `python3 -m unittest discover -s tests -t tests` (Python 3.11.2, Linux 6.6.135) |
| Node available | yes — `node v22.23.1` |
| Outcome | **PASS** — `Ran 189 tests in 1.067s` / `OK`, exit code 0 |
| Skips | none — 0 tests skipped |

## What was run

The suite that ships with this version, from its new location
`Tooling/v1.0.0/tests/`, after the migration recorded in
[`CHANGE_LOG.md`](../../CHANGE_LOG.md#migrate-packages-telegram-to-the-tooling_78deb9ee).
It is the whole suite: 10 test modules, offline, no network.

## Why the zero-skip line matters

Three tests in this suite are written to **skip loudly** rather than pass
quietly when their subject is missing (README, "What is proven, and how"):

- `test_conformance.TestAgainstClientMjs` — the envelope compared byte-for-byte
  against `/studio/packages/notify/src/client.mjs`, executed in `node`.
- `test_conformance.TestAgainstPollerSink` — the same envelope compared against
  `Packages/Poller`'s `notify_webhook` sink.
- `test_n8n_parity` — the receiver workflow's JavaScript executed against the
  same updates as the Python decoder.

All three **ran** in this recorded run (`... ok` in `run-tests.log`); none
skipped. That is the evidence that the migration did not silently disarm the
cross-implementation checks by breaking the paths they resolve — the
`Packages/Poller` path was in fact broken by the move and repaired, see the
change entry.

## Verbatim tail

```
----------------------------------------------------------------------
Ran 189 tests in 1.067s

OK
EXIT=0
```
