# Test results — Skills/Errors v1.0.0

Recorded verbatim per PROCESS.md §5.6 / invariant 6. Nothing here is edited or summarised
in a way that changes the outcome; the raw output is [`verify.log`](verify.log).

| | |
|---|---|
| **Version** | `v1.0.0` |
| **Branch** | `smoke/fix-skills-errors` |
| **Command** | `bash tests/verify.sh` |
| **Working directory** | `Skills/Errors/Tooling/v1.0.0/` |
| **When** | 2026-09-01 |
| **Exit code** | `0` |
| **Outcome** | `== errors smoke: 32 passed, 0 failed ==` |

## There is no `run-tests.sh`

`process.yaml: branches.test_decision` names `./run-tests.sh` as the generic runner. This
tool does not have one and never has. It ships exactly one test script,
`Tooling/v1.0.0/tests/verify.sh`, and that script is the whole suite; it is invoked
directly. The log file in this directory was named `run-tests.log` by the 2026-08-31
migration, which implied a runner that does not exist; it is now `verify.log`.

## What was run and why here

`tests/verify.sh` is the tool's committed self-check. It performs 32 assertions: static
structure checks on the three shipped templates (presence, the hub's Index / Part 1 /
Part 3 / absence of Part 2 / seeded `PAT-1..3` / the two drift-fixes, the area template's
hub binding and drift-fixes, all six incident fields with Signature first, and a
single-entry-style check), then dynamic checks against a fixture registry built in a temp
directory — signature greppability, the compact-grep-vs-`ID-[0-9]+` fragmentation caveat,
index↔catalog consistency including a deliberately dangling row, and a duplicate-ID guard
that reproduces the live `IN-38` bug.

It was run from inside `Tooling/v1.0.0/` to confirm the §9 migration's move did not break
it. The script resolves its own directory via `BASH_SOURCE` and reads the templates from
`$HERE/..`, so moving `tests/` and `templates/` together preserved the relationship; no
path repair was needed and none was made.

**Relation to the migration's record.** The 2026-08-31 migration recorded the same suite
run from the tool root as `bash Tooling/v1.0.0/tests/verify.sh`. This 2026-09-01 run, from
the version directory, produced output **byte-identical** to that recorded log (verified
with `diff`), so the earlier record is corroborated rather than merely restated.

## Verbatim output

```
$ cd Skills/Errors/Tooling/v1.0.0
$ bash tests/verify.sh
  PASS · template present: ERRORS_AND_FINDINGS.md.template
  PASS · template present: errors-area.md.template
  PASS · template present: incident-entry.md.template
  PASS · hub: grep-first purpose block
  PASS · hub: Index table
  PASS · hub: Part 1 (recurring classes)
  PASS · hub: Part 3 (open items)
  PASS · hub: intentionally NO Part 2
  PASS · hub: seed PAT-1/2/3 present
  PASS · hub drift-fix: no hardcoded PAT range
  PASS · hub drift-fix: compile-stamp clarified
  PASS · area: binds to hub
  PASS · area: states entry format
  PASS · area: Open items section
  PASS · area drift-fix: duplicate-ID guard note
  PASS · area drift-fix: PAT-* not hardcoded range
  PASS · entry has field: Signature
  PASS · entry has field: Cause
  PASS · entry has field: Fix
  PASS · entry has field: Guard
  PASS · entry has field: Status
  PASS · entry has field: Source
  PASS · entry: Signature is the FIRST field
  PASS · style standardized: no compact **XX-N entries
  PASS · greppable: signature string locates the incident
  PASS · caveat: '^\*\*BE-' finds only the 1 compact entry (misses headers)
  PASS · reliable locator: BE-[0-9]+ finds all 3 IDs
  PASS · index link resolves (errors/backend.md exists)
  PASS · dangling index row detected (errors/ghost.md missing)
  PASS · restored: index clean again
  PASS · clean catalog has no duplicate IDs
  PASS · guard: duplicate BE-2 is detected

== errors smoke: 32 passed, 0 failed ==
$ echo $?
0
```

