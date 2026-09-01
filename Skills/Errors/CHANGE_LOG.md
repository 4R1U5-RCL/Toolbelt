# Change log — Skills/Errors

Every iteration made in response to an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), in the
`PROCESS.md` §6 entry format. Each entry's `resolves` field cites the issue it answers, and
that issue cites this entry back (PROCESS.md §3 reciprocity).

An entry is delimited by a level-2 heading whose text is the bare change-id — no backticks,
no title, nothing else on the line (`process.yaml: definitions.entry`).

A change-id's identity is **the `iteration` field alone** (`process.yaml:
definitions.change-id`, PROCESS.md §10.8). Both segments derive from it: the description is
that field run through `slug_rule`, and the hash8 is the first 8 hex characters of
`sha256` over the canonical form of that field — trimmed, lowercased, whitespace runs
collapsed to a single space, trailing `. , ; : ! ?` stripped (§10.14). Both ids below were
recomputed with `sha256sum` on 2026-09-01 and reproduce exactly.

Versions are the directories under `Tooling/`; a released version directory is immutable
and is the rollback point (PROCESS.md §4). `v1.0.0` has not been released — it has never
merged to `main` — so both entries below belong to it and neither bumps the version.

---

## migrate-skills-errors-to-the-process-md_58690b69

- **id:** `migrate-skills-errors-to-the-process-md_58690b69`
- **resolves:** [`KNOWN_ISSUES.md#skills-errors-fails-track-b-conformance_4b9a21ed`](KNOWN_ISSUES.md#skills-errors-fails-track-b-conformance_4b9a21ed)
- **cause:** The tool was transferred from `operand-packages` in its pre-PROCESS.md shape
  (README + loose `templates/` and `tests/`), and nothing enforces the §3/§4 layout at
  transfer time — so the conventions were never applied to it. This is the §9 migration
  backlog.
- **outcome:** Four of the five Track B checks failed: four canonical documents missing,
  code not under `Tooling/`, no recorded results under `Tests/`, and a README naming no
  version — leaving the tool unable to release a version and without an in-repo rollback
  point. Full detail in the issue entry.
- **iteration:** Migrate Skills/Errors to the PROCESS.md layout at v1.0.0 and create the missing canonical documents
- **expected_result:** All five Track B checks pass for `Skills/Errors` at `v1.0.0`:
  1. all five canonical files exist at the tool root and are non-empty;
  2. `Tooling/v1.0.0/` holds the tool's code;
  3. `Tests/v1.0.0/` holds the actual output of running that version's tests;
  4. `README.md`, the newest `Tooling/` directory and the newest `CHANGE_LOG.md` entry all
     name `v1.0.0`;
  5. reciprocity holds — this entry and its issue cite each other, and every
     `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` entry and vice versa.
- **change:** A documents-and-layout migration with **no behaviour change**. The code did
  not change, it moved.
  - **Moved** (no edits to the moved files): `templates/` → `Tooling/v1.0.0/templates/`
    and `tests/` → `Tooling/v1.0.0/tests/`. Test code ships inside the version it tests
    (PROCESS.md §4).
  - **Path repair: none required, verified rather than assumed.**
    `Tooling/v1.0.0/tests/verify.sh` resolves its own location with
    `HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"` and reads the templates from
    `PKG="$HERE/.."`, so the move preserved the relationship it depends on. It is the only
    executable in the tool; there is no `bin/`, no `sys.path` manipulation, and no import
    that assumes a directory depth. **It has no `run-tests.sh`** — the runner is
    `bash tests/verify.sh`.
  - **Created** `Tests/v1.0.0/verify.log` — verbatim output of the self-check — and
    `Tests/v1.0.0/RESULTS.md` recording what was run, from where, when, and the outcome.
  - **Created** `IMPLEMENTATIONS.md` (four use cases derived from the README and the
    shipped files, each citing its template), `TEMPLATES.md` (the three templates actually
    present in `Tooling/v1.0.0/templates/`, each citing the implementations that use it),
    `KNOWN_ISSUES.md` (header + the issue this entry resolves), and this `CHANGE_LOG.md`.
  - **Edited** `README.md`, minimally: it now states the current version `v1.0.0` and
    links the version directories and the four new documents; the three `templates/…`
    paths in its "What's here" table, the `copy templates/…` line in the Quickstart and the
    self-check line were repointed at `Tooling/v1.0.0/…`; and its "Known issues / caveats"
    section now says explicitly that it describes the live studio registry, not this tool,
    and points at `KNOWN_ISSUES.md`. No other prose was changed.
- **verified_by:** `bash tests/verify.sh`, run on 2026-09-01 from
  `Skills/Errors/Tooling/v1.0.0/` on branch `smoke/fix-skills-errors` — **32 passed, 0
  failed**, exit code 0. Output recorded verbatim at
  [`Tests/v1.0.0/verify.log`](Tests/v1.0.0/verify.log); see
  [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md). This re-run is byte-identical to
  the output the migration recorded on 2026-08-31, so the earlier record is corroborated
  rather than merely restated.
- **version:** `v1.0.0` — the tool's current version. No bump: the code moved, it did not
  change, and a tool that has never been versioned starts at `v1.0.0` (PROCESS.md §9,
  §10.6).
- **merge_commit:** *(empty — not merged.)* This work is on branch
  `smoke/fix-skills-errors` in the working tree. No PR has been opened and nothing has
  reached `main`; the PR and merge (PROCESS.md §5.4/§8) are handled outside this run, and
  this field is filled in on merge. Because it is empty, the issue this entry resolves is
  `in-progress`, not `resolved`.

