# Known issues — Skills/Errors

Every issue found with **this tool** (the templates and their self-check), in the
`PROCESS.md` §6 entry format. Append-only (PROCESS.md §5.1): entries are never rewritten,
and a fix appends the version that resolved it. Each entry cites the
[`CHANGE_LOG.md`](CHANGE_LOG.md) entry that answers it.

> Not to be confused with the **"Known issues / caveats"** section of
> [`README.md`](README.md), which records defects of the *live studio registry this tool
> was distilled from* — not of the tool itself.

---

<a name="skills-errors-fails-track-b-conformance_4b9a21ed"></a>
## `skills-errors-fails-track-b-conformance_4b9a21ed`

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
- **iteration:** Bring the tool into conformance under PROCESS.md §9 without changing its
  behaviour: move `templates/` and `tests/` into `Tooling/v1.0.0/` (a tool that has never
  been versioned starts at `v1.0.0` per §9/§10.6), run the existing self-check from its new
  location, record the actual output under `Tests/v1.0.0/`, create the four missing
  canonical documents, and correct `README.md` to name `v1.0.0`. Recorded in
  [`CHANGE_LOG.md#migrate-skills-errors-to-the-process-md_58690b69`](CHANGE_LOG.md#migrate-skills-errors-to-the-process-md_58690b69).
- **resolved_by:** [`CHANGE_LOG.md#migrate-skills-errors-to-the-process-md_58690b69`](CHANGE_LOG.md#migrate-skills-errors-to-the-process-md_58690b69) at version `v1.0.0`
- **status:** resolved in the working tree — pending the PR merge to `main`, which is the
  only path to `main` (PROCESS.md §5.4/§8) and is handled outside this run.
- **occurrences:**
  | # | When | Where | Note |
  |---|---|---|---|
  | 1 | 2026-08-31 | `Skills/Errors` | Found by the §9 migration pass; the state it found is the outcome recorded above. |
