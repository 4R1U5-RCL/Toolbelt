# Known issues — Skills/Scratch

Every issue found with this tool, each linking to the iteration that fixed it in
[`CHANGE_LOG.md`](CHANGE_LOG.md) (PROCESS.md §3, reciprocal pair).

**Append-only** — PROCESS.md §5 invariant 1. Entries are never rewritten; a fix
appends, carrying the version of the iteration that resolved it.

Ids follow `process.yaml: definitions.issue-id` — `<description>_<hash8>`, where
the description is the summary slugified and truncated to 40 characters and the
hash is the first 8 hex characters of `sha256` over the canonical (trimmed,
lowercased, whitespace-collapsed) summary.

> **Not yet entries.** `README.md` carries a "Known issues / caveats" section of
> six numbered caveats (same-filesystem-only scratch; the ephemeral session
> scratchpad; the `clients/` double-repo trap; no auto-clean; unreliable peer
> registration; `.gitignore` being advisory rather than a technical barrier).
> They are real and they are documented, but they were written as README prose,
> not as entries in this file, and none has an id or a `CHANGE_LOG.md`
> counterpart. Migrating them into entries would mean assigning ids and causes to
> issues this iteration did not diagnose, so they are left where they are and
> named here instead.

| ID | Summary | Status |
|---|---|---|
| [`skills-scratch-failed-track-b-conformanc_5a423163`](#skills-scratch-failed-track-b-conformanc_5a423163) | Failed Track B conformance — four canonical documents missing, no `Tooling/`, no `Tests/`, no version in the README | resolved (`v1.0.0`) |

---

<a name="skills-scratch-failed-track-b-conformanc_5a423163"></a>
## `skills-scratch-failed-track-b-conformanc_5a423163`

| Field | Value |
|---|---|
| **id** | `skills-scratch-failed-track-b-conformanc_5a423163` |
| **status** | `resolved` |
| **resolved_by** | [`CHANGE_LOG.md#migrate-skills-scratch-to-the-tooling-te_96add0eb`](CHANGE_LOG.md#migrate-skills-scratch-to-the-tooling-te_96add0eb) at fix-version `v1.0.0` |
| **occurrences** | 1 — found 2026-08-31 by running the Track B checks of PROCESS.md §7 against this tool directory by hand |

**summary.** Skills/Scratch failed Track B conformance: four canonical documents
missing, code not under Tooling/, no recorded results under Tests/, and README
stated no version.

**outcome (X).** Measured against the five Track B checks of PROCESS.md §7, as
found on 2026-08-31. The tool directory contained exactly three things:
`README.md`, `templates/scratch.gitignore` and `tests/verify.sh`.

| Check | Result as found |
|---|---|
| Canonical files | **FAIL** — one of five present. `README.md` existed and was non-empty; `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and `CHANGE_LOG.md` did **not** exist. This matches the §9 backlog table row for `Skills/Scratch` exactly |
| Code layout | **FAIL** — no `Tooling/` directory. `templates/` and `tests/` sat at the tool root, so the test *code* was not inside the version it tests (§4) |
| Test layout | **FAIL** — no `Tests/` directory, and therefore no recorded result anywhere in the repo. The README asserted "**29/29**", and that claim was true when re-run, but the repo held no evidence for it: the outcome existed only in the memory of whoever last ran the script |
| Version agreement | **FAIL** — `README.md` named **no version at all**. With no `Tooling/` directory and no `CHANGE_LOG.md` either, none of the three sources the check compares existed, so there was nothing to agree |
| Reciprocity | **VACUOUS, both pairs.** `KNOWN_ISSUES.md` ↔ `CHANGE_LOG.md`: neither file existed. `IMPLEMENTATIONS.md` ↔ `TEMPLATES.md`: neither file existed. The check could not fail on a bad citation because there were no entries to cite |

Consequence: under §7, "a tool failing Track B cannot release a new version" —
the next genuine fix to this tool was blocked before it could start. The
practical cost was the test-layout failure: the tool's only executable claim
("29/29") was unauditable from the repository alone.

**cause (Y).** The tool predates `PROCESS.md`. Both `PROCESS.md` and
`process.yaml` are dated 2026-08-31 and describe this exact directory in their
own §9 migration backlog, where `Skills/Scratch` is listed with `README` ✅ and
every other column ❌. The layout is not drift away from the convention; it is
code written before the convention existed. Nothing in the tool enforces the
convention — it has no build, no CI and no packaging step — so nothing failed
loudly when it was unmet. The gap was visible only by reading the directory
against §3 and §4 by hand, which is the mechanism §7 Track B exists to replace.

**iteration (Z).** Bring the tool into conformance as its first pass through §6:
move `templates/` and `tests/` into `Tooling/v1.0.0/` (§9 — a tool that has never
been versioned starts at `v1.0.0`), repair the paths the move breaks, run the
suite from its new location and record the verbatim output under `Tests/v1.0.0/`,
create the four missing canonical files empty-but-valid, and state the current
version in `README.md`. Planned and recorded in
[`CHANGE_LOG.md#migrate-skills-scratch-to-the-tooling-te_96add0eb`](CHANGE_LOG.md#migrate-skills-scratch-to-the-tooling-te_96add0eb).

**What the move actually broke.** Recorded because it is the part §5 invariant 6
exists to catch, and because the suite was run before, during and after the move
rather than only at the end. `tests/verify.sh` resolves `PKG` as one directory
above itself and then asserts `grep -q "scratch.gitignore" "$PKG/README.md"` —
the check that the README still points at the shipped template. At the tool root
that resolved to the README. One level deeper it resolved to
`Tooling/v1.0.0/README.md`, which does not and must not exist, because §3 keeps
the five canonical documents at the tool root. Run from the new location before
repair, the suite printed `grep: .../Tooling/v1.0.0/README.md: No such file or
directory`, `FAIL · README points at the shipped template`, `28 passed, 1
failed`, exit `1`. It failed loudly rather than silently skipping, which is the
better of the two failure modes. Fixed by resolving the tool root explicitly
(`TOOLROOT`, two levels above the version directory) and pointing the check
there. Evidence in [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md): 29
passed, 0 failed, exit 0, with that check reading `PASS`.

**Still open after this iteration.** Stated rather than silently carried:

- **No `run-tests.sh`.** This tool has never had one; the suite is invoked as
  `bash tests/verify.sh`. `process.yaml`'s `test_decision` branch tests
  "`./run-tests.sh` exits 0", so a strict reading of that branch cannot be
  evaluated for this tool. Adding an entrypoint is a code change, and this
  iteration moved code without changing it, so it was not added here.
- **The six README caveats are not entries in this file** (see the note under the
  header). They carry no ids and no `CHANGE_LOG.md` counterparts.
- **`IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` reciprocity is by slug, not by id.**
  `process.yaml` defines an id format for `issue-id` and `change-id` only; it
  defines none for template or implementation entries, so those two files cite
  each other by plain anchor slug. A strict id-level reciprocity check would have
  nothing to match against.
- **The tool is one template and one test.** `TEMPLATES.md` documents the single
  artifact in `templates/`; the surface-selection half of the discipline is prose
  with no template behind it. That is the tool's real shape, not a gap this
  iteration should have filled by inventing artifacts.
