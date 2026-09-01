# Known issues — Skills/Handoff

Append-only (PROCESS.md §5.1). Every entry carries an id computed per
`process.yaml` `definitions.issue-id` and cites the `CHANGE_LOG.md` entry that
resolves it.

| id | Summary | Status |
|---|---|---|
| [`skills-handoff-fails-track-b-conformance_761fac80`](#skills-handoff-fails-track-b-conformance_761fac80) | Track B conformance failure found at migration | resolved |

The four caveats the README has always carried — hard-coded studio paths, the
topic-blind 4h scope test, curation being model judgment, and a handoff being a
snapshot rather than the durable store — are documented in `README.md` under
*Known issues / caveats*. They are not restated here as entries because no
iteration has been planned against them; doing so would require inventing an
`iteration` field that does not exist.

---

<a name="skills-handoff-fails-track-b-conformance_761fac80"></a>
## `skills-handoff-fails-track-b-conformance_761fac80`

| Field | Value |
|---|---|
| **id** | `skills-handoff-fails-track-b-conformance_761fac80` |
| **summary** | Skills/Handoff fails Track B conformance: four canonical documents missing, code not under Tooling/, no recorded test results under Tests/, README names no version |
| **source** | PROCESS.md §7 Track B check run against `Skills/Handoff` during the migration of this tool |
| **occurred_at** | 2026-08-31 |
| **tool** | `Skills/Handoff` |
| **status** | resolved |
| **resolved_by** | [`CHANGE_LOG.md#migrate-skills-handoff-to-the-track-b-la_bf26568c`](CHANGE_LOG.md#migrate-skills-handoff-to-the-track-b-la_bf26568c) at fix-version **v1.0.0** |
| **occurrences** | 1 — 2026-08-31, the migration run |

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
("a tool that has never been versioned starts at v1.0"): move `commands/`,
`templates/` and `tests/` into `Tooling/v1.0.0/`, leave the canonical `.md`
files at the tool root, run the suite from its new location and record the
verbatim output under `Tests/v1.0.0/`, create the four missing documents, and
state `v1.0.0` in `README.md`. Planned and recorded in
[`CHANGE_LOG.md#migrate-skills-handoff-to-the-track-b-la_bf26568c`](CHANGE_LOG.md#migrate-skills-handoff-to-the-track-b-la_bf26568c).

**Note on `resolved`.** The layout, the documents and the recorded results are
in place and the suite passes 15/15 from the new location
(`Tests/v1.0.0/run-tests.log`). The merge commit is not yet recorded — this
migration ran before merge and all git operations are performed outside it. §6
step 7 (`write_version` → `close_issue`) completes when that commit exists.
