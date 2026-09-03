# Change log — Workflows/Audit

Every iteration made in response to an entry in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Reciprocal: each entry here names the issue
it resolves, and that issue names this entry back (PROCESS.md §3). Ids follow
`process.yaml` → `definitions.change-id`: `<description>_<hash8>`, hashed over
the `iteration` field alone (PROCESS.md §10.8).

Newest last. Entries are appended, never rewritten.

**Note on history.** This file was created on 2026-08-31 as part of the first
entry below. The tool has no earlier iteration history: before that change it
consisted of a single `README.md`, so there was no code that could have been
iterated on and no record of any change to reconstruct.

**Both entries sit unmerged on branch `smoke/fix-workflows-audit`**, off `main`
at `44fd052`. Neither has a `merge_commit`, which is why both cited issues read
`in-progress` rather than `resolved`.

---

## a-documents-only-conformance-migration-a_27d16c95

| Field | Value |
|---|---|
| **id** | `a-documents-only-conformance-migration-a_27d16c95` |
| **resolves** | [`KNOWN_ISSUES.md#workflows-audit-failed-track-b-conforman_fb119cc2`](KNOWN_ISSUES.md#workflows-audit-failed-track-b-conforman_fb119cc2) |
| **cause** | The tool predates PROCESS.md and was never migrated to the `Tooling/`/`Tests/` convention (the §9 backlog), and separately no implementation was ever written for it |
| **outcome** | Track B failed on canonical files, code layout, test layout and version agreement; the repository gave a reader no way to tell that this workflow does not exist |
| **iteration** | A documents-only conformance migration at v1.0.0: create the four missing canonical documents as empty-but-valid records, establish the Tooling/v1.0.0 and Tests/v1.0.0 version anchors, state v1.0.0 in the README, and author no workflow logic, script, prompt, template or test |
| **expected_result** | All five canonical documents present and non-empty; the tool's constituting document under `Tooling/v1.0.0/`; a recorded result under `Tests/v1.0.0/`; `v1.0.0` named consistently in README, `Tooling/` and this entry; nothing fabricated |
| **change** | The four missing root documents created; the workflow's authored substance placed under `Tooling/v1.0.0/`; `Tests/v1.0.0/` populated with the verbatim capture of the tool's test state; README given a version line and a truthful contents section |
| **version** | `v1.0.0` — the tool's first version per PROCESS.md §9 / §10.6. **No bump**: nothing was moved and no code changed, because the tool has no code |
| **merge_commit** | *(empty)* — not merged. The iteration sits on branch `smoke/fix-workflows-audit`, awaiting the PR and the human gate (PROCESS.md §6 steps 5–6). Recorded here on merge (§6 step 7) |

**Id derivation.** `hash8` = first 8 hex chars of `sha256` over the canonical
form of the **`iteration` field alone** — trimmed, lowercased, whitespace
collapsed, trailing punctuation stripped — = `27d16c95`. `description` = that
same `iteration` field slugified per `process.yaml → slug_rule` and truncated to
40 characters. Verbatim recomputation in
[`Tests/v1.0.0/id-recompute-2026-09-01.log`](Tests/v1.0.0/id-recompute-2026-09-01.log).

**This id moved.** The migration published this entry as
`brought-workflows-audit-into-track-b-con_be1c5a4b`, hashed over a `summary`
field. `summary` is not a field of `change-entry` at all, and PROCESS.md §10.8
settles change identity as the `iteration` field alone. `be1c5a4b` is retired and
appears nowhere as a live citation; it is recorded here only so the old id is
traceable to the new one.

### Cause (Y)

Two causes, recorded in full in the issue entry: the tool predates PROCESS.md and
was never migrated to the `Tooling/`/`Tests/` convention (the §9 backlog), **and**
separately, no implementation was ever written for it — the directory has only
ever held a one-line README describing the folder rather than the tool.

### Outcome (X)

Track B failed on canonical files (four of five missing), code layout, test
layout and version agreement. Under PROCESS.md §7 the tool cannot release a
version until that is logged and fixed, and — the more damaging effect — the
repository gave a reader no way to tell that this workflow does not exist.

### Iteration (Z)

A documents-only conformance migration at `v1.0.0`. Explicitly **not** a build:
no workflow logic, script, prompt, template or test was authored, because
nothing in the repository says what this workflow does and inventing it would
violate the purpose of a repo whose contents are copied as proven method
(PROCESS.md §1).

### Expected result (V) — checkably

1. All five canonical `.md` files exist and are non-empty at the tool root.
2. `TEMPLATES.md` and `IMPLEMENTATIONS.md` are empty-but-valid per §9, each
   stating the absence explicitly rather than describing anything invented.
3. `KNOWN_ISSUES.md` and `CHANGE_LOG.md` each cite the other's id (§3
   reciprocity); `IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` reciprocity holds
   vacuously, with zero uncited entries on either side.
