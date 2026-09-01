# Change log — Skills/Errors

Every iteration made in response to an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), in the
`PROCESS.md` §6 entry format. Each entry's `resolves` field cites the issue it answers, and
that issue cites this entry back (PROCESS.md §3 reciprocity).

Versions are the directories under `Tooling/`; a released version directory is immutable
and is the rollback point (PROCESS.md §4).

---

<a name="migrate-skills-errors-to-the-process-md_58690b69"></a>
## `migrate-skills-errors-to-the-process-md_58690b69`

- **id:** `migrate-skills-errors-to-the-process-md_58690b69`
- **summary:** Migrate Skills/Errors to the PROCESS.md layout at v1.0.0 and create the missing canonical documents
- **resolves:** [`KNOWN_ISSUES.md#skills-errors-fails-track-b-conformance_4b9a21ed`](KNOWN_ISSUES.md#skills-errors-fails-track-b-conformance_4b9a21ed)
- **cause:** The tool was transferred from `operand-packages` in its pre-PROCESS.md shape
  (README + loose `templates/` and `tests/`), and nothing enforces the §3/§4 layout at
  transfer time — so the conventions were never applied to it. This is the §9 migration
  backlog.
- **outcome:** Four of the five Track B checks failed: four canonical documents missing,
  code not under `Tooling/`, no recorded results under `Tests/`, and a README naming no
  version — leaving the tool unable to release a version and without an in-repo rollback
  point. Full detail in the issue entry.
- **iteration:** A documents-and-layout migration with **no behaviour change**. The code
  did not change, it moved, so no version is bumped: the tool's existing code becomes its
  first released version, `v1.0.0` (PROCESS.md §9 — "a tool that has never been versioned
  starts at v1.0", §10.6 — `v1.0.0`).
- **expected_result:** All five Track B checks pass for `Skills/Errors` at `v1.0.0`:
  1. all five canonical files exist at the tool root and are non-empty;
  2. `Tooling/v1.0.0/` holds the tool's code;
  3. `Tests/v1.0.0/` holds the actual output of running that version's tests;
  4. `README.md`, the newest `Tooling/` directory and the newest `CHANGE_LOG.md` entry all
     name `v1.0.0`;
  5. reciprocity holds — this entry and its issue cite each other, and every
     `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` entry and vice versa.
- **change:**
  - **Moved** (no edits to the moved files): `templates/` → `Tooling/v1.0.0/templates/`
    and `tests/` → `Tooling/v1.0.0/tests/`. Test code ships inside the version it tests
    (PROCESS.md §4).
  - **Path repair: none required, verified rather than assumed.**
    `Tooling/v1.0.0/tests/verify.sh` resolves its own location with
    `HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and reads the templates from
    `PKG="$HERE/.."`, so the move preserved the relationship it depends on. It is the only
    executable in the tool; there is no `bin/`, no `sys.path` manipulation, and no import
    that assumes a directory depth. It has no `run-tests.sh`.
  - **Created** `Tests/v1.0.0/run-tests.log` — verbatim output of
    `bash Tooling/v1.0.0/tests/verify.sh` run from the tool root on 2026-08-31 — and
    `Tests/v1.0.0/RESULTS.md` recording what was run, when, and the outcome.
  - **Created** `IMPLEMENTATIONS.md` (four use cases derived from the README and the
    shipped files, each citing its template), `TEMPLATES.md` (the three templates actually
    present in `Tooling/v1.0.0/templates/`, each citing the implementations that use it),
    `KNOWN_ISSUES.md` (header + the issue this entry resolves), and this `CHANGE_LOG.md`.
  - **Edited** `README.md`, minimally: it now states the current version `v1.0.0` and
    links the version directories and the four new documents; the three `templates/…`
    paths in its "What's here" table, the `copy templates/…` line in the Quickstart and the
    `bash tests/verify.sh` self-check line were repointed at `Tooling/v1.0.0/…`; and its
    "Known issues / caveats" section now says explicitly that it describes the live studio
    registry, not this tool, and points at `KNOWN_ISSUES.md`. No other prose was changed.
- **verified_by:** `bash Tooling/v1.0.0/tests/verify.sh` run from the new location on
  2026-08-31 — **32 passed, 0 failed**, exit code 0. Output recorded verbatim at
  [`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log); see
  [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md).
- **version:** `v1.0.0` — the tool's current version. No bump: the code moved, it did not
  change.
- **merge_commit:** not yet merged. This change sits on a branch; the PR and merge to
  `main` (PROCESS.md §5.4/§8) are handled outside this run, and this field is to be filled
  in on merge.
