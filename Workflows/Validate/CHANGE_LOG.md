# CHANGE LOG — Workflows/Validate

Every iteration made in response to an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Each entry's
`resolves` field cites the issue it answers, and that issue cites this entry back (PROCESS.md §3
reciprocity).

Ids are `<description>_<hash8>` per `process.yaml` `definitions.change-id`. The identity string of
a **change** entry is its `iteration` field alone — the planned change Z (PROCESS.md §10.8, which
mirrors §10.3 for issues). It is *not* derived from any summary: a change entry has no `summary`
field, and `resolves`, `version` and `merge_commit` are excluded from identity because none of them
exist yet at `write_change`. Canonicalisation, in order: trim → lowercase → collapse whitespace runs
to a single space → strip trailing punctuation (`. , ; : ! ?`), per PROCESS.md §10.14.
`<description>` is that canonical string slugified and truncated to 40 characters; `<hash8>` is the
first 8 hex characters of its sha256.

Entry headings are the **bare id** — no backticks, nothing else on the line
(`process.yaml` `definitions.entry`), because the heading text is the anchor that
`CHANGE_LOG.md#<id>` citations resolve against.

> **One correction, recorded rather than hidden (2026-09-01).** The entry below was written during
> the 2026-08-31 migration and has never been merged or released. Its conformance defects were
> corrected in place: the heading was un-backticked, the identity row was relabelled from `summary`
> (not a change-entry field) to `iteration` (the field that *is* the identity, PROCESS.md §10.8),
> `merge_commit` was made honestly empty, and the branch is now named. The identity **text** is
> unchanged, so the id still recomputes to `migrate-workflows-validate-to-the-proces_c65a856c`.

---

## migrate-workflows-validate-to-the-proces_c65a856c

| Field | Value |
|---|---|
| **id** | `migrate-workflows-validate-to-the-proces_c65a856c` |
| **iteration** | Migrate Workflows/Validate to the PROCESS.md layout: code moved to Tooling/v1.0.0/, test results recorded under Tests/v1.0.0/, missing canonical documents created |
| **resolves** | [`KNOWN_ISSUES.md#workflows-validate-failed-track-b-confor_ccdc053f`](KNOWN_ISSUES.md#workflows-validate-failed-track-b-confor_ccdc053f) |
| **version** | `v1.0.0` — **no bump.** The code did not change, it moved. This tool had never been versioned, so its existing code becomes `v1.0.0` (PROCESS.md §9, §10.6) |
| **merge_commit** | *(empty — not merged)* |
| **date** | 2026-08-31 (iteration executed); 2026-09-01 (entry corrected, evidence re-run) |
| **branch** | `smoke/fix-workflows-validate` — where this entry and the iteration's files are committed. `main` is unchanged and holds none of it |

> The row labelled **iteration** above is this entry's identity field, and the only text the id is
> computed from. The `iteration (Z), in detail` section below expands it; it does not redefine it.
> This row was previously labelled `summary`, a field the change-entry schema does not define. The
> text is unchanged, so the id is unchanged — it still recomputes to `c65a856c`.

**cause (Y).** The tool predates the layout PROCESS.md §3/§4 mandates and was never migrated out of
the flat, single-directory shape carried over from `operand-packages` v1. PROCESS.md §9 lists it as
a backlog row.

**outcome (X).** Because of that, Track B conformance failed on four of its five checks and the
fifth was unverifiable: only `README.md` of the five canonical documents existed; the code sat at
the tool root with no `Tooling/` directory and therefore no immutable rollback point; no recorded
test results existed under `Tests/`; and `README.md` named no version, so nothing in the tool
identified what version its code was.

**iteration (Z), in detail.** A layout- and documentation-only migration — no behavioural change:

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

*How it was verified.* The suite is `python3 tests/selftest.py` — a Python script, **not** a shell
script; running it under `bash` produces a misleading cascade of shell syntax errors and proves
nothing (recorded in `Tests/v1.0.0/run-tests.log` so the next reader does not repeat it).

Two runs are on record, both from `Tooling/v1.0.0/` on Python 3.11.2:

- **2026-08-31T15:25Z**, recorded by the migration agent from the checkout at `/studio/scratch/tb`:
  **28 passed, 0 failed, exit code 0**, reported as identical to a baseline taken from the old
  location before the move.
- **2026-09-01**, re-run on branch `smoke/fix-workflows-validate` while correcting this entry:
  **28 passed, 0 failed, exit code 0**. The move did not break `sys.path` or any relative path —
  `tests/selftest.py` inserts `Path(__file__).resolve().parent.parent/"lib"`, and `bin/validate`
  resolves `PKG/"lib"` and `PKG/"config"/"panel.json"` from its own location, so both follow the
  tree. Re-checked directly: `bin/validate --help` prints usage (the moved `lib/` imports);
  `--panel nosuchkey` exits 1 with `ERROR: --panel matched no reasoners in the config.`, which
  can only be reached if the default config path was found and parsed; and `--help` still works
  with the cwd set to `bin/`.

Full output for both: [`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log); summary:
[`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md). The 2026-09-01 output is recorded verbatim;
the 2026-08-31 output is reproduced as the migration agent captured it and is not re-attested here.

*Known to remain open after this change* (see the residual gaps on the issue entry): the tool has
no `run-tests.sh`, so `process.yaml`'s `test_decision` gate has no entrypoint to call, and
`TEMPLATES.md` documents derived forms because no `templates/` directory exists. Both are code
changes and were deliberately left out of a move-only iteration.
