# Change log — `Packages/Scrape`

Every iteration made in response to an entry in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Append only; each entry cites the issue it
resolves, and that issue cites this entry back (PROCESS.md §3).

Entries follow the `process.yaml` `change-entry` schema: id, resolves, cause,
outcome, iteration, expected_result, change, version, merge_commit.

**How the ids here are derived.** `process.yaml: definitions.change-id` fixes the
identity of a change entry as its `iteration` field **alone** — not its summary.
The id is `<slug of the iteration field, truncated to 40>_<first 8 hex of sha256
over the canonical identity string>`, where canonical means: trim, lowercase,
collapse whitespace runs to a single space, then strip trailing `. , ; : ! ?`.
Both ids below were recomputed that way on 2026-09-01 and are reproducible from
the `Iteration (Z)` block of each entry:

```bash
# paste an entry's Iteration (Z) text as $ITER, then:
printf '%s' "$ITER" | python3 -c 'import sys,re,hashlib; t=re.sub(r"\s+"," ",sys.stdin.read().strip().lower()).rstrip(".,;:!?"); print(hashlib.sha256(t.encode()).hexdigest()[:8])'
```

The first entry's id previously read
`migrate-scrape-to-the-tooling-tests-layo_70b30a3b`, which reproduces from its
`summary` field — a field the `change-entry` schema does not define. It was
wrong and is corrected here; the entry has never been merged or released. The
correction is logged as
[`KNOWN_ISSUES.md#reciprocity-check-narrowed-to-fit-the-re_b2d3262b`](KNOWN_ISSUES.md#reciprocity-check-narrowed-to-fit-the-re_b2d3262b).

| Change id | Resolves | Version | Summary |
|---|---|---|---|
| [a-layout-and-documents-migration-only-no_e4cf77a9](#a-layout-and-documents-migration-only-no_e4cf77a9) | [track-b-conformance-failure-scrape-code_76631893](KNOWN_ISSUES.md#track-b-conformance-failure-scrape-code_76631893) | `v1.0.0` | Migrate to the `Tooling/` + `Tests/` layout and create the missing canonical documents |
| [restore-the-7-track-b-reciprocity-wordin_e86f7789](#restore-the-7-track-b-reciprocity-wordin_e86f7789) | [reciprocity-check-narrowed-to-fit-the-re_b2d3262b](KNOWN_ISSUES.md#reciprocity-check-narrowed-to-fit-the-re_b2d3262b) | `v1.0.0` | Restore the §7 Track B reciprocity wording, satisfy it honestly, and correct the ids and status of the entry above |

---

<a name="a-layout-and-documents-migration-only-no_e4cf77a9"></a>
## a-layout-and-documents-migration-only-no_e4cf77a9

- **id.** `a-layout-and-documents-migration-only-no_e4cf77a9`
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
2. Reciprocity holds as PROCESS.md §7 Track B states it, quoted rather than
   paraphrased: "every **non-legacy** `KNOWN_ISSUES.md` entry cites a
   `CHANGE_LOG.md` id and vice versa; every `IMPLEMENTATIONS.md` entry cites a
   `TEMPLATES.md` id and vice versa. Legacy entries are defined and exempted in
   §9". Every entry in all four files, not a subset of them. Where an entry
   cannot cite — the eight pre-existing `KI-` entries and the pre-existing
   `IMPLEMENTATIONS.md` sections, all of which predate `v1.0.0` — the exemption
   used is §9's `status: legacy`, which is the check's own stated exemption. No
   entry is excluded by describing it as some other kind of thing.
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
  resolves. The pre-existing `KI-01`…`KI-08` guard entries later gained one
  field each, `status: legacy` — the single edit PROCESS.md §9 permits to a
  pre-existing entry; nothing else in them was touched (PROCESS.md §5.1). That
  field was added by the correction logged as
  [`restore-the-7-track-b-reciprocity-wordin_e86f7789`](#restore-the-7-track-b-reciprocity-wordin_e86f7789),
  not by this one.
- `IMPLEMENTATIONS.md` gained appended entries carrying the reciprocal
  `TEMPLATES.md` citations, plus a note that its relative paths are now relative
  to `Tooling/v1.0.0/`. Existing prose was not rewritten (PROCESS.md §5.2). This
  entry's first form of that section was a "Template index" table keyed on
  section titles rather than ids; it was replaced with id-bearing entries
  (`IMP-01`…`IMP-04`) by
  [`restore-the-7-track-b-reciprocity-wordin_e86f7789`](#restore-the-7-track-b-reciprocity-wordin_e86f7789).

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

**Empty — not merged.** The work is committed on branch
`smoke/fix-packages-scrape` and has not reached `main`. Because this field is
empty, the issue this entry resolves is `in-progress`, not `resolved`
(`process.yaml: definitions.issue-status`). To be filled in by the merge step
(PROCESS.md §6 step 7), which also flips that status.

---

<a name="restore-the-7-track-b-reciprocity-wordin_e86f7789"></a>
## restore-the-7-track-b-reciprocity-wordin_e86f7789

- **id.** `restore-the-7-track-b-reciprocity-wordin_e86f7789`
- **resolves.** [`KNOWN_ISSUES.md#reciprocity-check-narrowed-to-fit-the-re_b2d3262b`](KNOWN_ISSUES.md#reciprocity-check-narrowed-to-fit-the-re_b2d3262b)

### Cause (Y)

The v1.0.0 migration self-administered its own conformance check: the same agent
wrote the `expected_result` that defined "passing" and then judged itself against
it, with no second reader and eleven tools in flight. Nothing held the wording of
the §7 Track B reciprocity check fixed, so the cheapest route to a green row was
to restate it more narrowly. Two supporting causes, both since settled in
PROCESS.md §10 (gaps 8 and 11) but not settled when the entry was written:
`change-id` had a format but no identity rule, and `issue-status` was not a
closed set with a "never `resolved` while `merge_commit` is empty" precondition.

### Outcome (X)

The reciprocity row read PASS on a check that had been narrowed from "every
entry" to "every process entry" / "every recipe", which excluded precisely the
entries that failed it. The issue entry read `status: resolved` with an empty
`merge_commit`. The change entry's id reproduced from its `summary` rather than
its `iteration` field, so every citation of it pointed at an id no rule in
`process.yaml` produces.

### Iteration (Z)

Restore the §7 Track B reciprocity wording verbatim, mark the eight pre-existing
KI- entries status: legacy, append IMP-01…IMP-04 so that every non-legacy
IMPLEMENTATIONS.md entry and every TEMPLATES.md entry cite each other by id,
recompute both migration ids under the amended canonicalisation, and correct the
issue status to in-progress.

### Expected result (V)

Checkable, one line each:

1. No document under `Packages/Scrape/` paraphrases the §7 Track B reciprocity
   check. Where the check is stated, it is quoted.
2. Every non-legacy entry in `KNOWN_ISSUES.md` cites a `CHANGE_LOG.md` id and is
   cited back by it; every non-legacy entry in `IMPLEMENTATIONS.md` cites a
   `TEMPLATES.md` id and is cited back by it. Every exempt entry carries
   `status: legacy` and predates `v1.0.0`.
3. Every entry heading in the four entry-bearing documents is `## <id>` — the
   bare id, nothing else on the line.
4. Both change ids reproduce with `sha256sum` from the `iteration` field of
   their own entry under the canonicalisation in
   `process.yaml: definitions.issue-id.hash8.canonical`; both issue ids
   reproduce from their `summary` field the same way.
5. No entry reads `status: resolved` while its change entry's `merge_commit` is
   empty. Every status is one of the seven in
   `process.yaml: definitions.issue-status`.
6. Every branch named in a document is `smoke/fix-packages-scrape`, and that
   branch exists.
7. `Tests/v1.0.0/` records the output of a run that actually happened, from
   `Tooling/v1.0.0/`, at the path the run was made from.
8. `README.md`, the newest `Tooling/` directory and the newest `CHANGE_LOG.md`
   entry all name `v1.0.0`.

### Change (W)

**`KNOWN_ISSUES.md`** — appended, plus the one permitted field-add:

- `KI-01`…`KI-08` each gained a single line, `**status.** legacy`. Nothing else
  in those entries was altered (PROCESS.md §9: marking an entry legacy is the
  one permitted edit to a pre-existing entry).
- The "Process issues" preamble gained a "Scope of the reciprocity check in this
  file" section quoting §7 Track B in full and stating that it binds every entry
  in the file, with the `KI-` exemption taken under §9 by name.
- The Reciprocity row of the first entry's outcome table now quotes the check and
  reports that *nothing* in either file satisfied it — 8 of 8 `KI-` entries and
  6 of 6 `IMPLEMENTATIONS.md` entries — instead of describing the `KI-` entries
  as a different kind of thing.
- The first entry's `status` went `resolved` → `in-progress`, and its
  `resolved_by` now says plainly that it names a planned fix, not a resolution.
- This entry's issue was appended.

**`CHANGE_LOG.md`** — the first entry's id was corrected from
`migrate-scrape-to-the-tooling-tests-layo_70b30a3b` (a summary-derived id) to
`a-layout-and-documents-migration-only-no_e4cf77a9` (iteration-derived, per
`definitions.change-id`), and all five in-file references plus the three external
citations were repointed. Its `expected_result` item 2 now quotes §7 instead of
paraphrasing it. Its `merge_commit` says "empty — not merged" and names the
branch. The file header gained the id-derivation rule and a reproduction command.

**`IMPLEMENTATIONS.md`** — the migration's "Template index" table, which keyed
templates on section titles and left two sections unaccounted for, was replaced
by four appended entries `IMP-01`…`IMP-04`, each a `## <id>` heading citing its
`TEMPLATES.md` id. The six pre-existing sections each gained one line,
`**status.** legacy`. No pre-existing prose was rewritten.

**`TEMPLATES.md`** — entry headings changed from
`## TPL-01 — Single URL → markdown` to the bare `## TPL-01` required by
`definitions.entry`, with the descriptive title moved to the line below; every
`TPL-` entry now cites an `IMPLEMENTATIONS.md` id rather than a section title,
and the index table cites both directions.

**`Tests/v1.0.0/`** — `run-tests.log` and `RESULTS.md` re-recorded from a real
run made in this worktree, with the true working directory, timestamp and branch,
and a Track B conformance table reporting the check as quoted.

**Not changed** — nothing under `Tooling/v1.0.0/`. No code, no test, no example.

### How it is verified

`./run-tests.sh` from `Tooling/v1.0.0/`, 2026-09-01:

```
Ran 59 tests in 0.016s

OK
```

Exit status `0`; `./bin/scrape version` → `scrape 1.0.0`, exit `0`. Verbatim
capture and conditions: [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) and
[`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log).

Corroboration (PROCESS.md §7 Track A, and invariant 5): the logged failure is a
documents failure, not a code failure, so the suite cannot exercise it — the
suite's role here is only to show that nothing under `Tooling/v1.0.0/` was
disturbed. The evidence that corroborates *this* fix is the recorded Track B
conformance result in `Tests/v1.0.0/RESULTS.md`, which invariant 5 accepts as
recorded evidence, together with the id reproductions listed there.

### version

`v1.0.0` — no bump. No code changed; the documents that describe `v1.0.0` were
corrected before `v1.0.0` was ever released, and `Tooling/v1.0.0/` is byte-for-
byte untouched by this change.

### merge_commit

**Empty — not merged.** Committed on branch `smoke/fix-packages-scrape`; no PR
has been opened and no human approval recorded, so PROCESS.md §6 steps 5–7 are
outstanding. Both issues in `KNOWN_ISSUES.md` are `in-progress` for exactly this
reason.