4. `Tests/v1.0.0/` records the tool's actual test state, and states plainly that
   no executable suite exists — never a pass (§5.6).
5. `README.md` names `v1.0.0`, agreeing with the `Tooling/` directory and with
   this entry, and describes what the tool actually contains.
6. No file is fabricated: every statement across the five documents is traceable
   to something observed in the repository on 2026-08-31.

### Change (W) — what changed, where, how it is verified

| What | Where | Verified by |
|---|---|---|
| The tool's constituting document | `Tooling/v1.0.0/WORKFLOW.md` | Holds the workflow's entire authored substance — the one sentence *"This folder contains the audit workflow."* — quoted verbatim, where PROCESS.md §4 requires a code-less tool's documents to live |
| Code moved into `Tooling/v1.0.0/` | **no program to move** | `find . -type f` before the change returned exactly `./README.md`. There was no `bin/`, `lib/`, `commands/`, `examples/`, `templates/`, `n8n/`, `tests/` or `run-tests.sh` to relocate. Capture in [`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log) |
| Path repairs after the move | **none needed** | No executable file was moved, so no `cd`, `sys.path`, import or relative entrypoint path could break |
| `Tests/v1.0.0/run-tests.log` created | `Tests/v1.0.0/` | Verbatim capture, 2026-08-31T15:25:02Z: `./run-tests.sh` → `No such file or directory`, `exit_code=127`; `ls tests/` → `No such file or directory`, `exit_code=2`; `python3 -m unittest discover -v` → `Ran 0 tests in 0.000s / OK` |
| `Tests/v1.0.0/RESULTS.md` created | `Tests/v1.0.0/` | Records that no executable suite exists, with the `Ran 0 tests / OK` line explicitly flagged as an empty discovery rather than a passing suite |
| `IMPLEMENTATIONS.md` created | tool root | Empty-but-valid: states that no implementation exists, cites the `find` evidence, and lists the fields a first entry must carry |
| `TEMPLATES.md` created | tool root | Empty-but-valid: states that no `templates/` directory and no template file of any kind exists |
| `KNOWN_ISSUES.md` created | tool root | Header plus the entry `workflows-audit-failed-track-b-conforman_fb119cc2`, which cites this change |
| `CHANGE_LOG.md` created | tool root | This file |
| `README.md` edited | tool root | Minimal edit: the original sentence is preserved verbatim; a version line (`v1.0.0`), a truthful contents section, a status line and a file table were added |

### Honest limits of this iteration

- **It does not make the tool work.** `Workflows/Audit` is still a reserved name
  with no authored process; this change makes that fact visible instead of
  ambiguous, which is what PROCESS.md §1 asks of the documents.
- **The issue stays open on its second cause.** That the workflow was never
  written cannot be closed by a conformance migration, and needs owner input the
  repository does not contain.

---

## correct-the-migration-records-in-place-a_531c29b0

| Field | Value |
|---|---|
| **id** | `correct-the-migration-records-in-place-a_531c29b0` |
| **resolves** | [`KNOWN_ISSUES.md#the-2026-08-31-conformance-migration-of_0b111e47`](KNOWN_ISSUES.md#the-2026-08-31-conformance-migration-of_0b111e47) |
| **cause** | The migration ran against the pre-amendment PROCESS.md, which had no rule for a code-less tool, no identity for `change-id`, no closed status set and no evidence path a code-less tool could satisfy; each gap was filled by invention rather than escalation |
| **outcome** | An invented marker file standing in for the tool's documents, an unreproducible change-id, a status no checker could read, and a branch claim that was false when written |
| **iteration** | Correct the migration records in place at v1.0.0, which was never released: remove the invented Tooling marker file and place the tool constituting document under Tooling/v1.0.0, recompute the change-id from its iteration field, replace the prose status with a closed-set value, name the real branch, and record the Track-B checks in Tests/v1.0.0/RESULTS.md as the evidence invariant 5 now requires |
| **expected_result** | No marker file anywhere under `Tooling/`; every id in both root documents reproduces under `sha256sum` from its identity field; every `status` is one of the seven; every branch reference names `smoke/fix-workflows-audit`; all five Track-B checks run and recorded verbatim under `Tests/v1.0.0/` |
| **change** | `Tooling/v1.0.0/README.md` deleted and `WORKFLOW.md` written in its place; both entry ids recomputed and every citation repaired; statuses set to `in-progress`; branch named explicitly; `RESULTS.md` rewritten around the Track-B result; prose headings in the four entry documents demoted to level 3 so every level-2 heading is a bare id |
| **version** | `v1.0.0` — **no bump.** `v1.0.0` has never merged, so it is not a released version directory and §4 immutability does not bind it. Bumping would leave a broken, never-released `v1.0.0` in the tree as a permanent rollback point to a state that never worked |
| **merge_commit** | *(empty)* — not merged. Sits on branch `smoke/fix-workflows-audit` awaiting the PR and the human gate |

**Id derivation.** `hash8` = `sha256` over the canonical `iteration` field alone
= `531c29b0`; `description` = that field slugified and truncated to 40
characters. Verbatim in
[`Tests/v1.0.0/id-recompute-2026-09-01.log`](Tests/v1.0.0/id-recompute-2026-09-01.log).

### Cause (Y)

Recorded in full in the issue entry. In short: four gaps in the specification the
migration ran against — no handling for a tool with no executable code, no
identity rule for `change-id`, no closed status vocabulary, and an invariant 5
that a code-less tool could not satisfy — each closed by invention instead of the
escalation PROCESS.md §5 requires. All four gaps are now settled in PROCESS.md
§10 as decisions 8, 9, 10 and 11.

### Outcome (X)

The tool's own records were non-conformant, which is the worst place for a
conformance migration to leave a defect: the documents that exist to make
staleness visible were themselves misleading. Specifically, a reader was told the
work sat on a branch that did not exist, and a checker could not reproduce a
change-id or parse a status.

### Iteration (Z)

Correct in place at `v1.0.0`, per the field table above. Nothing about the
workflow itself is invented — no process steps, no program, no test run.

### Expected result (V) — checkably

1. `find Tooling -type f` lists exactly one file, `WORKFLOW.md`, and it holds the
   tool's authored substance rather than a statement about the directory.
2. Every id in `KNOWN_ISSUES.md` and `CHANGE_LOG.md` reproduces byte-for-byte
   from its identity field under `sha256sum`, and every citation of every id
   resolves to a heading of the form `## <id>`.
3. Every `status` value is one of the seven in
   `process.yaml → definitions.issue-status`, and no `resolved` is written
   against an empty `merge_commit`.
4. No document claims the work sits anywhere other than
   `smoke/fix-workflows-audit`.
5. `Tests/v1.0.0/RESULTS.md` records that no executable suite exists and carries
   all five Track-B check results, run for real, with the commands and output
   preserved verbatim.

### Change (W) — what changed, where, how it is verified

| What | Where | Verified by |
|---|---|---|
| Invented marker deleted | `Tooling/v1.0.0/README.md` | Removed with `git rm`. It declared itself "a marker, not an implementation" and instructed the reader to delete it later — PROCESS.md §4 now states outright that no marker file is invented |
| Constituting document written | `Tooling/v1.0.0/WORKFLOW.md` | Carries the workflow's complete authored substance, quoted verbatim, plus an exact statement of how much of the process that sentence specifies (the name only). Nothing is added to it |
| `change-id` recomputed | `CHANGE_LOG.md` | `be1c5a4b` (hashed over a non-existent `summary` field) → `27d16c95` (hashed over `iteration`). Both citations in `KNOWN_ISSUES.md` repaired |
| `issue-id` recomputed | `KNOWN_ISSUES.md` | `fb119cc2` re-derived with `sha256sum` and **unchanged** — the summary carried no trailing punctuation, so PROCESS.md §10.14 did not move it |
| Statuses corrected | `KNOWN_ISSUES.md` | Prose status → `in-progress` on both entries, matching the index table. `resolved` is not written against an empty `merge_commit` |
| Branch claims corrected | `KNOWN_ISSUES.md`, `CHANGE_LOG.md` | Every reference now names `smoke/fix-workflows-audit`, off `main` at `44fd052`, and the file header states it once for both entries |
| Evidence recorded | `Tests/v1.0.0/RESULTS.md`, `track-b-2026-09-01.log`, `id-recompute-2026-09-01.log` | The Track-B checks run for real on 2026-09-01 with commands and output captured verbatim; this is the recorded evidence PROCESS.md §5.5 and §8 now accept from a code-less tool |
| Entry headings normalised | all four entry documents | Redundant `<a name>` anchors removed and prose headings demoted to level 3, so every level-2 heading is a bare id per `process.yaml → definitions.entry` and reciprocity is grep-verifiable |

### Honest limits of this iteration

- **It fixes records, not the tool.** Nothing here brings `Workflows/Audit`
  closer to being a workflow.
- **The code-layout check passes on a technicality of §4, and the entry says so.**
  What constitutes the tool now sits under `Tooling/v1.0.0/`; what constitutes
  the tool is one sentence. The check is satisfied as written; the tool is not
  useful. Both statements are true and neither is softened here.
- **Nothing is merged.** Both issues stay `in-progress`.

---

## retire-workflows-audit-at-v1-1-0-keep-th_add8a5e2

| Field | Value |
|---|---|
| **id** | `retire-workflows-audit-at-v1-1-0-keep-th_add8a5e2` |
| **resolves** | [`KNOWN_ISSUES.md#workflows-audit-is-a-reserved-name-carry_1ec09cf6`](KNOWN_ISSUES.md#workflows-audit-is-a-reserved-name-carry_1ec09cf6) |
| **cause** | The directory was created as a reserved name and no implementation was ever written; "audit" meanwhile named three unrelated capabilities across the system this repo serves, so the empty name could plausibly mean any of them |
| **outcome** | A reader finding `Workflows/Audit` could not tell which audit they had found, or whether it was working, broken, superseded or never built |
| **iteration** | Retire Workflows/Audit at v1.1.0: keep the directory as a signpost whose Tooling document records that the name is retired and where the capability went, and author no workflow logic for it |
| **expected_result** | The repository answers "where does auditing live" unambiguously, and the history of a name reserved and never built stays readable rather than being deleted |
| **change** | `Tooling/v1.1.0/WORKFLOW.md` — the retirement, the replacement, and why the name is retired rather than filled in; `Tests/v1.1.0/RESULTS.md` + `track-b.log`; `README.md` restated at v1.1.0. `Tooling/v1.0.0/` untouched |
| **version** | `v1.1.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because the directory was a reserved name that three
different capabilities could answer to (cause Y), the repository could not tell a
reader which audit lived here or whether it existed at all (outcome X). Iteration
Z retires the name and points at
[`Packages/Sentinel`](../../Packages/Sentinel), which is where the host-integrity
capability was actually built.

**Why not fill the name in.** Sentinel ships a program, and `Workflows/` is for
processes rather than programs (PROCESS.md §2). Putting it here would have meant
either mis-filing it or loosening the taxonomy to accommodate a single tool. And
naming one of the three audits "Audit" silently excludes the other two behind a
directory that looks general.

**Why not delete the directory.** PROCESS.md §4 makes a released version
directory immutable, and the record of a name that was reserved and never built
is the useful history here — deleting it would erase the finding that produced
this retirement.

**Evidence.** [`Tests/v1.1.0/track-b.log`](Tests/v1.1.0/track-b.log). No
executable suite exists; §5.5 and §8 make a recorded Track-B result the evidence
a code-less tool merges on.
