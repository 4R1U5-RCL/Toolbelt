# Change log — Sprint

Every iteration made in response to an issue in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Each entry cites the issue it resolves.

| ID | Summary | Version |
|---|---|---|
| [migrate-workflows-sprint-to-the-process_695ac22d](#migrate-workflows-sprint-to-the-process_695ac22d) | Migrate to the PROCESS.md layout; create the missing canonical documents | `v1.0.0` |

---

<a name="migrate-workflows-sprint-to-the-process_695ac22d"></a>
## migrate-workflows-sprint-to-the-process_695ac22d

- **id:** `migrate-workflows-sprint-to-the-process_695ac22d`
- **resolves:** [`KNOWN_ISSUES.md#workflows-sprint-failed-track-b-conforma_e81c9e76`](KNOWN_ISSUES.md#workflows-sprint-failed-track-b-conforma_e81c9e76)
- **version:** `v1.0.0` — **no bump.** The code did not change, it moved. Per
  PROCESS.md §9, a tool that has never been versioned starts at `v1.0.0` and its
  current code becomes `Tooling/v1.0.0/`, so this iteration *establishes* the
  version rather than incrementing one.
- **merge_commit:** not recorded — not merged by this session, which runs no git
  commands. To be filled by the merging session (PROCESS.md §6 step 7).

### cause (Y)

`Workflows/Sprint` was imported from `operand-packages` before PROCESS.md §3/§4
existed, and nothing has since run Track B against imported tools.

### outcome (X)

Four of five Track B checks failed: only `README.md` of the five canonical files
existed; the code sat loose at the tool root with no `Tooling/`; no `Tests/`
directory or recorded output existed; and no document named a version. The tool
had no rollback point and no visible staleness signal.

### iteration (Z)

Conform the tool at `v1.0.0` per PROCESS.md §9 without touching behaviour.

### expected_result (V)

All five Track B checks pass, checkably:

1. **Canonical files** — all five exist at the tool root and are non-empty.
2. **Reciprocity** — the one `KNOWN_ISSUES.md` entry cites this change-id and
   this entry cites that issue-id; every `IMPLEMENTATIONS.md` entry cites a
   `TEMPLATES.md` id and every `TEMPLATES.md` entry cites an
   `IMPLEMENTATIONS.md` id.
3. **Code layout** — every implementation file sits under `Tooling/v1.0.0/`.
4. **Test layout** — `Tests/v1.0.0/` exists and holds the actual output of the
   verification attempt.
5. **Version agreement** — `README.md`, the newest `Tooling/` directory and the
   newest `CHANGE_LOG.md` entry all name `v1.0.0`.

And, as a non-regression condition: no shipped file's behaviour changes.

### change (W)

**What changed, where:**

| Change | Detail |
|---|---|
| Code moved | `agents/`, `commands/`, `docs/`, `fleet-kit/` → `Tooling/v1.0.0/` (plain `mv`, contents byte-identical) |
| `Tests/v1.0.0/` created | `run-tests.log` (captured stdout of the verification attempt) + `RESULTS.md` |
| `IMPLEMENTATIONS.md` created | 5 entries (IMP-01…IMP-05), each citing its `TEMPLATES.md` id |
| `TEMPLATES.md` created | 6 entries (T-01…T-06), each citing its `IMPLEMENTATIONS.md` id |
| `KNOWN_ISSUES.md` created | header + first entry (the Track B failure) |
| `CHANGE_LOG.md` created | header + this entry |
| `README.md` edited | added a version line naming `v1.0.0`; repointed the install block's relative paths at `Tooling/v1.0.0/`; added a pointer to the four sibling documents |

**Paths checked for breakage, and the finding.** Every shipped script and
markdown file was read before and after the move. No file in this tool resolves a
sibling by relative path: `fleet-mbox.sh` takes `FLEET_ROOT`/`FLEET_SESSION` from
the environment; `fleet-board.sh` and `fleet-doctor.sh` take the worktree as
`$1`; `fleet-triage-guard.sh` reads stdin only; `commands/fleet.md`,
`agents/fleet-triage.md` and `fleet-kit/SOP-Sprints.md` address the kit at its
**install** paths under `~/.claude/`, which the move does not affect. There is no
`sys.path` manipulation and no `dirname $0` / `BASH_SOURCE` resolution anywhere
in the tool. **The only repo-relative paths in the whole tool were the `cp` lines
in `README.md`'s install block**, and those were repointed.

**How it is verified.**

- Track B checks 1–3 and 5: inspect the tool directory listing and the five files.
- Check 4: `Tests/v1.0.0/RESULTS.md` + `run-tests.log`.
- Non-regression: no `.sh`, `.md` or `.html` file under `Tooling/v1.0.0/` was
  edited — only relocated.
- Post-move sanity: `bash -n` on all four shell scripts, recorded verbatim in
  `Tests/v1.0.0/run-tests.log`. All four parse. **This is a syntax check, not a
  test** — it is recorded as such, and no passing test result is claimed.

### known limitation of this iteration

The tool ships no test code, so PROCESS.md §5.5's end-to-end corroboration
requirement cannot be met with a suite. What corroborates *this* change is the
conformance evidence itself, which is directly checkable by listing the
directory. The missing suite is recorded as residual on the issue entry.
