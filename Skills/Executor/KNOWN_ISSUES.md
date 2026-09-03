# Known issues — Skills/Executor

Every issue found with this tool, each citing the iteration that addressed it in
[`CHANGE_LOG.md`](CHANGE_LOG.md) (PROCESS.md §3).

**Append-only** (PROCESS.md §5.1). Entries are never removed; a fix appends a new
entry carrying the version that resolved it. Ids follow `process.yaml` →
`definitions.issue-id`: `<description>_<hash8>`, hashed over the `summary` field
alone (PROCESS.md §10.3).

### Note on history

Both entries were found while building `v1.0.0`. Neither is `legacy` — no prior
version exists for them to predate, so both are bound by the §7 reciprocity
check.

| Id | Summary | Status |
|---|---|---|
| [the-executor-placeholder-was-committed-a_e6332913](#the-executor-placeholder-was-committed-a_e6332913) | The Executor placeholder was committed as `README` with no extension, failing the canonical-files check | in-progress |
| [process-gate-cannot-enforce-the-approval_de559760](#process-gate-cannot-enforce-the-approval_de559760) | `process-gate` cannot enforce the approval invariant — a free private repo has no branch protection | in-progress |

### Why both are `in-progress` and not `resolved`

`merge_commit` is empty in both cited change entries: the work sits unmerged on
branch `feat/skills-executor`. `process.yaml → definitions.issue-status` is
explicit — "`resolved` is never written while merge_commit is empty". They move to
`resolved` at PROCESS.md §6 step 7, on merge.

---

## the-executor-placeholder-was-committed-a_e6332913

| Field | Value |
|---|---|
| **id** | `the-executor-placeholder-was-committed-a_e6332913` |
| **summary** | The Executor placeholder was committed as README with no extension, so the tool fails the canonical-files check that requires README.md |
| **outcome** | `Skills/Executor` failed Track B canonical-files from the moment the directory existed. A reader following §3 finds no `README.md`, and every relative link into the tool resolves against a filename that is not there |
| **cause** | The directory was created through the GitHub web UI, which writes a bare `README` when you create a folder — a new folder needs a file to exist at all. §3's "filenames are UPPERCASE, exactly as written" rule is enforced nowhere, so nothing objected |
| **iteration** | Rename the placeholder to README.md and write the tool's real README in the same change |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#rename-the-placeholder-to-readme-md-and_2049c2a8`](CHANGE_LOG.md#rename-the-placeholder-to-readme-md-and_2049c2a8), fix-version `v1.0.0` |
| **occurrences** | 1 — found 2026-09-03 while laying out the tool |

### Outcome (X)

The tool was non-conformant at creation, and would have stayed so silently. §3
requires five canonical files; a `README` without its extension satisfies none of
them, and Track B's canonical-files check reads for `README.md` exactly.

### Cause (Y)

Creating a folder in the GitHub web UI requires creating a file inside it, and
the UI's default is a bare `README`. The mechanism is worth recording because it
will recur: **every folder created through the web UI arrives non-conformant**,
and nothing in this repo checks filenames.

### Iteration (Z)

Rename to `README.md` and write the real README in the same change, so the tool
never exists in a state where the placeholder is its documentation.

---

## process-gate-cannot-enforce-the-approval_de559760

| Field | Value |
|---|---|
| **id** | `process-gate-cannot-enforce-the-approval_de559760` |
| **summary** | process-gate cannot enforce the approval invariant because a free private repository has no branch protection |
| **outcome** | INV-8 says an executor never merges without a recorded approval, and nothing prevents exactly that. A change can pass every gate check and still be merged unreviewed, in a repo whose process document says it cannot be |
| **cause** | GitHub offers branch protection and required reviews only on paid plans for private repositories. A CI check can *observe* review state through the API but has no power to block the merge button; enforcement is a repository setting, not a workflow |
| **iteration** | Report approval as DEFER rather than PASS, and state in the conformance table that the check is reported and never enforced |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#report-approval-as-defer-rather-than-pas_5c19c849`](CHANGE_LOG.md#report-approval-as-defer-rather-than-pas_5c19c849), fix-version `v1.0.0` |
| **occurrences** | 1 — found 2026-09-03 while specifying the conformance table |

### Outcome (X)

The draft conformance table listed approval as a check alongside six that are
genuinely mechanical. Shipping it that way would have made the gate assert
something it cannot do — a green gate implying review that never happened.

### Cause (Y)

A platform constraint, not a defect in the checker. `4R1U5-RCL` is a user
account, not an organisation, and its private repos are on the free plan, where
branch protection is unavailable.

### Iteration (Z)

Make the limitation visible instead of hiding it. The check reports `DEFER` with
the reason attached, and §11 of the prose says in as many words that approval is
reported and never enforced.

### Residual

**The underlying limitation is not fixed and cannot be fixed here.** The
iteration makes the gate honest, not capable. Closing it for real needs one of:
a paid plan with required reviews, a merge queue, or moving the repo to an
organisation. Recorded so the gap stays visible rather than being mistaken for
coverage — INV-5 applied to the gate's own reporting.
