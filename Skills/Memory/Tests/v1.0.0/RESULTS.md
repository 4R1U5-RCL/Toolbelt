# Test results — Skills/Memory v1.0.0

## What was run

`Tooling/v1.0.0/tests/verify.sh` — the package's only test entrypoint. There is
**no `run-tests.sh`** in this tool; `verify.sh` is what the README names as the
committed self-check. It is an offline smoke test: it sandboxes a temp dir,
installs the two shipped templates, cuts a fixture memory directory from them
with `tests/mem_tool.py build`, then lints the result (`mem_tool.py lint`) for
frontmatter validity, the index-is-recall invariant, wikilink resolution, and a
deliberate drift demo (un-indexed entry caught, then fixed).

Command, run from the version directory:

```
cd /studio/scratch/tb-wt/skills-memory/Skills/Memory/Tooling/v1.0.0 && bash tests/verify.sh
```

## When

2026-09-01, on branch `smoke/fix-skills-memory` in the worktree
`/studio/scratch/tb-wt/skills-memory`. `python3` and `bash` only; no network, no
credentials.

## Outcome — verbatim

```
== memory smoke: 18 passed, 0 failed ==
exit=0
```

Full captured output: [`run-tests.log`](run-tests.log) — the complete stdout of
the command above, unedited.

## Notes

- The suite was also run from the tool root as
  `bash Tooling/v1.0.0/tests/verify.sh`. Output was byte-identical to
  `run-tests.log` below the command line (18 passed, 0 failed, `exit=0`), so the
  suite does not depend on the caller's working directory.
- **No path repair was needed** by the migration. `verify.sh` resolves its own
  location from `BASH_SOURCE` (`HERE=…/tests`, `PKG="$HERE/.."`) and reads the
  templates as `$PKG/templates/`, so moving `tests/` and `templates/` together
  into `Tooling/v1.0.0/` preserved the relationship. `mem_tool.py` does no
  `sys.path` manipulation and takes all paths as arguments.
- This is a conformance/layout migration, so the suite corroborates only that
  the code still runs where it now lives. It does not exercise any logged
  functional error, because none was logged — the issue recorded in
  `KNOWN_ISSUES.md` for this change is a Track B conformance failure. Under
  PROCESS.md §5 invariant 5 as amended (decision 10), the evidence for that
  issue is the recorded Track-B conformance result below, not the smoke suite.

## Track B conformance result (2026-09-01, branch `smoke/fix-skills-memory`)

Run against `Skills/Memory` as it now stands, per PROCESS.md §7 Track B.

| Check | Verdict | Evidence |
|---|---|---|
| Canonical files | PASS | `README.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md`, `CHANGE_LOG.md` all present at the tool root and non-empty |
| Reciprocity | PASS | `KNOWN_ISSUES.md#skills-memory-failed-track-b-conformance_6cdef98b` ↔ `CHANGE_LOG.md#migrated-skills-memory-to-the-tooling-v1_16012fef` cite each other; the three `IMPLEMENTATIONS.md` entries (`new-memory-directory`, `record-a-memory`, `drift-check`) and the two `TEMPLATES.md` entries (`memory-md-template`, `memory-entry-md-template`) cite each other by id in both directions. No entry in this tool is `legacy`, so none is exempt |
| Code layout | PASS | all tool code and both shipped templates sit under `Tooling/v1.0.0/`; the tool root holds only the five `.md` files, `Tooling/` and `Tests/` |
| Test layout | PASS | this directory, `Tests/v1.0.0/`, holds `RESULTS.md` and `run-tests.log` for the current version |
| Version agreement | PASS | `README.md` names `v1.0.0`; the only (therefore newest) `Tooling/` directory is `v1.0.0`; the newest `CHANGE_LOG.md` entry names `v1.0.0` |

Ids were recomputed with `sha256sum` under the canonicalisation in
`process.yaml: definitions.issue-id.hash8` (trim → lowercase → collapse
whitespace → strip trailing `. , ; : ! ?`). Both reproduce unchanged:
`6cdef98b` from the issue `summary`, `16012fef` from the change `iteration`
field. The change id reproduces only because the trailing full stop on the
`iteration` field is stripped.
