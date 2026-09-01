# Known issues — Workflows/Review

Every issue found with this tool. Append-only (PROCESS.md §5.1). Ids are computed
per `process.yaml` `definitions.issue-id` — the `summary` field alone, canonicalised
(trim, lowercase, collapse whitespace runs to one space, strip trailing `. , ; : ! ?`)
then `sha256`, first 8 hex characters. Each entry cites the
[`CHANGE_LOG.md`](CHANGE_LOG.md) entry that carries its iteration.

Entry headings are the bare id (`process.yaml` `definitions.entry`), which is what
`KNOWN_ISSUES.md#<id>` citations resolve against.

| id | Summary | Status |
|---|---|---|
| [`workflows-review-fails-track-b-conforman_0b0b4b59`](#workflows-review-fails-track-b-conforman_0b0b4b59) | Track B conformance failure found at the 2026-08-31 migration | in-progress |
| [`workflows-review-v1-0-0-migration-output_d18c44d1`](#workflows-review-v1-0-0-migration-output_d18c44d1) | The migration output itself fails Track B (round 1 did not resolve the entry above) | in-progress |

Neither entry is `legacy`: both were written after PROCESS.md existed and both
have a `CHANGE_LOG.md` counterpart, so the §7 reciprocity check binds them.

---

## workflows-review-fails-track-b-conforman_0b0b4b59

| Field | Value |
|---|---|
| **id** | `workflows-review-fails-track-b-conforman_0b0b4b59` |
| **summary** | Workflows/Review fails Track B conformance: four canonical documents missing, no Tooling/ or Tests/ directories, README names no version, and the tool has no implementation at all |
| **outcome** | All five Track B checks of PROCESS.md §7 failed. The tool announced a workflow and supplied nothing a reader could use, run or copy, and carried no issue log or change log that would make that visible |
| **cause** | The directory was created as a placeholder and never taken through the PROCESS.md §9 conformance step; separately and more fundamentally, the review workflow itself has never been written |
| **iteration** | Create the PROCESS.md section 3 document set and the section 4 version directories for Workflows/Review at v1.0.0, without inventing a workflow, a template or a test result |
| **status** | in-progress |
| **resolved_by** | [`CHANGE_LOG.md#create-the-process-md-section-3-document_cddfd0f4`](CHANGE_LOG.md#create-the-process-md-section-3-document_cddfd0f4), fix-version **v1.0.0**. Not merged — see *Status, precisely* below |
| **source** | PROCESS.md §7 Track B run against `Workflows/Review` during the 2026-08-31 migration |
| **occurred_at** | 2026-08-31 |
| **tool** | `Workflows/Review` |
| **occurrences** | 1 — 2026-08-31, the migration run |

**Status, precisely.** `in-progress`, not `resolved`. `process.yaml`
`definitions.issue-status` puts it plainly: `resolved` is never written while
`merge_commit` is empty, and an approved-but-unmerged fix is still `in-progress`.
No PR carrying this work has merged; `main` still holds the single 42-byte
`README.md`. The migration recorded this entry as `partially resolved`, a string
outside the closed set of seven — that is one of the defects logged as
[`workflows-review-v1-0-0-migration-output_d18c44d1`](#workflows-review-v1-0-0-migration-output_d18c44d1).

**outcome (X), in detail.** Every Track B check failed:

| Check | Result before the migration |
|---|---|
| Canonical files | **FAIL** — only `README.md` existed. `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and `CHANGE_LOG.md` were all absent |
| Reciprocity | **FAIL (vacuous)** — none of the four files existed, so no pair could cite anything |
| Code layout | **FAIL** — no `Tooling/` directory, and no document under one |
| Test layout | **FAIL** — no `Tests/` directory and no recorded result of any kind |
| Version agreement | **FAIL** — `README.md` named no version, and there was no `Tooling/` directory and no `CHANGE_LOG.md` entry to agree with |

Verbatim, the entire tool was:

```
$ find . -mindepth 1
./README.md

$ cat README.md
This folder contains the review workflow.
```

**cause (Y), in detail.** Two distinct causes, and they are not the same failure:

1. *The document gap.* The directory was created — or transferred from
   `operand-packages` — as a placeholder and never taken through PROCESS.md §9's
   conformance step. The §3/§4 conventions postdate it, and nothing forced the
   gap shut: §9's backlog table records exactly this state for `Workflows/Review`
   (`README ✅`, all six other columns `❌`).
2. *The implementation gap.* No one has written the workflow. This is not drift
   away from a working tool and not a defect in one — there has never been a
   procedure here to break. The single-sentence README is a stub never filled in.

Cause 1 is a missing migration. Cause 2 is missing work, and no migration closes it.

**iteration (Z), in detail.** Bring the tool to the §3/§4 layout at **v1.0.0**
(§9: a tool that has never been versioned starts at `v1.0.0`): create the four
missing canonical documents stating honestly that no implementation, use case or
template exists; place the document that constitutes the tool under
`Tooling/v1.0.0/` per §4's code-less rule; record the Track-B result under
`Tests/v1.0.0/`; and state `v1.0.0` in `README.md`. Explicitly **not** in scope:
writing the review workflow.

**What this iteration does not close.** The workflow itself is still unwritten.
Under the amended §4 that is no longer a Track-B failure — a code-less tool's
documents *are* its `Tooling/` contents, and §5.5 accepts a recorded Track-B
result as evidence — so the tool is no longer unmergeable. But the substantive
gap stands: `Tooling/v1.0.0/REVIEW.md` records one sentence because one sentence
is all that exists. Closing that is a build, a new issue and a new iteration
under §6, not this one.

---

## workflows-review-v1-0-0-migration-output_d18c44d1

| Field | Value |
|---|---|
| **id** | `workflows-review-v1-0-0-migration-output_d18c44d1` |
| **summary** | Workflows/Review v1.0.0 migration output fails Track B: an invented marker file stands in for the tool's documents under Tooling/, entry headings are backticked, the issue status is outside the closed set, the change-id derives from a non-identity field, and the change entry's branch claim is false |
| **outcome** | The round-1 output of the fix loop did not bring the tool into conformance: the Code-layout check still had no tool document under Tooling/, both entries were unciteable by grep because their headings were backticked, the status string was not one of the seven, and the change-id did not reproduce from its identity field |
| **cause** | The 2026-08-31 spec had no rule for a tool with no executable code and no identity for a change-id, so the migrating agent invented a marker file and hashed the change entry on a `summary` field the change-entry schema does not define; the heading form and the closed status set were settled only afterwards, on 2026-09-01 (PROCESS.md §10 decisions 8, 9, 11, 13, 14) |
| **iteration** | Repair the Workflows/Review v1.0.0 migration output in place: delete the invented marker file, place the tool's constituting document under Tooling/v1.0.0/, restate both entry headings as bare ids, put every status inside the closed set, recompute both ids from their identity fields, and record the Track-B checks in Tests/v1.0.0/RESULTS.md as the tool's evidence |
| **status** | in-progress |
| **resolved_by** | [`CHANGE_LOG.md#repair-the-workflows-review-v1-0-0-migra_23ca8994`](CHANGE_LOG.md#repair-the-workflows-review-v1-0-0-migra_23ca8994), fix-version **v1.0.0**. Not merged — no `merge_commit`, so not `resolved` |
| **source** | PROCESS.md §7 Track B re-run against the migration output on branch `smoke/fix-workflows-review` |
| **occurred_at** | 2026-09-01 |
| **tool** | `Workflows/Review` |
| **occurrences** | 1 — 2026-09-01, the conformance re-run |

**Why this is a second entry and not an edit.** `process.yaml`
`loops.fix_loop.on_reentry` and PROCESS.md §7 Track A step 6 are explicit: when a
round's outcome does not resolve the logged error, the failure is *appended* to
`KNOWN_ISSUES.md` before replanning. This is round **2** of the bound of 3
(`loops.fix_loop.max_rounds`); the bound is not exhausted, so nothing escalates.

**outcome (X), in detail.** Five defects, each a Track-B or vocabulary failure:

1. **Invented marker file.** `Tooling/v1.0.0/NOTE.md` existed only to say the
   directory held no code. PROCESS.md §4 now forbids exactly that — "No marker
   file is invented" — and requires the documents that constitute the tool to
   live under `Tooling/v<version>/`. The Code-layout check therefore still failed
   in substance: nothing of the tool was under `Tooling/`.
2. **Heading form.** Both entry headings wrapped the id in backticks, breaking
   `definitions.entry` — `heading_form: "## <id>"`, the bare id, nothing else on
   the line. The migration papered over it with an `<a name="...">` tag, which
   supplies a second anchor rather than the one the `FILE.md#<id>` citations
   resolve against, and leaves reciprocity unverifiable by grep. The same rule
   bit a second way, found only when the check was mechanised: `definitions.entry`
   makes **any** level-2 heading an entry, so the prose headings
   `## No implementations are recorded` and `## No templates exist` were read as
   entries with non-id names, and `IMPLEMENTATIONS.md` / `TEMPLATES.md` failed
   reciprocity 1-versus-1 instead of passing vacuously 0-versus-0.
3. **Status outside the closed set.** `partially resolved` is not one of `open,
   planned, in-progress, resolved, escalated, legacy, wont-fix`.
4. **change-id from a non-identity field.** `migrate-workflows-review-to-the-track-b_abb4adaf`
   reproduces from a `summary` field that `definitions.change-entry` does not
   define. Identity is the `iteration` field alone.
5. **False branch claim.** The change entry stated "No branch was created,
   nothing was committed". The work is on branch `smoke/fix-workflows-review`
   and is committed there.

**cause (Y), in detail.** The migration ran against the 2026-08-31 spec, which
was silent on all five points. The 2026-09-01 decisions closed the silences:
8 (change-id identity), 9 (code-less tools conform; no marker file), 11 (closed
status set), 13 (entry heading form), 14 (canonicalisation strips trailing
punctuation). The defects are gaps the spec left open, not carelessness — but
they are still failures, and §7 requires them logged like any other issue.

**iteration (Z), in detail.** Repair in place, at v1.0.0. In place is legitimate
because v1.0.0 has never been released: `main` still holds the pre-migration
`README.md`, so §4's immutability rule has not yet attached to this directory and
no version bump is owed. What changed is recorded in
[`CHANGE_LOG.md#repair-the-workflows-review-v1-0-0-migra_23ca8994`](CHANGE_LOG.md#repair-the-workflows-review-v1-0-0-migra_23ca8994).
