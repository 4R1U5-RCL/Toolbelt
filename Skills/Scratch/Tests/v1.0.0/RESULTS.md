# Test results — Skills/Scratch v1.0.0

Recorded verbatim per PROCESS.md §5 invariant 6. The full captured stdout+stderr
is in [`run-tests.log`](run-tests.log); nothing in it has been edited. That file
holds two runs — the current record (RUN 2) and the 2026-08-31 migration run
(RUN 1), preserved byte-for-byte rather than overwritten.

| Field | Value |
|---|---|
| **Version** | `v1.0.0` |
| **Run at** | 2026-09-01T04:35:07+00:00 — RUN 2 in `run-tests.log`, executed on branch `smoke/fix-skills-scratch` after the conformance corrections to the canonical documents. No tooling file was changed by those corrections |
| **Command** | `bash tests/verify.sh`, executed with the working directory set to `Skills/Scratch/Tooling/v1.0.0/` |
| **Suite** | `Tooling/v1.0.0/tests/verify.sh` — the only test file this tool has |
| **Result** | **29 passed, 0 failed** · exit code `0` |
| **Environment** | GNU bash 5.2.15(1)-release (x86_64-pc-linux-gnu); git 2.39.5 |
| **Prior run** | 2026-08-31T15:27:11+00:00 (RUN 1), the migration run: **29 passed, 0 failed** · exit `0`. RUN 2 reproduces it exactly, so the migration's recorded verdict is corroborated by an independent execution |

## What was run

There is **no `run-tests.sh` in this tool** — it has never had one. The suite was
therefore invoked directly, which is what the tool's own README documents as its
committed self-check.

`tests/verify.sh` is a shell smoke test in three parts. It makes a throwaway
directory with `mktemp -d`, removes it on exit, and touches nothing in this
repository:

1. **Artifact checks (11).** `templates/scratch.gitignore` exists and is
   non-empty; it contains each documented surface and secret pattern
   (`scratch/`, `.runstate/`, `.claude/worktrees/`, `clients/`, `labs/`, `.env`,
   `*.key`, `*.pem`, `_token`); and the tool's `README.md` names the shipped
   template.
2. **Real-repo behaviour (13).** It initialises a throwaway git repository inside
   the sandbox, copies the shipped block in as its `.gitignore`, creates a file
   on every surface plus real source, and asserts via `git check-ignore` that the
   ten scratch/secret paths are ignored and that `src/app.ts`, `README.md` and
   `.gitignore` are not.
3. **Staging behaviour (5).** It runs `git add -A` in the sandbox repo and
   asserts that only the source files are staged — no `.env`, no `*.pem` /
   `*.key` / `*_token`, nothing under `scratch/`, `clients/`, `.runstate/` or
   `.claude/`.

The git commands in part 2 and part 3 run **only** against the sandbox
repository under `$SB` (a `mktemp -d` path). No git command was run against this
checkout.

## Verbatim outcome

```
== scratch smoke: 29 passed, 0 failed ==
exit code: 0
```

## Earlier runs — reported by the 2026-08-31 migration, not re-observed here

The three runs below were recorded by the migration session. The 2026-09-01
correction did **not** re-execute them: the pre-move layout and the unrepaired
script no longer exist on this branch, so re-running them would mean recreating
them. They are reported here as that session's record, attributed rather than
restated as first-hand evidence (§5 invariant 6). Only the run in the table
above, and RUN 1 preserved in `run-tests.log`, are runs whose raw output this
file holds.

**Baseline before the move.** The same suite run from the tool's pre-migration
location (`Skills/Scratch/tests/verify.sh`, with `templates/` and `tests/` still
at the tool root), immediately before the files were moved. Reported: **29
passed, 0 failed**, exit `0` — the same verdict. The migration therefore changed
the suite's location and one internal path, not its result.

**What the move broke, and the evidence it is fixed.** Between those runs the
suite **failed once**, deliberately observed by that session rather than assumed.
Run from `Tooling/v1.0.0/` before any repair, it reported:

```
grep: /studio/scratch/tb/Skills/Scratch/Tooling/v1.0.0/README.md: No such file or directory
  FAIL · README points at the shipped template
== scratch smoke: 28 passed, 1 failed ==
exit code: 1
```

Cause and fix are recorded in
[`../../CHANGE_LOG.md#move-the-implementation-into-tooling-v1_c96a11ad`](../../CHANGE_LOG.md#move-the-implementation-into-tooling-v1_c96a11ad).
The recorded run above, with that check reading `PASS`, is the evidence.
