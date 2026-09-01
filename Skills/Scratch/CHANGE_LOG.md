# Change log — iterations made in response to issues

Every entry here answers an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) and
cites its id, per PROCESS.md §3 (reciprocal pair) and §6. Newest last; entries
are appended, never rewritten.


> **Correction, 2026-09-01 (branch `smoke/fix-skills-scratch`).** The entry below
> was written by the 2026-08-31 migration and has never been merged or released.
> An audit found it non-conformant, so it was corrected in place: the `id` was
> **recomputed** from the `iteration` field under the amended identity rule
> (§10.8) — the old id derived from the `summary`, which is no longer the
> identity — `merge_commit` was made an honest empty, and the heading was put in
> bare-id form. `resolves` and `iteration` are unchanged, so the recomputed id is
> stable. `id` is normally immutable; it is rewritten here only because this
> entry has never been merged or released and its old value cannot be reproduced
> under the current rule. Correcting an unreleased entry is not an append-only
> violation; overwriting a released one would be.

Ids follow `process.yaml: definitions.change-id` — `<description>_<hash8>`. Both
segments derive from the **`iteration` field alone** (PROCESS.md §10.8): the
description is that field slugified and truncated to 40 characters, and the hash
is the first 8 hex characters of `sha256` over its canonical form. **Canonical**
= trim → lowercase → collapse whitespace runs to a single space → strip trailing
punctuation (`. , ; : ! ?`) (§10.14). The identity string is the field's literal
markdown text as written below, backticks included — the spec defines no markdown
normalisation step. The id below was recomputed with `sha256sum` on 2026-09-01
and reproduces.

---

<a name="move-the-implementation-into-tooling-v1_c96a11ad"></a>
## move-the-implementation-into-tooling-v1_c96a11ad

