# Change log — Workflows/Review

Every iteration made in response to an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)
(PROCESS.md §3). Ids are computed per `process.yaml` `definitions.change-id` — the
`iteration` field alone (PROCESS.md §10 decision 8), canonicalised (trim,
lowercase, collapse whitespace runs to one space, strip trailing `. , ; : ! ?`)
then `sha256`, first 8 hex characters.

Entry headings are the bare id (`process.yaml` `definitions.entry`).

| id | Resolves | Version | Merged |
|---|---|---|---|
| [`create-the-process-md-section-3-document_cddfd0f4`](#create-the-process-md-section-3-document_cddfd0f4) | [`workflows-review-fails-track-b-conforman_0b0b4b59`](KNOWN_ISSUES.md#workflows-review-fails-track-b-conforman_0b0b4b59) | v1.0.0 | no |
| [`repair-the-workflows-review-v1-0-0-migra_23ca8994`](#repair-the-workflows-review-v1-0-0-migra_23ca8994) | [`workflows-review-v1-0-0-migration-output_d18c44d1`](KNOWN_ISSUES.md#workflows-review-v1-0-0-migration-output_d18c44d1) | v1.0.0 | no |

Both iterations sit on branch `smoke/fix-workflows-review`. Neither has merged,
so `merge_commit` is empty for both and neither issue may be marked `resolved`.

---

## create-the-process-md-section-3-document_cddfd0f4

| Field | Value |
|---|---|
| **id** | `create-the-process-md-section-3-document_cddfd0f4` |
| **resolves** | [`KNOWN_ISSUES.md#workflows-review-fails-track-b-conforman_0b0b4b59`](KNOWN_ISSUES.md#workflows-review-fails-track-b-conforman_0b0b4b59) |
| **cause** | The directory was created as a placeholder and never taken through the PROCESS.md §9 conformance step; separately, the review workflow itself has never been written |
| **outcome** | All five Track B checks failed. The tool was one 42-byte `README.md` reading "This folder contains the review workflow." and nothing else |
| **iteration** | Create the PROCESS.md section 3 document set and the section 4 version directories for Workflows/Review at v1.0.0, without inventing a workflow, a template or a test result |
| **expected_result** | The five canonical files exist and are non-empty; this entry and its issue entry cite each other; the tool's document sits under `Tooling/v1.0.0/`; a recorded Track-B result sits under `Tests/v1.0.0/`; README, newest `Tooling/` and newest `CHANGE_LOG.md` entry all name v1.0.0 |
| **change** | The four missing canonical documents created, `README.md` extended to name v1.0.0, `Tooling/v1.0.0/` and `Tests/v1.0.0/` opened |
| **version** | **v1.0.0** — no bump. Per PROCESS.md §9 an unversioned tool starts at v1.0.0; this iteration establishes that version rather than succeeding one |
| **merge_commit** | *(empty)* — not merged |
| **branch** | `smoke/fix-workflows-review` |
| **date** | 2026-08-31, amended 2026-09-01 by [`repair-the-workflows-review-v1-0-0-migra_23ca8994`](#repair-the-workflows-review-v1-0-0-migra_23ca8994) |

**Note on this entry's id.** It changed. The migration computed
`migrate-workflows-review-to-the-track-b_abb4adaf` over a `summary` field, which
`definitions.change-entry` does not define; that hash does reproduce from the
string the migration used, but the field is not the identity. PROCESS.md §10
decision 8 settled change-id identity as the `iteration` field alone, so this
entry is now `create-the-process-md-section-3-document_cddfd0f4`, recomputed with
`sha256sum` over the canonicalised `iteration` value above. Every citation of the
old id was rewritten with it.

**cause (Y), in detail.** `Workflows/Review` was left as a placeholder directory
and never taken through PROCESS.md §9's conformance step — and, separately and
more fundamentally, the review workflow itself has never been written. See the
two causes distinguished in the issue entry.

**outcome (X), in detail.** All five Track B checks failed. Four canonical
documents absent, no `Tooling/`, no `Tests/`, no version named anywhere — a
directory that claims a workflow and supplies none, with no issue log or change
log to make that visible.

**iteration (Z), in detail.** Create the §3 document set and the §4 version
directories at v1.0.0, with every new document stating plainly that no
implementation, use case, template or test exists. Do **not** invent a workflow,
a template, or a test result to make a check pass.

**expected_result (V), checkably.** After this iteration:

1. All five canonical files exist at the tool root and are non-empty.
2. `KNOWN_ISSUES.md` and `CHANGE_LOG.md` entries cite each other by id;
   `IMPLEMENTATIONS.md` and `TEMPLATES.md` carry zero entries, so their
   reciprocity check has nothing to fail on and both say so explicitly.
3. `Tooling/v1.0.0/` holds the document that constitutes the tool and
   `Tests/v1.0.0/` holds a recorded Track-B result.
4. `README.md`, the newest `Tooling/` directory and the newest `CHANGE_LOG.md`
   entry all name **v1.0.0**.
5. No statement in any new document asserts anything about the review workflow's
   purpose, steps or usage — the repo contains no such information.

Deliberately **not** expected: a passing executable test suite, or a workflow. The
first cannot exist without the second, and the second is a build.

**change (W).** What changed, where, and how it was verified:

1. **Layout.** Nothing moved as code. `find . -mindepth 1` returned `./README.md`
   alone before the migration — no `bin/`, `lib/`, `commands/`, `examples/`,
   `templates/`, `n8n/`, `tests/` or `run-tests.sh` to relocate. Under §4's
   code-less rule the tool's document is what lives under `Tooling/v1.0.0/`; it
   is [`Tooling/v1.0.0/REVIEW.md`](Tooling/v1.0.0/REVIEW.md), carrying the tool's
   one documented sentence verbatim.
2. **Paths.** No path repair was needed or possible: this tool has no script, no
   `sys.path` manipulation, no import and no `bin/` entrypoint.
3. **Recorded results.** No executable suite exists, so none was run.
   [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) records that fact and the
   Track-B checks run in its place, with the verbatim transcript in
   [`Tests/v1.0.0/track-b-checks.log`](Tests/v1.0.0/track-b-checks.log). Per
   PROCESS.md §5.6, an unrun test is recorded as unrun, never as a pass.
4. **Documents.** `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and
   `CHANGE_LOG.md` created; `README.md` extended to name v1.0.0 and describe the
   tool's actual state. The pre-existing sentence "This folder contains the
   review workflow." is preserved verbatim.

**Verification.** The Track-B checks in `Tests/v1.0.0/track-b-checks.log`, run
against the working tree of `smoke/fix-workflows-review`.

---

## repair-the-workflows-review-v1-0-0-migra_23ca8994

| Field | Value |
|---|---|
| **id** | `repair-the-workflows-review-v1-0-0-migra_23ca8994` |
| **resolves** | [`KNOWN_ISSUES.md#workflows-review-v1-0-0-migration-output_d18c44d1`](KNOWN_ISSUES.md#workflows-review-v1-0-0-migration-output_d18c44d1) |
| **cause** | The 2026-08-31 spec had no rule for a code-less tool and no identity for a change-id, so the migrating agent invented a marker file and hashed the change entry on an undefined field; the heading form and the closed status set were settled only on 2026-09-01 |
| **outcome** | The round-1 migration output still failed Track B: no tool document under `Tooling/`, both entry headings backticked, a status outside the closed set, a change-id that does not reproduce from its identity field, and a false branch claim |
| **iteration** | Repair the Workflows/Review v1.0.0 migration output in place: delete the invented marker file, place the tool's constituting document under Tooling/v1.0.0/, restate both entry headings as bare ids, put every status inside the closed set, recompute both ids from their identity fields, and record the Track-B checks in Tests/v1.0.0/RESULTS.md as the tool's evidence |
| **expected_result** | All five Track B checks pass in form; every status is one of the seven; no `resolved` status exists with an empty `merge_commit`; both ids reproduce under `sha256sum` from their identity fields; every branch claim names `smoke/fix-workflows-review`; no code, workflow or test result is invented |
| **change** | `Tooling/v1.0.0/NOTE.md` deleted and `Tooling/v1.0.0/REVIEW.md` added; both entry headings restated as bare ids and the `<a name>` tags dropped; statuses set to `in-progress`; both ids recomputed and every citation rewritten; `Tests/v1.0.0/run-tests.log` replaced by `track-b-checks.log` and `RESULTS.md` rewritten; `README.md` and `TEMPLATES.md` corrected |
| **version** | **v1.0.0** — no bump. v1.0.0 has never been released (`main` still holds the pre-migration `README.md`), so §4 immutability has not attached to it and this is still round 2 of the same fix loop, not a new released version |
| **merge_commit** | *(empty)* — not merged |
| **branch** | `smoke/fix-workflows-review` |
| **date** | 2026-09-01 |

**cause (Y), in detail.** Round 1 ran against a spec that was silent on five
points. PROCESS.md §10's 2026-09-01 decisions closed the silences: 8 (change-id
identity is the `iteration` field), 9 (a code-less tool conforms; its documents
live under `Tooling/`; no marker file is invented), 11 (closed set of seven
statuses), 13 (an entry is a level-2 heading whose text is the bare id), 14
(canonicalisation strips trailing punctuation). Decisions 9 and 10 are the pair
that matters here: 9 requires a code-less tool to conform, 10 makes conforming
possible by accepting a recorded Track-B result as invariant-5 evidence.

**outcome (X), in detail.** The five defects are enumerated in the issue entry.
Their joint effect: the tool looked migrated and was not. Grep-based reciprocity
could not resolve either citation; the Code-layout check had a directory but no
tool in it; and a reader following `merge_commit` would have found an entry
claiming no branch existed while the work sat committed on one.

**iteration (Z), in detail.** As the `iteration` field above. Nothing in it
writes a workflow, a template or a test — the repair is confined to the recording
conventions and to relocating the text that already existed.

**expected_result (V), checkably.** After this iteration:

1. `Tooling/v1.0.0/` holds the document that constitutes the tool, and no file
   whose purpose is to announce that the directory is empty.
2. Every `## ` heading in `KNOWN_ISSUES.md` and `CHANGE_LOG.md` is a bare id
   matching `^[a-z0-9]+(-[a-z0-9]+)*_[0-9a-f]{8}$`.
3. Every `status` value is one of the seven in `definitions.issue-status`, and no
   entry reads `resolved` while its `merge_commit` is empty.
4. Both ids reproduce: canonicalise the identity field, `sha256sum`, first 8 hex.
5. Every branch claim in this tool names `smoke/fix-workflows-review`.
6. Each of the four canonical-document pairs is reciprocal, or vacuously so with
   the vacuity stated rather than the check reworded.

**change (W).** What changed, where, and how it was verified:

1. **`Tooling/v1.0.0/NOTE.md` deleted.** It was the invented marker §4 now
   forbids. Replaced by `Tooling/v1.0.0/REVIEW.md`, which carries the tool's own
   text — the single documented sentence, verbatim — rather than commentary about
   the directory being empty.
2. **Headings.** ``## `<id>` `` became `## <id>` in `KNOWN_ISSUES.md` and
   `CHANGE_LOG.md`, and the redundant `<a name="...">` tags were removed so the
   heading itself is the anchor the citations resolve against. In
   `IMPLEMENTATIONS.md` and `TEMPLATES.md` the level-2 prose headings were
   demoted to level 3: `definitions.entry` counts any level-2 heading as an
   entry, so those two headings were being read as malformed entries and were
   failing reciprocity. Both files now hold zero entries, which is the vacuous
   pass they were meant to have.
3. **Statuses.** `partially resolved` became `in-progress` on issue
   `…_0b0b4b59`; the new issue `…_d18c44d1` is `in-progress`. Neither is
   `resolved`, because neither has a `merge_commit`.
4. **Ids.** Both recomputed with `sha256sum` over the canonicalised identity
   field. The issue-id `workflows-review-fails-track-b-conforman_0b0b4b59`
   reproduced unchanged. The change-id moved from
   `migrate-workflows-review-to-the-track-b_abb4adaf` to
   `create-the-process-md-section-3-document_cddfd0f4`; every citation of the old
   id in this tool was rewritten.
5. **Branch claims.** The round-1 entry claimed "No branch was created, nothing
   was committed". Both entries now name `smoke/fix-workflows-review` and record
   `merge_commit` as empty.
6. **Test record.** `Tests/v1.0.0/run-tests.log` was replaced by
   `track-b-checks.log`. The old log recorded a `python3 -m unittest discover`
   over an empty directory — a vacuous `OK` on `Ran 0 tests`, which corroborates
   nothing — and its closing directory listing had gone stale against the tree.
   The new log is a verbatim transcript, run 2026-09-01, of the absence probes
   and the five Track-B checks. `RESULTS.md` was rewritten to the §4 form: no
   executable suite exists, and here are the Track-B checks run in its place.
7. **Prose.** `README.md` and `TEMPLATES.md` were corrected where they described
   `Tooling/v1.0.0/` as empty or asserted a check result the amended spec states
   differently.

**Verification.** [`Tests/v1.0.0/track-b-checks.log`](Tests/v1.0.0/track-b-checks.log)
— the five Track-B checks plus id reproduction and heading-form checks, run
against the working tree of `smoke/fix-workflows-review` and recorded verbatim.

**Loop position.** Round 2 of the bound of 3 (`loops.fix_loop.max_rounds`). The
bound is not exhausted, so the loop itself does not escalate. One thing is
escalated, and it is a spec gap rather than a tool defect: `process.yaml`
`branches.test_decision` still gates on `./run-tests.sh` exiting 0 and escalates
`on_unknown` when a suite "never ran", which no code-less tool can pass — the
deadlock §10 decision 10 was settled to remove, left in the machine-readable half
of the spec. It is recorded in
[`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) and belongs in
`process.yaml`, not in this tool's `KNOWN_ISSUES.md`. Reading `testing` as
satisfied by the recorded Track-B result (PROCESS.md §5.5, §8), the loop is at
`awaiting_human` —
PROCESS.md §6 steps 5–7 (PR, human approval, merge) have not been performed from
here, and until they are, `merge_commit` stays empty and both issues stay
`in-progress`.
