# Known issues — Skills/Errors

Every issue found with **this tool** (the templates and their self-check), in the
`PROCESS.md` §6 entry format. Append-only (PROCESS.md §5.1): entries are never rewritten,
and a fix appends the version that resolved it. Each entry cites the
[`CHANGE_LOG.md`](CHANGE_LOG.md) entry that answers it.

An entry is delimited by a level-2 heading whose text is the bare issue-id — no backticks,
no title, nothing else on the line (`process.yaml: definitions.entry`). The heading text is
the anchor a `KNOWN_ISSUES.md#<id>` citation resolves against.

`status` is drawn from the closed set of seven in `process.yaml:
definitions.issue-status` — `open, planned, in-progress, resolved, escalated, legacy,
wont-fix`. No other string is valid, and `resolved` is never written while `merge_commit`
is empty.

Neither entry below is `legacy`: this tool had only a `README.md` before the 2026-08-31
migration, so it has no pre-conformance entries, and both entries here are bound by the
§7 Track B reciprocity check.

> Not to be confused with the **"Known issues / caveats"** section of
> [`README.md`](README.md), which records defects of the *live studio registry this tool
> was distilled from* — not of the tool itself.

---

## skills-errors-fails-track-b-conformance_4b9a21ed

- **id:** `skills-errors-fails-track-b-conformance_4b9a21ed`
- **summary:** Skills/Errors fails Track B conformance: four canonical documents missing, code not under Tooling/, no recorded results under Tests/
- **occurred_at:** 2026-08-31
- **source:** Track B conformance check (PROCESS.md §7) run against `Skills/Errors` during
  the §9 migration; independently recorded in the PROCESS.md §9 backlog table, whose
  `Skills/Errors` row reads README ✅ and IMPLEMENTATIONS / TEMPLATES / KNOWN_ISSUES /
  CHANGE_LOG / Tooling / Tests all ❌.
