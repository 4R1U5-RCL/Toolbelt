# Change log — Skills/Handoff

Every iteration made in response to an entry in [KNOWN_ISSUES.md](KNOWN_ISSUES.md).
Ids are computed per `process.yaml` `definitions.change-id` — identity is the
`iteration` field alone (PROCESS.md §10.8). Entry headings are the bare id
(`definitions.entry.heading_form`).

| id | Resolves | Version |
|---|---|---|
| [bring-the-tool-into-3-4-conformance-at-v_54324955](#bring-the-tool-into-3-4-conformance-at-v_54324955) | [skills-handoff-fails-track-b-conformance_761fac80](KNOWN_ISSUES.md#skills-handoff-fails-track-b-conformance_761fac80) | v1.0.0 |

---

## bring-the-tool-into-3-4-conformance-at-v_54324955

| Field | Value |
|---|---|
| **id** | `bring-the-tool-into-3-4-conformance-at-v_54324955` |
| **summary** | Migrate Skills/Handoff to the Track B layout at v1.0.0 and create the four missing canonical documents |
| **resolves** | [KNOWN_ISSUES.md#skills-handoff-fails-track-b-conformance_761fac80](KNOWN_ISSUES.md#skills-handoff-fails-track-b-conformance_761fac80) |
| **version** | **v1.0.0** — no bump. The code did not change, it moved. Per PROCESS.md §9 a tool that has never been versioned starts at v1.0.0, and this iteration establishes that version rather than succeeding one |
| **merge_commit** | *(empty)* — nothing has merged. The work is on branch `smoke/fix-skills-handoff`, which is not pushed and has no PR. §6 step 7 fills this in on merge; until then `KNOWN_ISSUES.md` holds the issue at `in-progress`, never `resolved` |
| **date** | 2026-08-31 (migration); corrected 2026-09-01 |

**Identity.** The id derives from the `iteration (Z)` field below, alone
(`process.yaml` `definitions.change-id`, PROCESS.md §10.8). Canonical string
(trim → lowercase → collapse whitespace → strip trailing `. , ; : ! ?`):

```
bring the tool into §3/§4 conformance at v1.0.0 without changing a line of its behaviour
```

`sha256` = `543249555511c74d…`, so `hash8` = `54324955`; the slug rule truncates
the iteration to `bring-the-tool-into-3-4-conformance-at-v`. Computed with
`sha256sum` on 2026-09-01.

**cause (Y).** `Skills/Handoff` was transferred from `operand-packages` as a flat
package directory and never brought through PROCESS.md §9's conformance step;
the §3/§4 conventions postdate it and nothing forced the gap shut.

**outcome (X).** Four canonical documents were missing (`IMPLEMENTATIONS.md`,
`TEMPLATES.md`, `KNOWN_ISSUES.md`, `CHANGE_LOG.md`), the code sat at the tool
root with no `Tooling/v<version>/` rollback point, no `Tests/` directory backed
the README's `15/15` claim, and `README.md` named no version — so the tool could
not release a new version and its staleness was invisible.

**iteration (Z).** Bring the tool into §3/§4 conformance at v1.0.0 without
changing a line of its behaviour.

**expected_result (V).** All five Track B checks of §7 pass for `Skills/Handoff`:
five non-empty canonical files at the tool root; reciprocal citation in both
document pairs; code under `Tooling/v1.0.0/`; recorded results under
`Tests/v1.0.0/`; and `README.md`, the newest `Tooling/` directory and the newest
`CHANGE_LOG.md` entry all naming **v1.0.0**. The suite must still pass from its
new location — a move that breaks the tool is not a conformance fix.

**change (W).** What changed, where, and how it was verified:

1. **Layout.** `commands/`, `templates/` and `tests/` moved from the tool root
   into `Tooling/v1.0.0/` (plain `mv`; contents untouched). The five canonical
   `.md` files stay at the tool root. Test *code* moved with the version, per §4.
2. **Paths.** Checked, and none needed repair.
   `Tooling/v1.0.0/tests/verify.sh` resolves its package root from
   `${BASH_SOURCE[0]}` (`HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PKG="$(cd "$HERE/.." && pwd)"`),
   and the two paths it reads — `$PKG/commands/handoff.md` and
   `$PKG/templates/handoff-template.md` — moved with it, so the relationship is
   unchanged. There is no `run-tests.sh`, no `bin/` entrypoint and no Python in
   this package, so there was no `cd` assumption, `sys.path` manipulation or
   import depth to fix. Verified by running the suite from an unrelated working
   directory as well as from `Tooling/v1.0.0/`; both exit 0.
3. **Recorded results.** `Tests/v1.0.0/run-tests.log` holds the verbatim output
   of `bash tests/verify.sh` run from `Tooling/v1.0.0/`; `Tests/v1.0.0/RESULTS.md`
   states what was run, when, and the outcome.
4. **Documents.** `IMPLEMENTATIONS.md` (four use cases, each citing a
   `TEMPLATES.md` id), `TEMPLATES.md` (the two shipped forms, each citing back),
   `KNOWN_ISSUES.md` (header + the conformance entry) and this file created.
5. **README.md.** A `Version: v1.0.0` line added, and the file-location and
   install/test paths updated to their `Tooling/v1.0.0/` form. No other edit.
6. **Conformance corrections, 2026-09-01** (branch `smoke/fix-skills-handoff`).
   The migration's own entries failed the amended spec, so they were corrected
   in place — they are unmerged and unreleased, so nothing released was
   overwritten:
   - `KNOWN_ISSUES.md` status `resolved` → `in-progress`; a `resolved` with an
     empty `merge_commit` is forbidden (`definitions.issue-status`) and untrue —
     nothing has merged.
   - This entry's id recomputed under the new `change-id` identity rule (§10.8,
     the `iteration` field alone). It was `migrate-skills-handoff-to-the-track-b-la_bf26568c`,
     derived from the `summary`; it is now
     `bring-the-tool-into-3-4-conformance-at-v_54324955`. Every citation of the
     old id — the index table here, two in `KNOWN_ISSUES.md`, one in
     `Tests/v1.0.0/RESULTS.md` — was updated. The issue-id was recomputed too and
     is unchanged (`761fac80`).
   - All entry headings in the four prose documents changed from
     `` ## `id` `` to the bare `## id` form (`definitions.entry.heading_form`),
     and the now-redundant `<a name>` anchors were dropped; the heading text is
     the anchor.
   - `merge_commit` stated as empty rather than as prose implying a pending
     record.

**Verification.** `bash tests/verify.sh` from `Tooling/v1.0.0/` — **15 passed,
0 failed**, exit 0. Re-run 2026-09-01 on branch `smoke/fix-skills-handoff`; full
verbatim output in [Tests/v1.0.0/run-tests.log](Tests/v1.0.0/run-tests.log).

**Honest gaps at the time of writing.** The suite is a conformance smoke test of
the *shipped package*, not of a live `/handoff` run — it can corroborate that
this move broke nothing, and nothing more. It does not exercise the logged
failure in the Track-A sense, because the logged failure is a **layout**
failure: the corroborating evidence for it is the Track-B conformance result
(§5.5, §8, §10.10), not the smoke suite. `process.yaml`'s `test_decision` names
`./run-tests.sh`, which this tool does not have; the suite is invoked as
`bash tests/verify.sh` instead, and adding a wrapper was deliberately not done
because it would be a code change under a no-bump entry. The merge commit is
recorded by §6 step 7 once it exists.
