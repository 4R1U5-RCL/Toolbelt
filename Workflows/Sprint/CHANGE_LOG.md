# Change log — Sprint

Every iteration made in response to an issue in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Each entry cites the issue it resolves.

| ID | Summary | Version |
|---|---|---|
| [conform-the-tool-at-v1-0-0-per-process-m_a832777d](#conform-the-tool-at-v1-0-0-per-process-m_a832777d) | Migrate to the PROCESS.md layout; create the missing canonical documents | `v1.0.0` |

---

<a name="conform-the-tool-at-v1-0-0-per-process-m_a832777d"></a>
## conform-the-tool-at-v1-0-0-per-process-m_a832777d

- **id:** `conform-the-tool-at-v1-0-0-per-process-m_a832777d`
- **resolves:** [`KNOWN_ISSUES.md#workflows-sprint-failed-track-b-conforma_e81c9e76`](KNOWN_ISSUES.md#workflows-sprint-failed-track-b-conforma_e81c9e76)
- **version:** `v1.0.0` — **no bump.** The code did not change, it moved. Per
  PROCESS.md §9, a tool that has never been versioned starts at `v1.0.0` and its
  current code becomes `Tooling/v1.0.0/`, so this iteration *establishes* the
  version rather than incrementing one.
- **branch:** `smoke/fix-workflows-sprint`
- **merge_commit:** *(empty)* — not merged. The work is committed on
  `smoke/fix-workflows-sprint` only; merging to `main` is the owner's gate
  (PROCESS.md §5.4, §8). Because this field is empty the resolving issue entry
  reads `in-progress`, not `resolved`.

### id correction (2026-09-01)

This entry was first written with the change-id
`migrate-workflows-sprint-to-the-process_695ac22d`. That id was an orphan: neither
segment reproduced from the entry. Under `process.yaml: definitions.change-id` a
change-id's identity is the `iteration` field alone, canonicalised (trim →
lowercase → collapse whitespace → strip trailing `. , ; : ! ?`) and sha256'd,
first 8 hex chars; the description is the same field through `slug_rule`.

Recomputed from the `iteration (Z)` text below:

```
$ printf '%s' 'conform the tool at `v1.0.0` per process.md §9 without touching behaviour' | sha256sum
a832777d27391cdc1ed9cdb01a3958f09eaae1f209c907b57f1cfef34b1206f9  -
```

slug_rule over the same canonical string gives
`conform-the-tool-at-v1-0-0-per-process-m` (the 40-character truncation lands
mid-word in `process-md`, which the rule permits and then finds no trailing
hyphen to strip). Hence `conform-the-tool-at-v1-0-0-per-process-m_a832777d`.

The `id` field is immutable (`process.yaml: change-entry.immutable`), but this
entry has never been merged or released, so the correction replaces a value that
never had a released identity rather than rewriting a published one. Every
citation moved with it — the reciprocal `KNOWN_ISSUES.md` entry cites the new id
in both its `resolved_by` field and its `iteration` section.

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

**Amended 2026-09-01, before merge** (the audit of the migration run; nothing here
had been merged or released, so these correct the entry rather than rewrite a
published one):

| Amendment | Detail |
|---|---|
| change-id corrected | `..._695ac22d` → `conform-the-tool-at-v1-0-0-per-process-m_a832777d`, recomputed from the `iteration` field per `process.yaml: definitions.change-id`. See *id correction* above. Both citations in `KNOWN_ISSUES.md` moved with it |
| `status` corrected | the issue entry's status was free prose ("fixed in tree at `v1.0.0`, pending merge"), outside the closed set of seven. It now reads `in-progress` — the correct value while `merge_commit` is empty |
| `merge_commit` / branch stated truthfully | the entry now names branch `smoke/fix-workflows-sprint` and records `merge_commit` as empty. The earlier claim "this session runs no git commands" is gone; this session does commit, to that branch only |
| entry headings normalised | `IMPLEMENTATIONS.md` and `TEMPLATES.md` headings were `## IMP-01 — Install the kit…`; they are now the bare id `## IMP-01`, with the title moved to the line below (`process.yaml: definitions.entry`). `KNOWN_ISSUES.md` and `CHANGE_LOG.md` already used the bare form |
| non-entry level-2 headings removed | `## Honest gap` (IMPLEMENTATIONS) and `## Not templates` (TEMPLATES) sat among the entries, where a bare-id parser would read them as entries with no counterpart. Their text moved verbatim into each document's preamble; nothing was deleted |
| `Tests/v1.0.0/` re-recorded | `RESULTS.md` and `run-tests.log` regenerated from an actual re-run on this branch. The previous record captured the "no suite" finding but did not name the Track-B checks run in its place, which PROCESS.md §4 requires of a code-less tool. `trackb-check.py` (the checker that produced the output) is kept beside it so the result is re-runnable |

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

- All five Track B checks: run mechanically by
  [`Tests/v1.0.0/trackb-check.py`](Tests/v1.0.0/trackb-check.py); verbatim
  output in [`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log) STEP 2,
  read across in [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) §2. All
  five pass. The reciprocity check parses entries by the bare-id heading rule and
  reports the entry counts it found, so a heading it failed to parse would show
  as a missing entry rather than as a silent pass.
- Both ids reproduce from their identity fields under `sha256sum`: `run-tests.log`
  STEP 3. The retired id has no live citation: STEP 4.
- Non-regression: no `.sh`, `.md` or `.html` file under `Tooling/v1.0.0/` was
  edited — only relocated. `git diff` over `Tooling/` is empty for the 2026-09-01
  amendment.
- Post-move sanity: `bash -n` on all four shell scripts, recorded verbatim in
  `Tests/v1.0.0/run-tests.log` STEP 6. All four parse. **This is a syntax check,
  not a test** — it is recorded as such, and no passing test result is claimed.

### known limitation of this iteration

The tool ships no test code, so PROCESS.md §5.5's end-to-end corroboration
requirement cannot be met with a suite. Amended §5.5 and §8 (decisions 9 and 10)
require **recorded evidence**, not test files, and accept a recorded Track-B
conformance result for a code-less tool — which is what
`Tests/v1.0.0/RESULTS.md` is. That evidence corroborates the *conformance* this
iteration set out to achieve; it does not corroborate that the tool works, and
`RESULTS.md` §5 says so plainly. The missing suite is recorded as residual on the
issue entry and is not closed here.

`merge_commit` stays empty until the owner approves and the merge happens
(PROCESS.md §8: approval and merge are separate, and an agent never merges
without a recorded approval). No approval is recorded, so this is not an
escalation — the process is waiting at the human gate, which §5 says is not an
escalation.
