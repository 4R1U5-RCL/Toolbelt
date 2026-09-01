# Known issues — Skills/Handoff

Append-only (PROCESS.md §5.1). Every entry carries an id computed per
`process.yaml` `definitions.issue-id` and cites the `CHANGE_LOG.md` entry that
resolves it. Entry headings are the bare id (`process.yaml`
`definitions.entry.heading_form`); statuses come from the closed set of seven in
`definitions.issue-status`.

| id | Summary | Status |
|---|---|---|
| [skills-handoff-fails-track-b-conformance_761fac80](#skills-handoff-fails-track-b-conformance_761fac80) | Track B conformance failure found at migration | in-progress |

The four caveats the README has always carried — hard-coded studio paths, the
topic-blind 4h scope test, curation being model judgment, and a handoff being a
snapshot rather than the durable store — are documented in `README.md` under
*Known issues / caveats*. They are not restated here as entries because no
iteration has been planned against them; doing so would require inventing an
`iteration` field that does not exist.

---

## skills-handoff-fails-track-b-conformance_761fac80

| Field | Value |
|---|---|
| **id** | `skills-handoff-fails-track-b-conformance_761fac80` |
| **summary** | Skills/Handoff fails Track B conformance: four canonical documents missing, code not under Tooling/, no recorded test results under Tests/, README names no version |
| **source** | PROCESS.md §7 Track B check run against `Skills/Handoff` during the migration of this tool |
| **occurred_at** | 2026-08-31 |
| **tool** | `Skills/Handoff` |
| **status** | `in-progress` |
| **resolved_by** | [CHANGE_LOG.md#bring-the-tool-into-3-4-conformance-at-v_54324955](CHANGE_LOG.md#bring-the-tool-into-3-4-conformance-at-v_54324955), planned fix-version **v1.0.0**. Not merged — see *Status* below |
| **occurrences** | 1 — 2026-08-31, the migration run |

**Identity.** The id reproduces from the `summary` field alone
(`process.yaml` `definitions.issue-id`, PROCESS.md §10.3). Canonical string
(trim → lowercase → collapse whitespace → strip trailing `. , ; : ! ?`):

```
skills/handoff fails track b conformance: four canonical documents missing, code not under tooling/, no recorded test results under tests/, readme names no version
```

`sha256` = `761fac804bdc81b0…`, so `hash8` = `761fac80`; the slug rule truncates
the summary to `skills-handoff-fails-track-b-conformance`. Recomputed with
`sha256sum` on 2026-09-01 under the amended canonicalisation — unchanged.

**outcome (X).** Four of the five canonical files of §3 did not exist:
`IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and `CHANGE_LOG.md`.
Only `README.md` was present. The tool's code — `commands/`, `templates/`,
`tests/` — sat directly at the tool root with no `Tooling/v<version>/`
directory, so §4's rollback point did not exist and there was no immutable
released version to iterate away from. No `Tests/` directory existed, so the
`15/15` result the README asserts had no recorded output backing it; the claim
was unverifiable from the repo. `README.md` named no version anywhere, so the
Version-agreement check of §7 had nothing to compare. Concretely: the tool could
not release a new version, and its staleness was invisible — exactly the failure
mode §1 exists to prevent.

**cause (Y).** The tool was transferred from `operand-packages` as a flat
package directory and never brought through §9's conformance step. The
conventions of §3 and §4 postdate it, and nothing in the repo forced the gap
shut: PROCESS.md §9 records the same state for every tool in the backlog table,
`Skills/Handoff` among them (`README ✅`, all six other columns `❌`). It is a
missing migration, not a defect in the skill — the skill itself runs and its
suite passes.

**iteration (Z).** Migrate the tool to the §3/§4 layout at **v1.0.0** per §9
("a tool that has never been versioned starts at v1.0.0"): move `commands/`,
`templates/` and `tests/` into `Tooling/v1.0.0/`, leave the canonical `.md`
files at the tool root, run the suite from its new location and record the
verbatim output under `Tests/v1.0.0/`, create the four missing documents, and
state `v1.0.0` in `README.md`. Planned and recorded in
[CHANGE_LOG.md#bring-the-tool-into-3-4-conformance-at-v_54324955](CHANGE_LOG.md#bring-the-tool-into-3-4-conformance-at-v_54324955).

**Status: `in-progress`, not `resolved`.** The layout, the documents and the
recorded results are in place and the suite passes 15/15 from the new location
(`Tests/v1.0.0/run-tests.log`, re-run 2026-09-01). Nothing has merged: the work
sits on branch `smoke/fix-skills-handoff`, which is not pushed and has no PR, so
`merge_commit` in the change entry is empty. `process.yaml`
`definitions.issue-status` states plainly that `resolved` is never written while
`merge_commit` is empty — an approved-but-unmerged fix is `in-progress`. §6 step 7
(`write_version` → `close_issue`) flips this to `resolved` when the merge commit
exists, and not before.

**Correction — 2026-09-01.** This entry was written by the 2026-08-31 migration
with `status: resolved` and no merge commit, and with a backticked heading. Both
are Track-B conformance failures under the amended spec (PROCESS.md §10.11/§10.13,
`process.yaml` `definitions.issue-status`, `definitions.entry`). Corrected in
place on branch `smoke/fix-skills-handoff`: status → `in-progress`, heading → the
bare id, and the `CHANGE_LOG.md` citation → the change-id recomputed under the
amended `change-id` identity rule (§10.8 — the `iteration` field alone). The
entry is unmerged and unreleased, so correcting it does not overwrite released
history; the identity fields (`id`, `summary`) are untouched.
