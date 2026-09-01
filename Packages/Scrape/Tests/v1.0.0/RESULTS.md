# Test results — Scrape v1.0.0

Recorded results of running the `Packages/Scrape` suite at version `v1.0.0`.
Verbatim console capture: [`run-tests.log`](run-tests.log).

| Field | Value |
|---|---|
| Version | `v1.0.0` |
| Run at | 2026-08-31T15:19:56+00:00 (container local time, UTC) |
| Runner | `Tooling/v1.0.0/run-tests.sh` (wraps `python3 -m unittest discover -s tests -t tests`) |
| Working directory | `/studio/scratch/tb/Packages/Scrape/Tooling/v1.0.0` |
| Interpreter | Python 3.11.2 |
| Network / credentials | none — the suite is offline and needs no `FIRECRAWL_API_KEY` |

## What was run

```
$ cd /studio/scratch/tb/Packages/Scrape/Tooling/v1.0.0 && ./run-tests.sh
```

Run after the migration of the tool's code from the tool root into
`Tooling/v1.0.0/`, to confirm the move did not break the suite's path
assumptions. `run-tests.sh` and `tests/helpers.py` both resolve paths relative
to their own `__file__`, so they moved intact; no path repair was needed.

## Outcome — verbatim

```
Ran 59 tests in 0.016s

OK
```

Process exit status: `0`.

The `usage: scrape url ...` / `scrape url: error: argument --format: invalid
choice: 'pdf'` lines in `run-tests.log` are expected stderr emitted by the CLI
test that asserts an unknown `--format` is rejected; they are not failures. The
full capture, including those lines, is in `run-tests.log`.

## Entrypoint smoke check

```
$ ./bin/scrape version
scrape 1.0.0
```

Exit status `0` — the `bin/scrape` shim still resolves the `scrape` package
after the move.

## Scope note

This run is a **conformance/regression** record for the migration described in
[`CHANGE_LOG.md#migrate-scrape-to-the-tooling-tests-layo_70b30a3b`](../../CHANGE_LOG.md).
It is not Track A corroboration of a code fix: no code changed at this version,
so there is no logged code failure for the suite to exercise.
