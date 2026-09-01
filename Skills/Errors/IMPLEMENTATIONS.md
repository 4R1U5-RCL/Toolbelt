# Implementations — Skills/Errors

How this tool is actually used. Every entry below is derived from
[`README.md`](README.md) and from the shipped files in
[`Tooling/v1.0.0/`](Tooling/v1.0.0/) — nothing here describes a use the repo does not
support. Each entry links to the template it applies in
[`TEMPLATES.md`](TEMPLATES.md), and every template there links back — the §7 Track B
reciprocity pair.

An entry is delimited by a level-2 heading whose text is the bare entry id — no backticks,
no title, nothing else on the line (`process.yaml: definitions.entry`). The heading text is
the anchor an `IMPLEMENTATIONS.md#<id>` citation resolves against.

The tool is a **discipline plus a fixed entry format**, not a `/command`: it ships three
markdown templates and a self-check script. There is no `bin/`, no `examples/`, and no
config file in this directory, so every implementation below is "install the template,
then follow the discipline".

| id | Use case | Template |
|---|---|---|
| [`imp-scaffold`](#imp-scaffold) | Seed a project's registry at scaffold time | [`tpl-hub`](TEMPLATES.md#tpl-hub), [`tpl-area`](TEMPLATES.md#tpl-area) |
| [`imp-incident`](#imp-incident) | Record one incident mid-session | [`tpl-entry`](TEMPLATES.md#tpl-entry) |
| [`imp-promote`](#imp-promote) | Promote a repeat failure to a `PAT-*` class | [`tpl-hub`](TEMPLATES.md#tpl-hub) |
| [`imp-selfcheck`](#imp-selfcheck) | Verify the shipped package before adopting it | all three |

---

## imp-scaffold

**Seed a new project's registry**

**When.** At project scaffold, before the first error-prone phase. The README calls this
the tool's charter: a project scaffolded without its knowledge-infra runs blind, and
retrofitting costs more than seeding (the same argument the shipped `PAT-3` class states).

**Do.**

1. Copy [`tpl-hub`](TEMPLATES.md#tpl-hub) to the repo root as `ERRORS_AND_FINDINGS.md`;
   fill `<Project>` and the `Last full rebuild` date.
2. For each area, copy [`tpl-area`](TEMPLATES.md#tpl-area) to `errors/<area>.md` and choose
   a short, stable, unique ID prefix (the README's live instance uses `HC-*` harness,
   `IN-*` infra, `TE-*`/`MO-*`/`EL-*` clients — those are that instance's names, not
   defaults to copy).
3. Add one Index row in the hub per area file. Keep the seeded `PAT-1`/`PAT-2`/`PAT-3`
   classes that apply; add project-specific ones later.

**Result.** The two-tier shape: hub (Index + Part 1 + Part 3) over per-area catalogs.

**Templates:** [`tpl-hub`](TEMPLATES.md#tpl-hub), [`tpl-area`](TEMPLATES.md#tpl-area).

---

## imp-incident

**Record one incident**

**When.** A session hits an error, defect or gotcha.

**Do** (the README's quickstart lifecycle, verbatim in intent):

1. **Grep first** — `grep -rn "<error string>" ERRORS_AND_FINDINGS.md errors/`. Most are
   already recorded with a fix.
2. On a miss, copy [`tpl-entry`](TEMPLATES.md#tpl-entry) to the **bottom of the matching
   topical section** of the right `errors/<area>.md`. The Signature line leads and must be
   a verbatim error string or an observable behavior.
3. Assign the next ID for that prefix — after grepping the prefix for the highest number
   in use, never from a plain count (the README records the live `IN-38` duplicate as the
   reason).
4. Close the loop: `Status: FIXED <sha>` plus a **Guard** that catches the whole class.
5. If the item is `OPEN`, mirror it into **both** the area file's Open-items section and
   the hub's Part 3.

**Templates:** [`tpl-entry`](TEMPLATES.md#tpl-entry).

---

## imp-promote

**Mint a `PAT-*` class**

**When.** A failure has bitten **more than once, across more than one area** — the README's
explicit threshold.

**Do.** Add a `### PAT-N — <title>` block to the hub's Part 1 in the aggregate shape:
title, prose, Watch-for/Signature, Guard — no Cause/Fix/Source — listing its member
incident IDs inline. The member incidents cite back up (`see PAT-N`), giving the two-way
index between hub and catalogs.

**Templates:** [`tpl-hub`](TEMPLATES.md#tpl-hub) (its Part 1 section and seeded classes are
the shape to copy).

---

## imp-selfcheck

**Verify the package**

**When.** Before adopting the templates, and after any change to them.

**Do.** From `Tooling/v1.0.0/`, run `bash tests/verify.sh`. **There is no `run-tests.sh`**
in this tool — `tests/verify.sh` is the whole suite. It can in fact be invoked from any
working directory: the script resolves its own location via `BASH_SOURCE` and reads the
templates from `$HERE/..`, so it does not depend on where it is called from.

**What it checks** (32 assertions): the three templates exist and are non-empty; the hub's
grep-first block, Index, Part 1, Part 3, absence of a Part 2, seeded `PAT-1/2/3`, and the
two hub drift-fixes; the area template's hub binding, entry format, Open-items section and
its two drift-fixes; all six incident fields with Signature first; that no template uses
the compact `**XX-N` style. It then builds a fixture registry in a temp dir and checks
signature greppability, the compact-grep-vs-`ID-[0-9]+` fragmentation caveat,
index↔catalog consistency including a deliberately dangling row, and a duplicate-ID guard
reproducing the live `IN-38` bug.

Recorded output for the current version: [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md)
and the verbatim log [`Tests/v1.0.0/verify.log`](Tests/v1.0.0/verify.log) — 32 passed, 0
failed, exit 0, last run 2026-09-01.

**Templates:** all three — [`tpl-hub`](TEMPLATES.md#tpl-hub),
[`tpl-area`](TEMPLATES.md#tpl-area), [`tpl-entry`](TEMPLATES.md#tpl-entry).
