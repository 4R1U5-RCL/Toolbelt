# Test results — Scrape v1.0.0

Recorded results for `Packages/Scrape` at version `v1.0.0`. Two records, both
verbatim console captures of runs that actually happened:

| File | Holds |
|---|---|
| [`run-tests.log`](run-tests.log) | the executable suite, `Tooling/v1.0.0/run-tests.sh` |
| [`track-b.log`](track-b.log) | the PROCESS.md §7 Track B conformance check |

| Field | Value |
|---|---|
| Version | `v1.0.0` |
| Run at | suite 2026-09-01T04:33+00:00; conformance check 2026-09-01T04:44+00:00 (container local time, UTC) |
| Branch | `smoke/fix-packages-scrape` (not merged; no PR opened) |
| Runner | `Tooling/v1.0.0/run-tests.sh` (wraps `python3 -m unittest discover -s tests -t tests`) |
| Working directory | `/studio/scratch/tb-wt/packages-scrape/Packages/Scrape/Tooling/v1.0.0` |
| Interpreter | Python 3.11.2 |
| Network / credentials | none — the suite is offline and needs no `FIRECRAWL_API_KEY` |

## 1. The executable suite

```
$ cd /studio/scratch/tb-wt/packages-scrape/Packages/Scrape/Tooling/v1.0.0 && ./run-tests.sh
```

### Outcome — verbatim

```
Ran 59 tests in 0.016s

OK
```

Process exit status: `0`. Full capture in [`run-tests.log`](run-tests.log).

The `usage: scrape url ...` / `scrape url: error: argument --format: invalid
choice: 'pdf'` lines in that log are expected stderr from the CLI test that
asserts an unknown `--format` is rejected; they are not failures.

### Entrypoint smoke check

```
$ ./bin/scrape version
scrape 1.0.0
```

Exit status `0` — the `bin/scrape` shim still resolves the `scrape` package from
under `Tooling/v1.0.0/`.

### What this run does and does not show

