# Change log — `Packages/Scrape`

Every iteration made in response to an entry in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Append only; each entry cites the issue it
resolves, and that issue cites this entry back (PROCESS.md §3).

Entries follow the `process.yaml` `change-entry` schema: id, resolves, cause,
outcome, iteration, expected_result, change, version, merge_commit.

| Change id | Resolves | Version | Summary |
|---|---|---|---|
| [migrate-scrape-to-the-tooling-tests-layo_70b30a3b](#migrate-scrape-to-the-tooling-tests-layo_70b30a3b) | [track-b-conformance-failure-scrape-code_76631893](KNOWN_ISSUES.md#track-b-conformance-failure-scrape-code_76631893) | `v1.0.0` | Migrate to the `Tooling/` + `Tests/` layout and create the missing canonical documents |

---

<a name="migrate-scrape-to-the-tooling-tests-layo_70b30a3b"></a>
## migrate-scrape-to-the-tooling-tests-layo_70b30a3b

- **id.** `migrate-scrape-to-the-tooling-tests-layo_70b30a3b`
- **summary.** Migrate Scrape to the Tooling/Tests layout at v1.0.0 and create the missing canonical documents
- **resolves.** [`KNOWN_ISSUES.md#track-b-conformance-failure-scrape-code_76631893`](KNOWN_ISSUES.md#track-b-conformance-failure-scrape-code_76631893)

### Cause (Y)

`Packages/Scrape` predates the PROCESS.md §3/§4 conventions (settled
2026-08-31); it was merged in PR #14 and no migration pass had run against it
since. It is one of the eleven rows in the PROCESS.md §9 backlog.

### Outcome (X)

The tool failed the Track B canonical-files, reciprocity, code-layout,
test-layout and version-agreement checks: `TEMPLATES.md` and `CHANGE_LOG.md` did
not exist, the code sat at the tool root with no `Tooling/` directory, no
`Tests/` directory held recorded results, and `README.md` named no version. With
no released version directory the tool had no in-repo rollback point, and under
PROCESS.md §7 it could not release a new version.

### Iteration (Z)

A layout-and-documents migration only — no behaviour change. Move every
implementation file into `Tooling/v1.0.0/`, verify the suite still passes from
its new location, record the actual output under `Tests/v1.0.0/`, create the two
missing canonical documents, append the reciprocal template citations, and state
the version in `README.md`.

### Expected result (V)

Checkable, one line per Track B row:

1. `README.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and
   `CHANGE_LOG.md` all exist at the tool root and are non-empty.
2. Every `KNOWN_ISSUES.md` process entry cites a `CHANGE_LOG.md` id and back;
   every `IMPLEMENTATIONS.md` recipe cites a `TEMPLATES.md` id and back.
3. The tool's code sits under `Tooling/v1.0.0/`; nothing but the five documents,
   `Tooling/` and `Tests/` remains at the tool root.
4. `Tests/v1.0.0/` holds the verbatim output of the suite run.
5. `README.md`, the newest `Tooling/` directory and the newest `CHANGE_LOG.md`
   entry all name `v1.0.0`.
6. `./run-tests.sh` still exits `0` from `Tooling/v1.0.0/`, and `./bin/scrape
   version` still resolves the package.

### Change (W)

**Moved** — from the tool root into `Tooling/v1.0.0/`, by plain `mv`, contents
unmodified: `bin/`, `scrape/`, `tests/`, `examples/`, `run-tests.sh`,
`.gitignore`.

**Paths repaired** — none were needed. Both path-manipulating files resolve
against their own `__file__` and so survived the move intact:

- `run-tests.sh` does `cd "$(dirname "$0")"` before
  `python3 -m unittest discover -s tests -t tests`.
- `tests/helpers.py:15` and `bin/scrape:10` each do
  `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))`,
  which now resolves to `Tooling/v1.0.0/` instead of the tool root — the same
  relative depth, so the `scrape` package is still importable.

This was verified by running rather than assumed; see below.

**Created** —

- `CHANGE_LOG.md` (this file), with its header and this first entry.
- `TEMPLATES.md`. The tool has **no `templates/` directory**; the file records
  that explicitly and documents the application forms that do exist — the four
  files in `Tooling/v1.0.0/examples/` (`single-url.json`, `batch-json.json`,
  `llm-chunks.json`, `urls.txt`) as `TPL-01`…`TPL-04`, and the "new backend
  class" form from `IMPLEMENTATIONS.md` as `TPL-05`. Every template is
  transcribed verbatim from the file it comes from.
- `Tests/v1.0.0/run-tests.log` — the verbatim console capture.
- `Tests/v1.0.0/RESULTS.md` — what was run, when, and the outcome.

**Appended** —

- `KNOWN_ISSUES.md` gained a "Process issues" section and the issue this entry
  resolves. The existing `KI-01`…`KI-08` guard entries were not touched
  (PROCESS.md §5.1).
- `IMPLEMENTATIONS.md` gained a "Template index" section supplying the
  reciprocal `TEMPLATES.md` citation each existing recipe owed, plus a note that
  its relative paths are now relative to `Tooling/v1.0.0/`. Existing prose was
  not rewritten (PROCESS.md §5.2).

**Edited** — `README.md` only: a version line naming `v1.0.0` and pointers to
`TEMPLATES.md`, `CHANGE_LOG.md` and `Tests/`, and the Quickstart / Layout /
Testing sections repointed at `Tooling/v1.0.0/`. No other prose changed.

**Not changed** — no file under `scrape/`, `tests/`, `bin/` or `examples/` was
edited. `scrape/__init__.py` already carried `__version__ = "1.0.0"`, which is
why `v1.0.0` is both the §10.6 starting version and the version the code already
claimed.

### How it is verified

`./run-tests.sh` run from `Tooling/v1.0.0/` after the move:

```
Ran 59 tests in 0.016s

OK
```

Exit status `0`. Plus `./bin/scrape version` → `scrape 1.0.0`, exit `0`. Full
capture and conditions: [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) and
[`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log).

Note on corroboration (PROCESS.md §7 Track A): this suite is a **regression**
check, not corroboration of a code fix. The logged issue is a documents-and-
layout failure, so its corroborating evidence is the repository tree and the five
documents themselves — the suite's role is to prove the move broke nothing.

### version

`v1.0.0` — **no bump.** The code did not change, it moved. Per PROCESS.md §9,
a tool that has never been versioned has its current code become
`Tooling/v1.0.0/`; this is that directory, and it is now the rollback point for
the next iteration (PROCESS.md §5 safeguard 1).

### merge_commit

Not recorded. This migration ran under an orchestrator that performs all git
operations, so no branch, PR or merge commit existed at write time. To be filled
in by the merge step (PROCESS.md §6 step 7).