---

## correct-the-skills-errors-migration-entr_fc96ca88

- **id:** `correct-the-skills-errors-migration-entr_fc96ca88`
- **resolves:** [`KNOWN_ISSUES.md#skills-errors-migration-entries-violate_329e05c5`](KNOWN_ISSUES.md#skills-errors-migration-entries-violate_329e05c5)
- **cause:** The migration ran against the PROCESS.md of 2026-08-31; decisions 8 and 11–14
  (change-id identity, the closed status set, the entry heading form, the
  trailing-punctuation strip) were settled on 2026-09-01, after it. The false branch claim
  has a separate cause: the §6 step 3 wording was copied into the record as though the step
  had been performed, instead of reporting the repository's actual state.
- **outcome:** A status string outside the closed set of seven (and asserting `resolved`
  with an empty `merge_commit`), a document asserting the work "sits on a branch" when no
  branch existed, backticked entry headings in all four entry-bearing documents, and two
  ids whose correctness under the amended rules had never been demonstrated. Full detail in
  the issue entry.
- **iteration:** Correct the Skills/Errors migration entries to the amended PROCESS.md: closed-set status, a true branch statement, bare-id entry headings, and ids recomputed and reverified
- **expected_result:** Checkably, on this branch:
  1. every `status` value in `KNOWN_ISSUES.md` is one of the seven in
     `process.yaml: definitions.issue-status`;
  2. no entry reads `resolved` while its change entry's `merge_commit` is empty;
  3. every statement about a branch in these documents names `smoke/fix-skills-errors`,
     which exists and is the branch the work is on — `git branch --show-current` returns it;
  4. every entry heading in `KNOWN_ISSUES.md`, `CHANGE_LOG.md`, `IMPLEMENTATIONS.md` and
     `TEMPLATES.md` matches `^## <bare-id>$`, and every `FILE.md#<id>` citation resolves to
     one of those headings;
  5. both ids reproduce from their identity fields under the amended canonicalisation, as
     computed with `sha256sum`;
  6. reciprocity holds for **both** non-legacy issue/change pairs and for every
     `IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` pair;
  7. version agreement holds — `README.md`, the newest `Tooling/` directory and the newest
     `CHANGE_LOG.md` entry all name `v1.0.0`;
  8. `bash tests/verify.sh` still passes 32/32 from `Tooling/v1.0.0/`.
- **change:** Documents only. **No file under `Tooling/v1.0.0/` was modified**, so the
  tool's behaviour is untouched and no version is bumped.
  - **`KNOWN_ISSUES.md`** — heading of the existing entry changed to the bare id; `status`
    changed from the free-text `resolved in the working tree — pending the PR merge to
    main` to `in-progress`, with the reasoning moved to a `status_note` field; the header
    now states the closed status set and records that this tool has **no** `legacy`
    entries (it had only a `README.md` before the migration, so every entry is bound by
    reciprocity). The audit's own findings are appended as
    `skills-errors-migration-entries-violate_329e05c5`.
  - **`CHANGE_LOG.md`** — heading changed to the bare id; the non-spec `summary` field
    removed and the `iteration` field made to carry the statement of Z that the change-id
    is derived from, so the id is reproducible under §10.8 (the field now holds the exact
    string the migration had hashed, which is why the id itself is unchanged); the
    `merge_commit` field rewritten to state the true position — empty, on branch
    `smoke/fix-skills-errors`, no PR; `verified_by` rewritten to describe the run actually
    performed on 2026-09-01. This entry appended.
  - **`IMPLEMENTATIONS.md` / `TEMPLATES.md`** — entry ids lowercased (`IMP-scaffold` →
    `imp-scaffold`, `TPL-hub` → `tpl-hub`, and so on) and headings reduced to the bare id
    with the title moved onto the following line, so heading text, anchor and citation are
    the same string; the now-redundant `<a name=…>` anchors removed; every cross-citation
    updated.
  - **`Tests/v1.0.0/`** — `run-tests.log` renamed to `verify.log`. The old name implied a
    `run-tests.sh` this tool does not have. `RESULTS.md` rewritten to record the 2026-09-01
    run: the command, the directory it was run from, the exit code and the verbatim output.
  - **`README.md`** — the self-check line now names the runner and the directory it is run
    from, and states the recorded result's date.
- **verified_by:** `bash tests/verify.sh`, run on 2026-09-01 from
  `Skills/Errors/Tooling/v1.0.0/` — **32 passed, 0 failed**, exit code 0
  ([`Tests/v1.0.0/verify.log`](Tests/v1.0.0/verify.log)). That suite tests the templates,
  not these documents, so it corroborates only expected_result item 8 — it confirms the
  documents-only change did not disturb the tool. Items 1–7 are Track B conformance checks;
  they were checked by inspection and by `grep`/`sha256sum` against the tree on this
  branch, and the results are recorded in
  [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md). Per PROCESS.md §5.5 as amended by
  §10.10, a recorded Track-B result is admissible evidence.
- **version:** `v1.0.0` — unchanged. `v1.0.0` has never merged, so it is not a released,
  immutable directory; correcting its records is the append-only root-document exception of
  §5 safeguard 2, not an edit to a frozen version.
- **merge_commit:** *(empty — not merged.)* On branch `smoke/fix-skills-errors`; no PR
  opened, nothing on `main`. Filled in on merge.