It shows that nothing under `Tooling/v1.0.0/` is broken. It is **not** Track A
corroboration of a code fix: `git diff HEAD -- Packages/Scrape/Tooling/` is empty
on this branch, so no code changed and there is no logged code failure for the
suite to exercise. Both issues in `KNOWN_ISSUES.md` are documents failures, and
their corroborating evidence is section 2 below — which invariant 5 accepts as
recorded evidence ("For a code-less tool (§4) it is a recorded Track-B
conformance result").

## 2. Track B conformance

Verbatim capture: [`track-b.log`](track-b.log).

The check applied is PROCESS.md §7 Track B **quoted, not paraphrased**:

| Check | Passes when |
|---|---|
| Canonical files | all five of §3 exist and are non-empty |
| Reciprocity | every **non-legacy** `KNOWN_ISSUES.md` entry cites a `CHANGE_LOG.md` id and vice versa; every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` id and vice versa. Legacy entries are defined and exempted in §9 |
| Code layout | the tool's code sits under `Tooling/v<version>/` |
| Test layout | recorded results exist under `Tests/v<version>/` for the current version |
| Version agreement | `README.md`, the newest `Tooling/` directory and the newest `CHANGE_LOG.md` entry name the same current version |

### Result

| Check | Result | Evidence |
|---|---|---|
| Canonical files | **PASS** | all five present and non-empty; sizes in `track-b.log` |
| Reciprocity | **PASS** | `track-b.log` §reciprocity — 28 level-2 headings across the four entry-bearing documents, each either citing its counterpart's id or carrying `status: legacy` |
| Code layout | **PASS** | the code is under `Tooling/v1.0.0/`; the tool root holds only the five documents, `Tooling/` and `Tests/` |
| Test layout | **PASS** | this directory |
| Version agreement | **PASS** | `README.md` "Current version: `v1.0.0`"; newest (only) `Tooling/` dir `v1.0.0`; newest `CHANGE_LOG.md` entry `version` field `v1.0.0`. `Tooling/v1.0.0/scrape/__init__.py` also carries `__version__ = "1.0.0"` |

### How the reciprocity check was run

**Every** level-2 heading in `KNOWN_ISSUES.md`, `CHANGE_LOG.md`,
`IMPLEMENTATIONS.md` and `TEMPLATES.md` was treated as an entry. A heading passes
only by containing an id that is itself a heading in the paired document, or by
carrying `status: legacy`. No heading was excused on the grounds that it is
"really" some other kind of thing — that reading is what the previous version of
this record used, and it is the defect logged as
[`KNOWN_ISSUES.md#reciprocity-check-narrowed-to-fit-the-re_b2d3262b`](../../KNOWN_ISSUES.md#reciprocity-check-narrowed-to-fit-the-re_b2d3262b).

Counts: 28 headings — 11 in `KNOWN_ISSUES.md`, 2 in `CHANGE_LOG.md`, 10 in
`IMPLEMENTATIONS.md`, 5 in `TEMPLATES.md`. 15 exempt under §9 (`status: legacy`,
all predating `v1.0.0`); 13 non-legacy, all citing. 0 failures.

### Disclosed deviation — heading form on legacy entries

`process.yaml: definitions.entry` requires an entry heading to be `## <id>`, the
bare id. The 15 legacy headings do not satisfy it — they are prose titles such as
`## KI-01 — One slow/broken page aborts the whole batch`. This is **not fixed**,
and it is recorded here rather than passed over: PROCESS.md §9 permits exactly
one edit to a pre-existing entry, adding `status: legacy`, so renaming their
headings is not available. `track-b.log` lists all 15 by name. Every entry
written at `v1.0.0` does satisfy the heading form.

### Id reproduction

Both id types were recomputed from the files with `sha256sum`, per
`process.yaml: definitions.issue-id` / `definitions.change-id`: issue identity is
the `summary` field alone, change identity is the `iteration` field alone,
canonicalised as trim → lowercase → collapse whitespace runs to one space → strip
trailing `. , ; : ! ?`.

| Document | Id as written | Recomputed |
|---|---|---|
| `KNOWN_ISSUES.md` | `track-b-conformance-failure-scrape-code_76631893` | reproduces (184 canonical bytes) |
| `KNOWN_ISSUES.md` | `reciprocity-check-narrowed-to-fit-the-re_b2d3262b` | reproduces (276 canonical bytes) |
| `CHANGE_LOG.md` | `a-layout-and-documents-migration-only-no_e4cf77a9` | reproduces (341 canonical bytes) |
| `CHANGE_LOG.md` | `restore-the-7-track-b-reciprocity-wordin_e86f7789` | reproduces (343 canonical bytes) |

The change entry's id previously read
`migrate-scrape-to-the-tooling-tests-layo_70b30a3b`, which reproduces from its
`summary` — not a `change-entry` field. It did not reproduce from `iteration` and
was corrected.

### Where the checker lives, and why not here

The two checks in `track-b.log` were run from a scratch script outside the
repository. PROCESS.md §4 gives a tool's directory exactly three places for
files — the five root documents, `Tooling/v<version>/` and `Tests/<version>/` —
and a Track B conformance checker fits none of them: it is not this tool's code,
so it cannot go in `Tooling/v1.0.0/` (which is also the released rollback point
and byte-for-byte untouched on this branch), and it is not a result, so it does
not belong here either. The check is therefore reproducible from the description
above but is not shipped. That is a gap in PROCESS.md §4, not in this tool, and
it is surfaced rather than worked around.

## 3. Status

Neither issue in `KNOWN_ISSUES.md` is resolved. Both are `in-progress`: the work
is committed on branch `smoke/fix-packages-scrape`, no PR has been opened, no
human approval is recorded, and both change entries' `merge_commit` fields are
empty. PROCESS.md §6 steps 5–7 are outstanding.