- **outcome:** The tool could not release a new version (PROCESS.md §7: "a tool failing
  Track B cannot release a new version"), and four of the five Track B checks failed:
  - *Canonical files* — only `README.md` existed. `IMPLEMENTATIONS.md`, `TEMPLATES.md`,
    `KNOWN_ISSUES.md` and `CHANGE_LOG.md` were all absent, so there was no record of how
    the tool is applied, no catalog of its templates, nowhere to log an issue against it,
    and nowhere to log an iteration.
  - *Code layout* — the tool's code sat at the tool root as `templates/` and `tests/`, not
    under `Tooling/v<version>/`. With no released version directory there was **no
    in-repo rollback point** (PROCESS.md §4/§5 safeguard 1).
  - *Test layout* — no `Tests/` directory existed. `tests/verify.sh` was present and the
    README asserted "32/32", but no recorded output backed that claim, so the result was
    unverifiable from the repo alone.
  - *Version agreement* — `README.md` named no version at all, and with no `Tooling/`
    directory and no `CHANGE_LOG.md` entry there was nothing for it to agree with.
  - *Reciprocity* was the only check not failed, vacuously: with no `KNOWN_ISSUES.md`,
    `CHANGE_LOG.md`, `IMPLEMENTATIONS.md` or `TEMPLATES.md` there were no entries to be
    non-reciprocal.
- **cause:** The tool predates the PROCESS.md conventions. It was transferred from
  `operand-packages` (PROCESS.md §1: this repo is v2.0 of it) in its original shape —
  README plus loose `templates/` and `tests/` directories — and nothing in the repo
  enforces the §3/§4 layout at transfer time, so the conventions were never applied to it.
  This is the §9 migration backlog, not a defect in the templates themselves.
- **iteration:** Migrate Skills/Errors to the PROCESS.md layout at v1.0.0 and create the
  missing canonical documents — i.e. bring the tool into conformance under §9 without
  changing its behaviour: move `templates/` and `tests/` into `Tooling/v1.0.0/` (a tool
  that has never been versioned starts at `v1.0.0` per §9/§10.6), run the existing
  self-check from its new location, record the actual output under `Tests/v1.0.0/`, create
  the four missing canonical documents, and correct `README.md` to name `v1.0.0`. Recorded
  in
  [`CHANGE_LOG.md#migrate-skills-errors-to-the-process-md_58690b69`](CHANGE_LOG.md#migrate-skills-errors-to-the-process-md_58690b69).
- **resolved_by:** [`CHANGE_LOG.md#migrate-skills-errors-to-the-process-md_58690b69`](CHANGE_LOG.md#migrate-skills-errors-to-the-process-md_58690b69) at version `v1.0.0`
- **status:** in-progress
- **status_note:** The iteration is written and executed in the working tree, but nothing
  has merged: `merge_commit` in the cited change entry is empty, and
  `process.yaml: definitions.issue-status` states that `resolved` is never written while
  `merge_commit` is empty — an approved-but-unmerged fix is still `in-progress`. The work
  is on branch `smoke/fix-skills-errors`; no PR has been opened and the merge to `main`
  (PROCESS.md §5.4/§8) is handled outside this run. This field replaces an earlier
  free-text status ("resolved in the working tree — pending the PR merge to `main`"), which
  was outside the closed set of seven.
- **occurrences:**
  | # | When | Where | Note |
  |---|---|---|---|
  | 1 | 2026-08-31 | `Skills/Errors` | Found by the §9 migration pass; the state it found is the outcome recorded above. |

---

## skills-errors-migration-entries-violate_329e05c5

- **id:** `skills-errors-migration-entries-violate_329e05c5`
- **summary:** Skills/Errors migration entries violate the amended PROCESS.md: a status outside the closed set, a false branch claim, and backticked entry headings
- **occurred_at:** 2026-09-01
- **source:** Post-migration audit by an agent that did not perform the 2026-08-31
  migration, read against the amended PROCESS.md / `process.yaml` (PR #16, §10 decisions
  11–14). Re-confirmed by inspection of the tool's own documents on this branch.
- **outcome:** Four defects, all in the migration's own records rather than in the
  templates:
  - *Status vocabulary* — the issue entry's `status` read `resolved in the working tree —
    pending the PR merge to main`. That is not one of the seven values in
    `process.yaml: definitions.issue-status`, so it is a Track B conformance failure
    (§10.11). It also asserted `resolved` while `merge_commit` was empty, which the same
    definition forbids outright.
  - *False branch claim* — `CHANGE_LOG.md`'s `merge_commit` field read "This change sits on
    a branch". At the time it was written no branch existed for this work, so the document
    asserted a fact about the repository that was not true. `process.yaml: create_branch`
    makes the branch a real artifact of the procedure, not a form of words.
  - *Entry heading form* — every entry heading in `KNOWN_ISSUES.md`, `CHANGE_LOG.md`,
    `IMPLEMENTATIONS.md` and `TEMPLATES.md` wrapped the id in backticks (and, in the latter
    two, appended a title). `process.yaml: definitions.entry` requires the heading text to
    be the bare id, because that text is the anchor a `FILE.md#<id>` citation resolves
    against; backticks or extra words break the anchor and make reciprocity unverifiable by
    grep (§10.13).
  - *Unverified ids* — the two ids minted by the migration had not been reproduced against
    the amended canonicalisation (§10.14, trailing-punctuation strip) or the new change-id
    identity rule (§10.8, the `iteration` field alone). Their correctness was assumed, not
    demonstrated.
- **cause:** The migration ran on 2026-08-31 against the PROCESS.md of that date. Decisions
  8 and 11–14 were settled on 2026-09-01, *after* the migration and partly because of what
  it exposed — the status vocabulary was open, `change-id` had a format but no identity
  rule, "entry" was undefined for a prose document, and canonicalisation did not strip
  trailing punctuation. The branch claim has a separate cause: it was copied from the §6
  step 3 description of the procedure and written as though the step had been performed,
  rather than reporting the repository's actual state.
- **iteration:** Correct the Skills/Errors migration entries to the amended PROCESS.md:
  closed-set status, a true branch statement, bare-id entry headings, and ids recomputed
  and reverified. Recorded in
  [`CHANGE_LOG.md#correct-the-skills-errors-migration-entr_fc96ca88`](CHANGE_LOG.md#correct-the-skills-errors-migration-entr_fc96ca88).
- **resolved_by:** [`CHANGE_LOG.md#correct-the-skills-errors-migration-entr_fc96ca88`](CHANGE_LOG.md#correct-the-skills-errors-migration-entr_fc96ca88) at version `v1.0.0`
- **status:** in-progress
- **status_note:** No `merge_commit` exists for this work either — it is on branch
  `smoke/fix-skills-errors` and has not been PR'd or merged. `v1.0.0` has never been
  released, so correcting these entries edits an *unreleased* version rather than a frozen
  one, and no version is bumped: no file under `Tooling/v1.0.0/` was changed.
- **occurrences:**
  | # | When | Where | Note |
  |---|---|---|---|
  | 1 | 2026-09-01 | `Skills/Errors` | Found by the post-migration audit; the four defects above are the state it found. |
