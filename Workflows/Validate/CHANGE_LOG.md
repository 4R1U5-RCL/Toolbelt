# CHANGE LOG — Workflows/Validate

Every iteration made in response to an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Each entry's
`resolves` field cites the issue it answers, and that issue cites this entry back (PROCESS.md §3
reciprocity).

Ids are `<description>_<hash8>` per `process.yaml` §5 — the slugified summary, plus the first 8
hex characters of the sha256 of the canonicalised summary.

---

## `migrate-workflows-validate-to-the-proces_c65a856c`

| Field | Value |
|---|---|
| **id** | `migrate-workflows-validate-to-the-proces_c65a856c` |
| **summary** | Migrate Workflows/Validate to the PROCESS.md layout: code moved to Tooling/v1.0.0/, test results recorded under Tests/v1.0.0/, missing canonical documents created |
| **resolves** | [`KNOWN_ISSUES.md#workflows-validate-failed-track-b-confor_ccdc053f`](KNOWN_ISSUES.md#workflows-validate-failed-track-b-confor_ccdc053f) |
| **version** | `v1.0.0` — **no bump.** The code did not change, it moved. This tool had never been versioned, so its existing code becomes `v1.0.0` (PROCESS.md §9, §10.6) |
| **merge_commit** | not yet merged — recorded on merge, per PROCESS.md §6 step 7 |
| **date** | 2026-08-31 |

**cause (Y).** The tool predates the layout PROCESS.md §3/§4 mandates and was never migrated out of
the flat, single-directory shape carried over from `operand-packages` v1. PROCESS.md §9 lists it as
a backlog row.

**outcome (X).** Because of that, Track B conformance failed on four of its five checks and the
fifth was unverifiable: only `README.md` of the five canonical documents existed; the code sat at
the tool root with no `Tooling/` directory and therefore no immutable rollback point; no recorded
test results existed under `Tests/`; and `README.md` named no version, so nothing in the tool
identified what version its code was.

**iteration (Z).** A layout- and documentation-only migration — no behavioural change:

1. Move `bin/`, `config/`, `docs/`, `lib/`, `tests/` and `.gitignore` from the tool root into
   `Tooling/v1.0.0/`. Test *code* moves with the version (PROCESS.md §4).
2. Check and repair anything the move breaks, then run the existing self-test from its new
   location.
3. Record the verbatim run output under `Tests/v1.0.0/`.
4. Create the four missing canonical documents and state the current version in `README.md`.

**expected_result (V), stated checkably.** After the iteration, all five Track B checks pass:
`README.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and `CHANGE_LOG.md` all exist
and are non-empty at the tool root; every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` entry
and vice versa, and this entry and its issue cite each other; the code sits under
`Tooling/v1.0.0/`; recorded results exist under `Tests/v1.0.0/`; and `README.md`, the newest
`Tooling/` directory and the newest `CHANGE_LOG.md` entry all name `v1.0.0`. The self-test must
still report `28 passed, 0 failed` from its new location — the same result as before the move.

**change (W) — what changed, where, and how it was verified.**

*What moved* (plain `mv`; no file content edited):

| From | To |
|---|---|
| `bin/` | `Tooling/v1.0.0/bin/` |
| `config/` | `Tooling/v1.0.0/config/` |
| `docs/` | `Tooling/v1.0.0/docs/` |
| `lib/` | `Tooling/v1.0.0/lib/` |
| `tests/` | `Tooling/v1.0.0/tests/` |
| `.gitignore` | `Tooling/v1.0.0/.gitignore` |

Stale `__pycache__` directories were deleted before the move; they are ignored by the tool's own
`.gitignore`, which moved with the code and still covers everything beneath it.

*Path repairs required: none.* Both path-sensitive files resolve relative to their own location and
the tree moved as a unit — `bin/validate` computes `PKG = Path(__file__).resolve().parent.parent`
and reads `PKG/"lib"` and `PKG/"config"/"panel.json"`; `tests/selftest.py` inserts
`Path(__file__).resolve().parent.parent/"lib"` on `sys.path`. Both were read and re-verified rather
than assumed. No source file was edited.

*Files created:*

- `IMPLEMENTATIONS.md` — seven use cases, each derived from `README.md`, the `bin/validate`
  argument parser, or `config/panel.json`, each citing its `TEMPLATES.md` form.
- `TEMPLATES.md` — the matching seven forms, copied verbatim from those same artifacts, with an
  explicit note that the tool has **no `templates/` directory** and that nothing was invented.
- `KNOWN_ISSUES.md` — header plus the Track B conformance entry this change resolves.
- `CHANGE_LOG.md` — this file.
- `Tests/v1.0.0/run-tests.log` — captured output, verbatim.
- `Tests/v1.0.0/RESULTS.md` — what was run, when, and the outcome.

*Files edited:* `README.md` only — a "Version" line naming `v1.0.0`, updated paths for the moved
code, and a pointer to the recorded results. No behavioural documentation was rewritten.

*How it was verified.* `python3 tests/selftest.py`, run from `Tooling/v1.0.0/` on Python 3.11.2 at
2026-08-31T15:25Z: **28 passed, 0 failed, exit code 0** — identical to the baseline run taken from
the old location before the move. Entrypoint path resolution was checked separately
(`bin/validate --help` imports the moved `lib/`; a deliberate bad `--panel` key proves the default
config path is found and parsed; both work with the cwd set to `bin/`). Full output:
[`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log); summary:
[`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md).

*Known to remain open after this change* (see the residual gaps on the issue entry): the tool has
no `run-tests.sh`, so `process.yaml`'s `test_decision` gate has no entrypoint to call, and
`TEMPLATES.md` documents derived forms because no `templates/` directory exists. Both are code
changes and were deliberately left out of a move-only iteration.
