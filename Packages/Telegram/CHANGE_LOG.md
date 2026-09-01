# Change log — iterations made in response to issues

Every entry here answers an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) and
cites its id, per PROCESS.md §3 (reciprocal pair) and §6. Newest last; entries
are appended, never rewritten.

Entry ids follow `process.yaml: definitions.change-id` —
`<description>_<hash8>`, the hash being the first 8 hex characters of
`sha256` over the canonical (trimmed, lowercased, whitespace-collapsed)
summary.

---

<a name="migrate-packages-telegram-to-the-tooling_78deb9ee"></a>
## `migrate-packages-telegram-to-the-tooling_78deb9ee`

| Field | Value |
|---|---|
| **id** | `migrate-packages-telegram-to-the-tooling_78deb9ee` |
| **resolves** | [`KNOWN_ISSUES.md#packages-telegram-failed-track-b-conform_9f851380`](KNOWN_ISSUES.md#packages-telegram-failed-track-b-conform_9f851380) |
| **version** | `v1.0.0` — current version, **no bump**. The code did not change, it moved (PROCESS.md §9: an unversioned tool's current code becomes `Tooling/v1.0.0/`) |
| **merge_commit** | not recorded — this working copy performs no git operations; the commit and PR are the orchestrator's (PROCESS.md §8) |

**summary.** Migrate Packages/Telegram to the Tooling/Tests versioned layout at
v1.0.0 and create CHANGE_LOG.md.

**cause (Y).** The tool predates PROCESS.md. It was authored as a flat package
directory — `telegram/`, `bin/`, `templates/`, `n8n/`, `examples/`, `tests/`,
`run-tests.sh` all at the tool root — and the convention that a tool's code sits
under `Tooling/v<version>/` and its recorded test output under
`Tests/v<version>/` did not exist when it was written. `CHANGE_LOG.md` had never
been created because no iteration had ever been logged through §6.

**outcome (X).** Packages/Telegram failed three of the five Track B checks of
PROCESS.md §7: canonical files (`CHANGE_LOG.md` absent), code layout (no
`Tooling/`), test layout (no `Tests/`). Under §7 a tool in that state cannot
release a new version, so the next real fix to this package was blocked before
it started.

**iteration (Z).** Move the implementation into `Tooling/v1.0.0/`, repair the
paths the move breaks, run the suite from its new location and record the actual
output under `Tests/v1.0.0/`, create `CHANGE_LOG.md`, and state the current
version in `README.md`.

**expected_result (V).** Checkably:

1. `Packages/Telegram/Tooling/v1.0.0/` contains the code; the five canonical
   `.md` files remain at the tool root and nothing else does.
2. `./run-tests.sh` run from `Tooling/v1.0.0/` exits 0.
3. The three cross-implementation tests **run** rather than skip — a skip would
   mean the move silently disarmed them.
4. `Tests/v1.0.0/` holds the verbatim output of that run.
5. All five canonical files exist and are non-empty.
6. `README.md`, the newest `Tooling/` directory and this entry all name
   `v1.0.0`.

**change (W).** What changed, where, and how it was verified:

- **Moved** into `Tooling/v1.0.0/`: `telegram/`, `bin/`, `templates/`, `n8n/`,
  `examples/`, `tests/`, `run-tests.sh`. Plain `mv`; no file contents altered by
  the move itself.
- **Left at the tool root**: `README.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`,
  `KNOWN_ISSUES.md`, `CHANGE_LOG.md` (§3), and `.gitignore` — the ignore rules
  (`__pycache__/`, `*.pyc`, state and lock files) apply recursively from the
  root and would stop covering the tool root if moved down.
- **Path repaired — one, and it was load-bearing.**
  `tests/test_conformance.py` resolved `Packages/Poller` by walking three
  directories up from the test file. At the new depth that expression pointed at
  `Packages/Telegram/Tooling/`, so `os.path.isdir` returned False and both
  cross-package conformance tests would have **skipped silently while the suite
  still reported OK** — exactly the failure mode the file's own docstring warns
  about. Replaced with `_poller_sinks_root()`, which walks five directories up
  to `Packages/`, and accepts either the flat `Packages/Poller/poller/` or a
  migrated `Packages/Poller/Tooling/v<version>/poller/` (newest first), so the
  test survives the Poller's own migration. Verified by the tests running:
  `test_envelope_bytes_match_the_poller_sink ... ok` in
  [`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log).
- **Paths checked and found correct at the new depth, unchanged**:
  `run-tests.sh` (`cd "$(dirname "$0")"`, relative discovery of `tests`);
  `bin/telegram` and `tests/helpers.py` (both insert `dirname(dirname(__file__))`
  on `sys.path`, which is still the package root because `telegram/` moved with
  them); `telegram/template.py` `_builtin_dir()` (same two-level walk to
  `templates/`, which also moved); `tests/test_n8n_parity.py` (two-level walk to
  `n8n/`, which also moved). Verified by running, not by inspection alone: the
  suite passes and `./bin/telegram templates` and `./bin/telegram render report`
  both produce correct output from the new location.
- **Created**: `Tests/v1.0.0/run-tests.log` (captured stdout+stderr of the
  verbose run, exit code included), `Tests/v1.0.0/RESULTS.md`, and this file.
- **Edited**: `README.md` only — the Quickstart `cd` path, the `n8n/README.md`
  link, the `grep -rn TG-03` hint, and a Layout section naming the current
  version. Wording and claims otherwise untouched.
- **Not edited**: `IMPLEMENTATIONS.md` (append-only, §5.2) and `TEMPLATES.md`
  (already present and complete). Both contain tool-root-relative paths such as
  `./bin/telegram` and `tests/test_conformance.py` that are now one directory
  further down; this is recorded as an open sub-point on the issue rather than
  fixed by rewriting an append-only document.

**Verification of V, item by item:** 1 ✅ (`ls` of the tool root); 2 ✅ (exit 0);
3 ✅ (zero skips in the log, all three named tests `ok`); 4 ✅; 5 ✅; 6 ✅.