| Field | Value |
|---|---|
| **id** | `move-the-implementation-into-tooling-v1_c96a11ad` |
| **resolves** | [`KNOWN_ISSUES.md#skills-scratch-failed-track-b-conformanc_5a423163`](KNOWN_ISSUES.md#skills-scratch-failed-track-b-conformanc_5a423163) |
| **version** | `v1.0.0` — current version, **no bump**. The code did not change, it moved (PROCESS.md §9: a tool that has never been versioned starts at `Tooling/v1.0.0/`) |
| **merge_commit** | *(empty — nothing has merged)*. The work is committed on branch `smoke/fix-skills-scratch`, which is not pushed and has no PR. Because this field is empty the issue it resolves stays `in-progress`, not `resolved` (`process.yaml: definitions.issue-status`) |

**summary.** Migrate Skills/Scratch to the Tooling/Tests versioned layout at
v1.0.0 and create the four missing canonical documents. *(A one-line gloss, not a
`change-entry` field and not the id source — the id derives from the `iteration`
field below.)*

**cause (Y).** The tool predates `PROCESS.md` (both the process document and
`process.yaml` are dated 2026-08-31, and their own §9 backlog lists
`Skills/Scratch` with `README` present and every other column absent). It was
authored as a flat directory — `README.md`, `templates/`, `tests/` at the tool
root — before the convention that a tool's code sits under `Tooling/v<version>/`
and its recorded output under `Tests/v<version>/` existed. Nothing in the tool
enforces that convention, so nothing failed loudly when it was unmet.

**outcome (X).** Skills/Scratch failed four of the five Track B checks of
PROCESS.md §7 — canonical files (four of five absent: `IMPLEMENTATIONS.md`,
`TEMPLATES.md`, `KNOWN_ISSUES.md`, `CHANGE_LOG.md`), code layout (no `Tooling/`),
test layout (no `Tests/`, therefore no recorded result for the README's "29/29"
claim), and version agreement (the README named no version, and neither of the
other two sources existed). Reciprocity was vacuous for both pairs. Under §7 a
tool in that state cannot release a new version, so the next real fix to this
tool was blocked before it started.

**iteration (Z).** Move the implementation into `Tooling/v1.0.0/`, repair the
paths the move breaks, run the suite from its new location and record the actual
output under `Tests/v1.0.0/`, create the four missing canonical documents
empty-but-valid, and state the current version in `README.md`.

**expected_result (V).** Checkably:

1. `Skills/Scratch/Tooling/v1.0.0/` contains `templates/` and `tests/`; the five
   canonical `.md` files remain at the tool root and nothing else does.
2. `bash tests/verify.sh`, run from `Tooling/v1.0.0/`, exits 0 with 29 passed and
   0 failed — the same verdict as the pre-move baseline.
3. No check silently disappears: the count stays 29, so a path break shows up as
   a failure rather than as a quietly skipped assertion.
4. `Tests/v1.0.0/` holds the verbatim output of that run.
5. All five canonical files exist at the tool root and are non-empty.
6. `README.md`, the newest `Tooling/` directory and this entry all name `v1.0.0`.

**change (W).** What changed, where, and how it was verified:

- **Moved** into `Tooling/v1.0.0/`: `templates/` (holding `scratch.gitignore`)
  and `tests/` (holding `verify.sh`). Plain `mv`; no file contents altered by the
  move itself. These two directories were the tool's entire implementation —
  there is no `bin/`, no `examples/`, no `commands/`, no `n8n/` and no
  `run-tests.sh` in this tool.
- **Left at the tool root**: `README.md` and the four documents created by this
  iteration (§3).
- **Path repaired — one, and it was the only one.** `tests/verify.sh` sets
  `PKG="$(cd "$HERE/.." && pwd)"` and used `$PKG/README.md` for the check
  "README points at the shipped template". `$PKG` is now the version directory,
  which correctly holds `templates/` but must never hold `README.md`, since §3
  keeps the canonical documents at the tool root. Added
  `TOOLROOT="$(cd "$PKG/../.." && pwd)"` and pointed that one assertion at
  `$TOOLROOT/README.md`, plus a two-line comment stating the layout the script
  now assumes. `$PKG/templates/scratch.gitignore` was left alone — `templates/`
  moved with the tests, so that path is still correct.
- **Verified by running, not by inspection.** The suite was run three times: at
  the old location before the move (29 passed, 0 failed, exit 0 — the baseline);
  from the new location before the repair, which **failed** with `grep:
  .../Tooling/v1.0.0/README.md: No such file or directory`, `FAIL · README points
  at the shipped template`, `28 passed, 1 failed`, exit `1`; and from the new
  location after the repair (29 passed, 0 failed, exit 0). The middle run is
  recorded in [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) rather than
  discarded, because it is the evidence that the fix fixed something.
- **Created**: `Tests/v1.0.0/run-tests.log` (captured stdout+stderr with the exit
  code and environment), `Tests/v1.0.0/RESULTS.md`, `IMPLEMENTATIONS.md`,
  `TEMPLATES.md`, `KNOWN_ISSUES.md`, and this file.
- **Edited**: `README.md` only — the `templates/scratch.gitignore` path in the
  "What's here" table, the self-check command at the foot of the file, and a new
  Layout line naming the current version and the two versioned directories.
  Wording and claims otherwise untouched.
- **Not created**: `run-tests.sh`. This tool has never had one and adding an
  entrypoint would be a code change inside a migration that otherwise only moves
  code. Recorded as an open point on the issue instead.

**Verification of V, item by item:** 1 ✅ (`find` of the tool root); 2 ✅ (29
passed, 0 failed, exit 0); 3 ✅ (count unchanged at 29 across the baseline and
final runs); 4 ✅ (`Tests/v1.0.0/run-tests.log` + `RESULTS.md`); 5 ✅ (all five
present and non-empty); 6 ✅ (`README.md` Layout line, `Tooling/v1.0.0/`, and the
`version` field above).
