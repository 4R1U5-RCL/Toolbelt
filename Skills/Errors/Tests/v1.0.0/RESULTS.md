# Test results — Skills/Errors v1.0.0

Recorded verbatim per PROCESS.md §5.6. Nothing here is edited or summarised in a way that
changes the outcome; the raw output is [`run-tests.log`](run-tests.log).

| | |
|---|---|
| **Version** | `v1.0.0` |
| **What was run** | `bash Tooling/v1.0.0/tests/verify.sh` |
| **There is no `run-tests.sh`** | This tool ships one test script, `tests/verify.sh`, and no `run-tests.sh`. The script was run directly. |
| **Working directory** | `/studio/scratch/tb/Skills/Errors` (the tool root, after the move) |
| **When** | 2026-08-31, ~15:20 UTC |
| **Exit code** | `0` |
| **Outcome** | `== errors smoke: 32 passed, 0 failed ==` |

## What was run and why here

`Tooling/v1.0.0/tests/verify.sh` is the tool's committed self-check. It performs 32
assertions: static structure checks on the three shipped templates (presence, the hub's
Index / Part 1 / Part 3 / absence of Part 2 / seeded `PAT-1..3` / the two drift-fixes, the
area template's hub binding and drift-fixes, all six incident fields with Signature first,
and a single-entry-style check), then dynamic checks against a fixture registry built in a
temp directory — signature greppability, the compact-grep-vs-`ID-[0-9]+` fragmentation
caveat, index↔catalog consistency including a deliberately dangling row, and a duplicate-ID
guard that reproduces the live `IN-38` bug.

It was run **after** the migration, from the tool root, to confirm the move into
`Tooling/v1.0.0/` did not break it. The script resolves its own directory via
`BASH_SOURCE` and reads the templates from `$HERE/..`, so moving `tests/` and `templates/`
together preserved the relationship; no path repair was needed and none was made.

The run was also executed once from inside `Tooling/v1.0.0/` before this recording, with
the same result (32 passed, 0 failed, exit 0).

## Verbatim output

```
$ bash Tooling/v1.0.0/tests/verify.sh
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

The suite exercises the **templates**, which is what this tool is. It does not — and
cannot — test the §9 migration itself; that is corroborated by the layout being verifiable
in the tree (`Tooling/v1.0.0/`, `Tests/v1.0.0/`, five canonical files at the tool root) and
by this suite still passing unchanged from its new location, which is the specific risk the
move introduced.
