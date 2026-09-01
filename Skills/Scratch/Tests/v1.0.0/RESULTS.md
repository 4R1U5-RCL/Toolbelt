# Test results — Skills/Scratch v1.0.0

Recorded verbatim per PROCESS.md §5 invariant 6. The full captured stdout+stderr
is in [`run-tests.log`](run-tests.log); nothing in it has been edited.

| Field | Value |
|---|---|
| **Version** | `v1.0.0` |
| **Run at** | 2026-08-31T15:27:11+00:00 — the recorded run in `run-tests.log`, executed after the README edit so the log reflects the tool's final state. An identical run at 15:24:11, before that edit, produced the same 29/0/exit-0 result |
| **Command** | `bash tests/verify.sh`, executed with the working directory set to `Skills/Scratch/Tooling/v1.0.0/` |
| **Suite** | `Tooling/v1.0.0/tests/verify.sh` — the only test file this tool has |
| **Result** | **29 passed, 0 failed** · exit code `0` |
| **Environment** | GNU bash 5.2.15(1)-release (x86_64-pc-linux-gnu); git 2.39.5 |

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

## Baseline before the move, for comparison

The same suite was run from the tool's pre-migration location
(`Skills/Scratch/tests/verify.sh`, with `templates/` and `tests/` still at the
tool root) immediately before the files were moved. It reported **29 passed, 0
failed**, exit `0` — the same result. The migration therefore changed the
suite's location and one internal path, not its verdict.

## What the move broke, and the evidence it is fixed

Between those two runs the suite **failed once**, deliberately observed rather
than assumed. Run from `Tooling/v1.0.0/` before any repair:

```
grep: /studio/scratch/tb/Skills/Scratch/Tooling/v1.0.0/README.md: No such file or directory
  FAIL · README points at the shipped template
== scratch smoke: 28 passed, 1 failed ==
exit code: 1
```

Cause and fix are recorded in
[`../../CHANGE_LOG.md#migrate-skills-scratch-to-the-tooling-te_96add0eb`](../../CHANGE_LOG.md).
The recorded run above, with that check reading `PASS`, is the evidence.
