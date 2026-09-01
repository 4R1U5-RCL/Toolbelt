# Change log — Skills/Handoff

Every iteration made in response to an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).
Ids are computed per `process.yaml` `definitions.change-id`.

| id | Resolves | Version |
|---|---|---|
| [`migrate-skills-handoff-to-the-track-b-la_bf26568c`](#migrate-skills-handoff-to-the-track-b-la_bf26568c) | [`skills-handoff-fails-track-b-conformance_761fac80`](KNOWN_ISSUES.md#skills-handoff-fails-track-b-conformance_761fac80) | v1.0.0 |

---

<a name="migrate-skills-handoff-to-the-track-b-la_bf26568c"></a>
## `migrate-skills-handoff-to-the-track-b-la_bf26568c`

| Field | Value |
|---|---|
| **id** | `migrate-skills-handoff-to-the-track-b-la_bf26568c` |
| **summary** | Migrate Skills/Handoff to the Track B layout at v1.0.0 and create the four missing canonical documents |
| **resolves** | [`KNOWN_ISSUES.md#skills-handoff-fails-track-b-conformance_761fac80`](KNOWN_ISSUES.md#skills-handoff-fails-track-b-conformance_761fac80) |
| **version** | **v1.0.0** — no bump. The code did not change, it moved. Per PROCESS.md §9 a tool that has never been versioned starts at v1.0.0, and this iteration establishes that version rather than succeeding one |
| **merge_commit** | not yet recorded — this iteration ran before merge; all git operations are performed outside it (see the note at the end) |
| **date** | 2026-08-31 |

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

**Verification.** `bash tests/verify.sh` from `Tooling/v1.0.0/` — **15 passed,
0 failed**, exit 0, on 2026-08-31. Full output in
[`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log).

**Honest gaps at the time of writing.** The suite is a conformance smoke test of
the *shipped package*, not of a live `/handoff` run — it can corroborate that
this move broke nothing, and nothing more. `process.yaml`'s `test_decision`
names `./run-tests.sh`, which this tool does not have; the suite is invoked as
`bash tests/verify.sh` instead, and adding a wrapper was deliberately not done
because it would be a code change under a no-bump entry. The merge commit is
recorded by §6 step 7 once it exists.