## Scope of what this corroborates

The suite exercises the **templates**, which is what this tool is. It does not — and cannot
— test the §9 migration itself, nor the document corrections made on this branch. Those are
Track B conformance matters, recorded below.

## Track B conformance — recorded result

PROCESS.md §5.5 as amended by decision 10 accepts a recorded Track-B conformance result as
evidence. Checked on branch `smoke/fix-skills-errors`, 2026-09-01, against the tree:

| Check | Result | How it was checked |
|---|---|---|
| Canonical files | **PASS** | all five of §3 exist at `Skills/Errors/` and are non-empty |
| Code layout | **PASS** | the tool's code (`templates/`, `tests/`) sits under `Tooling/v1.0.0/`; nothing remains at the tool root |
| Test layout | **PASS** | `Tests/v1.0.0/` holds `RESULTS.md` + `verify.log` for the current version |
| Version agreement | **PASS** | `README.md` names `v1.0.0`; newest (only) `Tooling/` dir is `v1.0.0`; newest `CHANGE_LOG.md` entry records `version: v1.0.0` |
| Reciprocity | **PASS** | both non-legacy issue↔change pairs cite each other by id; all four `imp-*` entries cite a `tpl-*` id and all three `tpl-*` entries cite an `imp-*` id |
| Status vocabulary | **PASS** | every `status` value in `KNOWN_ISSUES.md` is in the closed set of seven; neither reads `resolved`, because both `merge_commit` fields are empty |
| Entry heading form | **PASS** | every level-2 entry heading in `KNOWN_ISSUES.md`, `CHANGE_LOG.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md` is the bare id, and every `FILE.md#<id>` citation resolves to one |
| Id reproduction | **PASS** | all four ids recomputed with `sha256sum` under the amended canonicalisation (§10.14) and the amended change-id identity rule (§10.8); all four reproduce — see below |
| Branch claims | **PASS** | every branch statement about *this* work names `smoke/fix-skills-errors`, which is the branch checked out (`git branch --show-current`). The two remaining occurrences of the old "sits on a branch" wording are explicitly attributed quotations of the defect being recorded, in the `outcome` of `skills-errors-migration-entries-violate_329e05c5` and the `outcome` of its change entry |

There are **no `legacy` entries** in this tool: it had only a `README.md` before the
migration, so no entry predates its first conformant version and none is exempt from
reciprocity.

### Id reproduction

Canonicalisation: trim → lowercase → collapse whitespace runs to one space → strip trailing
`. , ; : ! ?`. issue-id identity is the `summary` field alone (§10.3); change-id identity is
the `iteration` field alone (§10.8). hash8 = first 8 hex chars of `sha256sum` over that
canonical string.

| id | Identity field | Recomputed hash8 | Matches |
|---|---|---|---|
| `skills-errors-fails-track-b-conformance_4b9a21ed` | issue `summary` | `4b9a21ed` | yes |
| `migrate-skills-errors-to-the-process-md_58690b69` | change `iteration` | `58690b69` | yes |
| `skills-errors-migration-entries-violate_329e05c5` | issue `summary` | `329e05c5` | yes |
| `correct-the-skills-errors-migration-entr_fc96ca88` | change `iteration` | `fc96ca88` | yes |

The second row is the one the amendment put at risk: the migration derived that id from a
`summary` field, which is not a `change-entry` field at all and is no longer the identity.
The field was corrected to carry the statement of the planned iteration Z, and the id is
unchanged because the corrected `iteration` field holds the exact string that had been
hashed. This is recorded plainly rather than presented as a coincidence.

## Not covered

- No test exercises the documents themselves; the Track B table above is a recorded manual
  check, not an automated one. There is no conformance linter in this repo.
- The suite is a self-check of the shipped templates. It cannot corroborate that a project
  which *adopts* the templates then follows the discipline.
