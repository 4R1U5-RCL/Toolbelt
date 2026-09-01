# Test results — Packages/Poller v2.1.0

Recorded verbatim per PROCESS.md §5 invariant 6. Raw capture:
[`run-tests.log`](run-tests.log).

| Field | Value |
|---|---|
| Version under test | `v2.1.0` |
| Code location | `Packages/Poller/Tooling/v2.1.0/` |
| Runs recorded | 2026-08-31T15:20:38Z (migration) and 2026-09-01T04:35:30Z (re-run on branch `smoke/fix-packages-poller`) |
| Runner | `./run-tests.sh` (wraps `python3 -m unittest discover -s tests -t tests`) |
| Interpreter | Python 3.11.2 |
| Network | none — the suite is offline and deterministic by design |
| Exit code | `0` (both runs) |

## What was run

### Run 1 — 2026-08-31T15:20:38Z (the migration run)

```
$ cd /studio/scratch/tb/Packages/Poller/Tooling/v2.1.0 && ./run-tests.sh
```

Verbatim outcome:

```
...........................................................................................................................................................................................
----------------------------------------------------------------------
Ran 187 tests in 1.119s

OK
exit_code=0
```

### Run 2 — 2026-09-01T04:35:30Z (re-run on branch `smoke/fix-packages-poller`)

```
$ cd /studio/scratch/tb-wt/packages-poller/Packages/Poller/Tooling/v2.1.0 && ./run-tests.sh
```

Verbatim outcome:

```
...........................................................................................................................................................................................
----------------------------------------------------------------------
Ran 187 tests in 1.060s

OK
exit_code=0
```

**Outcome: PASS — 187 tests, 0 failures, 0 errors, in both runs.** Only the
wall-clock duration differs between them; the pass count and exit code do not.

## Smoke checks of the moved entry point

Run from the new location, after the move, to confirm the `bin/poller` shim's
`sys.path` insertion still resolves the package:

```
$ ./bin/poller --version
poller 2.1.0

$ ./bin/poller status --config examples/generic-http.json
example: NEVER_RAN — no heartbeat at /root/.poller/example.heartbeat.json
exit_code=1
```

`status` exits `1` because no watch has ever run against that example config —
`NEVER_RAN` is the expected answer here, not a failure of the smoke check. The
2026-09-01 re-run reproduced both lines exactly.

## Scope and honest limits

- This is the **v2.1.0 suite as it already stood**; no test was added or altered
  by the migration recorded in
  [`../../CHANGE_LOG.md#conformance-only-migration-of-the-existi_18d24e7c`](../../CHANGE_LOG.md#conformance-only-migration-of-the-existi_18d24e7c).
- The run corroborates that moving the tree under `Tooling/v2.1.0/` did not
  break imports, the test discovery root, or the executable shim. It does **not**
  corroborate any behavioural fix, because the migration changed no code.
- A baseline run at the tool root *before* the move produced the same result
  (187 tests, OK), so the pass is not an artefact of the new layout.
- Nothing here exercises live network rails (Kaggle, Slack, Telegram, n8n);
  those require credentials and were not run.
- The raw capture of both runs, including the smoke checks, is in
  [`run-tests.log`](run-tests.log). Nothing here is reconstructed from memory.
