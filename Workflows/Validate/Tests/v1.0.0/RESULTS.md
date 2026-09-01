# Tests — Workflows/Validate v1.0.0

Recorded results for `Tooling/v1.0.0/`. Raw captured output: [`run-tests.log`](run-tests.log).

| Field | Value |
|---|---|
| Version under test | `v1.0.0` |
| Run at | 2026-08-31T15:25Z (UTC) |
| Run by | migration agent, on the container host |
| Runner | none — this tool has **no `run-tests.sh`**; the suite was invoked directly |
| Command | `python3 tests/selftest.py`, from `Workflows/Validate/Tooling/v1.0.0/` |
| Interpreter | Python 3.11.2 |
| Network / secrets | none used — `selftest.py` injects a fake `call_model` |

## Outcome — verbatim

```
== selftest: 28 passed, 0 failed ==
exit_code=0
```

28 assertions passed, 0 failed, exit code 0. The full per-assertion listing is in
`run-tests.log`.

The same suite was run once **before** the move (from the old tool root) as a baseline and
also reported `28 passed, 0 failed`. The move therefore changed no test outcome.

## Post-move entrypoint path check (not part of the suite)

Moving the code under `Tooling/v1.0.0/` could have broken the relative path resolution in
`bin/validate` (`PKG = Path(__file__).resolve().parent.parent`, then `PKG/"lib"` and
`PKG/"config"/"panel.json"`) and in `tests/selftest.py` (`parent.parent/"lib"`). Both resolve
relative to their own file, and the whole directory tree moved as a unit, so both survived
unchanged. Verified explicitly and captured in `run-tests.log`:

- `python3 bin/validate --help` — prints usage, proving `import validate_core` from the moved
  `lib/` succeeded.
- `OPENROUTER_API_KEY=x python3 bin/validate --panel nosuchkey hello` — fails with
  `ERROR: --panel matched no reasoners in the config.` and `exit_code=1`. **This exit 1 is the
  expected result**: reaching that message requires the default `--config` path
  (`Tooling/v1.0.0/config/panel.json`) to have been found, opened and parsed. It is a path proof,
  not a test failure.
- `bin/validate --help` also runs correctly with the working directory set to `bin/`, confirming
  no dependence on the caller's cwd.

No source file was edited for this migration — no path required repair.

## Gap

There is no `run-tests.sh` in this tool. `process.yaml`'s `test_decision` branch expects
`./run-tests.sh` to exit 0 as the CI test gate; for this tool that gate currently has no
entrypoint to call. Adding one would be a code change, which this migration deliberately is not,
so it is recorded here and in `KNOWN_ISSUES.md` rather than done silently.
