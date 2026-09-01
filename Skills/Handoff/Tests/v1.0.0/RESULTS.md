# Test results — Skills/Handoff v1.0.0

| | |
|---|---|
| **Version** | v1.0.0 |
| **Run at** | 2026-09-01, 04:32 UTC (re-run on branch `smoke/fix-skills-handoff`) |
| **Command** | `bash tests/verify.sh`, from `Skills/Handoff/Tooling/v1.0.0/` |
| **Outcome** | **15 passed, 0 failed** — exit code `0` |
| **Full output** | [run-tests.log](run-tests.log) |
| **Change** | [CHANGE_LOG.md#bring-the-tool-into-3-4-conformance-at-v_54324955](../../CHANGE_LOG.md#bring-the-tool-into-3-4-conformance-at-v_54324955) |
| **Issue** | [KNOWN_ISSUES.md#skills-handoff-fails-track-b-conformance_761fac80](../../KNOWN_ISSUES.md#skills-handoff-fails-track-b-conformance_761fac80) |

## What was run

This tool has **no `run-tests.sh`**. Its suite is a single shell script,
`Tooling/v1.0.0/tests/verify.sh`, invoked directly with `bash`. It is offline:
it builds a sandbox `HOME` under `mktemp -d`, installs the package into it, and
removes it on exit — the real `~/.claude` is never touched.

Fifteen assertions across seven groups: install (2), the fail-closed template
guard — present / missing / empty (3), the 4h scope rule — empty dir / recent /
stale (3), the filename convention (1), end-to-end generation and section
conformance (4), memory-link degradation to `None` (1), write-scope (1).

Verbatim result line:

```
== handoff smoke: 15 passed, 0 failed ==
```

`run-tests.log` is the unedited stdout+stderr of the run named in the table
above, captured by redirecting the invocation to the file.

## Environment

```
Linux 6.6.135-09383-g1140e4f27e24 x86_64
GNU bash, version 5.2.15(1)-release (x86_64-pc-linux-gnu)
```

## Track B — conformance result

Recorded because the issue this version answers is a **layout** failure, and
PROCESS.md §5.5 / §8 / §10.10 make a recorded Track-B result the evidence for
that class. Checked on branch `smoke/fix-skills-handoff`, 2026-09-01:

| Check | Result |
|---|---|
| Canonical files | **PASS** — all five of §3 exist at the tool root and are non-empty |
| Reciprocity | **PASS** — the one `KNOWN_ISSUES.md` entry cites `CHANGE_LOG.md#bring-the-tool-into-3-4-conformance-at-v_54324955` and that entry's `resolves` cites it back; `IMPL-01…04` each cite a `TMPL-*` id and `TMPL-01/02` each cite back. No entry is `legacy` — this tool had only a `README.md` before the migration, so every entry postdates its first conformant version |
| Code layout | **PASS** — `commands/`, `templates/`, `tests/` under `Tooling/v1.0.0/`; nothing left at the tool root but the five documents |
| Test layout | **PASS** — this directory, `Tests/v1.0.0/`, holds `RESULTS.md` + `run-tests.log` for the current version |
| Version agreement | **PASS** — `README.md` says v1.0.0, the newest `Tooling/` directory is `v1.0.0`, and the newest (only) `CHANGE_LOG.md` entry names v1.0.0 |
| Entry form (`definitions.entry`) | **PASS** — every entry heading in the four prose documents is `## <bare id>` |
| Status vocabulary (`definitions.issue-status`) | **PASS** — the sole status is `in-progress`, a member of the closed set of seven |
| `resolved` ⇒ `merge_commit` | **PASS** — no entry reads `resolved`; nothing has merged, and `merge_commit` is recorded as empty |

## Notes

- The suite was also run from an unrelated working directory (`/`) by absolute
  path on 2026-09-01 and exited `0`, confirming it does not depend on the
  caller's `cwd`.
- The 2026-08-31 migration run recorded the same result (15 passed / 0 failed,
  exit 0) from the same script; that log is in git history. `run-tests.log` was
  replaced with the 2026-09-01 run because that is the run this branch can
  vouch for, and because the old log's `$ cd` line named a path outside this
  worktree.
- Scope limit, stated plainly: this exercises the **shipped package** — file
  placement, the guard logic, the scope arithmetic, the filename form and
  section conformance. It does **not** invoke Claude Code or produce a real
  handoff, so it cannot corroborate the curation behaviour described in
  `commands/handoff.md` steps 4–5.
- Not verified here: the claim in the 2026-08-31 record that the same suite was
  run *before* the migration from the old tool root. That tree no longer exists
  on this branch, so the claim is left out of this document rather than
  restated.
