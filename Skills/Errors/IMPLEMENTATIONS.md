# Implementations — Skills/Errors

How this tool is actually used. Every entry below is derived from
[`README.md`](README.md) and from the shipped files in
[`Tooling/v1.0.0/`](Tooling/v1.0.0/) — nothing here describes a use the repo does not
support. Each entry links to the template it applies in
[`TEMPLATES.md`](TEMPLATES.md).

The tool is a **discipline plus a fixed entry format**, not a `/command`: it ships three
markdown templates and a self-check script. There is no `bin/`, no `examples/`, and no
config file in this directory, so every implementation below is "install the template,
then follow the discipline".

| id | Use case | Template |
|---|---|---|
| [`IMP-scaffold`](#imp-scaffold) | Seed a project's registry at scaffold time | [`TPL-hub`](TEMPLATES.md#tpl-hub), [`TPL-area`](TEMPLATES.md#tpl-area) |
| [`IMP-incident`](#imp-incident) | Record one incident mid-session | [`TPL-entry`](TEMPLATES.md#tpl-entry) |
| [`IMP-promote`](#imp-promote) | Promote a repeat failure to a `PAT-*` class | [`TPL-hub`](TEMPLATES.md#tpl-hub) |
| [`IMP-selfcheck`](#imp-selfcheck) | Verify the shipped package before adopting it | all three |

---

<a name="imp-scaffold"></a>
## `IMP-scaffold` — seed a new project's registry

**When.** At project scaffold, before the first error-prone phase. The README calls this
the tool's charter: a project scaffolded without its knowledge-infra runs blind, and
retrofitting costs more than seeding (the same argument the shipped `PAT-3` class states).

**Do.**

1. Copy [`TPL-hub`](TEMPLATES.md#tpl-hub) to the repo root as `ERRORS_AND_FINDINGS.md`;
   fill `<Project>` and the `Last full rebuild` date.
2. For each area, copy [`TPL-area`](TEMPLATES.md#tpl-area) to `errors/<area>.md` and choose
   a short, stable, unique ID prefix (the README's live instance uses `HC-*` harness,
   `IN-*` infra, `TE-*`/`MO-*`/`EL-*` clients — those are that instance's names, not
   defaults to copy).
3. Add one Index row in the hub per area file. Keep the seeded `PAT-1`/`PAT-2`/`PAT-3`
   classes that apply; add project-specific ones later.

**Result.** The two-tier shape: hub (Index + Part 1 + Part 3) over per-area catalogs.

**Templates:** [`TPL-hub`](TEMPLATES.md#tpl-hub), [`TPL-area`](TEMPLATES.md#tpl-area).

---

<a name="imp-incident"></a>
## `IMP-incident` — record one incident

**When.** A session hits an error, defect or gotcha.

**Do** (the README's quickstart lifecycle, verbatim in intent):

1. **Grep first** — `grep -rn "<error string>" ERRORS_AND_FINDINGS.md errors/`. Most are
   already recorded with a fix.
2. On a miss, copy [`TPL-entry`](TEMPLATES.md#tpl-entry) to the **bottom of the matching
   topical section** of the right `errors/<area>.md`. The Signature line leads and must be
   a verbatim error string or an observable behavior.
3. Assign the next ID for that prefix — after grepping the prefix for the highest number
   in use, never from a plain count (the README records the live `IN-38` duplicate as the
   reason).
4. Close the loop: `Status: FIXED <sha>` plus a **Guard** that catches the whole class.
5. If the item is `OPEN`, mirror it into **both** the area file's Open-items section and
   the hub's Part 3.

**Templates:** [`TPL-entry`](TEMPLATES.md#tpl-entry).

---

<a name="imp-promote"></a>
## `IMP-promote` — mint a `PAT-*` class

**When.** A failure has bitten **more than once, across more than one area** — the README's
explicit threshold.

**Do.** Add a `### PAT-N — <title>` block to the hub's Part 1 in the aggregate shape:
title, prose, Watch-for/Signature, Guard — no Cause/Fix/Source — listing its member
incident IDs inline. The member incidents cite back up (`see PAT-N`), giving the two-way
index between hub and catalogs.

**Templates:** [`TPL-hub`](TEMPLATES.md#tpl-hub) (its Part 1 section and seeded classes are
the shape to copy).

---

<a name="imp-selfcheck"></a>
## `IMP-selfcheck` — verify the package

**When.** Before adopting the templates, and after any change to them.

**Do.** `bash Tooling/v1.0.0/tests/verify.sh` from anywhere — the script resolves its own
directory via `BASH_SOURCE` and reads the templates from `$HERE/..`, so it does not depend
on the working directory.

**What it checks** (32 assertions): the three templates exist and are non-empty; the hub's
grep-first block, Index, Part 1, Part 3, absence of a Part 2, seeded `PAT-1/2/3`, and the
two hub drift-fixes; the area template's hub binding, entry format, Open-items section and
its two drift-fixes; all six incident fields with Signature first; that no template uses
the compact `**XX-N` style. It then builds a fixture registry in a temp dir and checks
signature greppability, the compact-grep-vs-`ID-[0-9]+` fragmentation caveat,
index↔catalog consistency including a deliberately dangling row, and a duplicate-ID guard
reproducing the live `IN-38` bug.

Recorded output for the current version: [`Tests/v1.0.0/`](Tests/v1.0.0/).

**Templates:** all three — [`TPL-hub`](TEMPLATES.md#tpl-hub),
[`TPL-area`](TEMPLATES.md#tpl-area), [`TPL-entry`](TEMPLATES.md#tpl-entry).
