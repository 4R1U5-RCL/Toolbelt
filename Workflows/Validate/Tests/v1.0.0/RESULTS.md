# Tests — Workflows/Validate v1.0.0

Recorded results for `Tooling/v1.0.0/`. Raw captured output: [`run-tests.log`](run-tests.log).

The iteration these results belong to is [`../../CHANGE_LOG.md#migrate-workflows-validate-to-the-proces_c65a856c`](../../CHANGE_LOG.md#migrate-workflows-validate-to-the-proces_c65a856c),
which is committed on branch `smoke/fix-workflows-validate` and is **not merged**.

Two runs are on record. Run 2 is the one captured first-hand by the session that wrote this
file; Run 1 is reproduced as the migration agent recorded it and is **not** re-attested here.

| Field | Run 1 | Run 2 |
|---|---|---|
| Version under test | `v1.0.0` | `v1.0.0` |
| Run at | 2026-08-31T15:25Z (UTC) | 2026-09-01 |
| Run by | migration agent, on the container host | correction pass, on the container host |
| Location | checkout `/studio/scratch/tb` (no branch named in the record) | worktree `/studio/scratch/tb-wt/workflows-validate`, branch `smoke/fix-workflows-validate` |
| Runner | none — this tool has **no `run-tests.sh`**; the suite was invoked directly | same |
| Command | `python3 tests/selftest.py`, from `Workflows/Validate/Tooling/v1.0.0/` | same |
| Interpreter | Python 3.11.2 | Python 3.11.2 |
| Network / secrets | none used — `selftest.py` injects a fake `call_model` | same |
| Result | `28 passed, 0 failed`, exit code 0 | `28 passed, 0 failed`, exit code 0 |

## Outcome — verbatim

Run 2, tail of the suite output:

```
== selftest: 28 passed, 0 failed ==
exit_code=0
```

28 assertions passed, 0 failed, exit code 0, from the post-move location. The full
per-assertion listing for both runs is in `run-tests.log`.

Run 1 reports that the same suite was also run **before** the move (from the old tool root) as a
baseline and reported `28 passed, 0 failed`. That baseline is the migration agent's record; this
session did not observe it. What this session did observe is that the suite passes 28/28 from the
new location.

## Runner trap — recorded so it is not re-discovered

`tests/selftest.py` is a **Python** script and there is no `run-tests.sh` in this tool. Running it
as `bash tests/selftest.py` produces shell errors that look like a broken suite but are only the
wrong interpreter:

```
tests/selftest.py: line 5: import: command not found
tests/selftest.py: line 6: syntax error near unexpected token `0,'
exit_code=2
```

This is captured in full in `run-tests.log` under RUN 2. It is **not** a test failure. The suite
is run with `python3`.

## Post-move entrypoint path check (not part of the suite)

Moving the code under `Tooling/v1.0.0/` could have broken the relative path resolution in
`bin/validate` (`PKG = Path(__file__).resolve().parent.parent`, then `PKG/"lib"` and
`PKG/"config"/"panel.json"`) and in `tests/selftest.py` (`sys.path.insert(0, parent.parent/"lib")`).
Both resolve relative to their own file, and the whole directory tree moved as a unit, so both
survived unchanged. Re-verified first-hand on 2026-09-01 and captured in `run-tests.log` under
RUN 2:

- `python3 bin/validate --help` — prints usage, proving `import validate_core` from the moved
  `lib/` succeeded.
- `OPENROUTER_API_KEY=x python3 bin/validate --panel nosuchkey hello` — fails with
  `ERROR: --panel matched no reasoners in the config.` and `exit_code=1`. **This exit 1 is the
  expected result**: reaching that message requires the default `--config` path
  (`Tooling/v1.0.0/config/panel.json`) to have been found, opened and parsed. It is a path proof,
  not a test failure.
- `bin/validate --help` also runs correctly with the working directory set to `bin/`, confirming
  no dependence on the caller's cwd.

No source file under `Tooling/v1.0.0/` was edited — for the migration or for the 2026-09-01 correction pass. No path required repair.

## Gap

There is no `run-tests.sh` in this tool. `process.yaml`'s `test_decision` branch expects
`./run-tests.sh` to exit 0 as the CI test gate; for this tool that gate currently has no
entrypoint to call. Adding one would be a code change, which this migration deliberately is not,
so it is recorded here and in `KNOWN_ISSUES.md` rather than done silently.
