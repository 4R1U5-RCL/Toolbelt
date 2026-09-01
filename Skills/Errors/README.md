# Errors — the grep-before-debugging findings registry

A durable, **greppable** record of every error, defect, and gotcha the project has hit — so a future
session (or a teammate, or triage tooling) can **recognize** a problem from its signature, **reuse**
the known fix, and **catch the whole class upfront** via the recorded guard. The one habit that makes
it pay off: **grep the registry before you debug.**

**Current version: `v1.0.0`.** The code (templates + tests) lives in
[`Tooling/v1.0.0/`](Tooling/v1.0.0/); recorded test results for that version live in
[`Tests/v1.0.0/`](Tests/v1.0.0/). Canonical documents: [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md),
[`TEMPLATES.md`](TEMPLATES.md), [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), [`CHANGE_LOG.md`](CHANGE_LOG.md).

Not a `/command` — a discipline plus a fixed entry format, like **[Memory](../Memory/)**. Where Memory
holds durable *facts*, this registry holds durable *failures*.

## What's here

| Path | Installs to | Role |
|------|-------------|------|
| `Tooling/v1.0.0/templates/ERRORS_AND_FINDINGS.md.template` | repo root | The **hub**: purpose/how-to block, the per-area Index, Part 1 (recurring `PAT-*` classes), Part 3 (open-items rollup). |
| `Tooling/v1.0.0/templates/errors-area.md.template` | `errors/<area>.md` | A **per-area** incident catalog skeleton. |
| `Tooling/v1.0.0/templates/incident-entry.md.template` | (snippet) | The atomic **single-incident** entry format. |

The templates ship **pre-seeded with a portable generic `PAT-*` taxonomy** and **correct the drift
traps** the live system exhibits (see Known issues).

## Architecture

Two tiers:

- **Hub — `ERRORS_AND_FINDINGS.md`** (repo root): the Index of area files, **Part 1** (cross-area
  recurring failure classes, `PAT-*`), and **Part 3** (the open-items rollup). *(There is
  intentionally no Part 2 — the per-incident detail is externalized to the area files.)*
- **Per-area catalogs — `errors/<area>.md`**: the concrete incidents, one short prefix per area
  (e.g. `HC-*` harness, `IN-*` infra, `TE-*` a client). Grouped by topic/stage, appended within the
  section.

`PAT-*` classes cite their member incident IDs; incidents cite back up (`see PAT-3`) — a two-way index
between hub and catalogs.

## The entry format (the greppability contract)

Every incident is one entry; the **Signature leads** and must be an actual error string or observable
behavior — that's what makes the file greppable *and* machine-matchable:

```markdown
## AA-N — <title>
- **Signature:** <verbatim error string / observable behavior>
- **Cause:** <root cause>
- **Fix:** <the change that resolved it>
- **Guard:** <the check that catches the whole class — or `see PAT-N`>
- **Status:** OPEN | FIXED <date/PR>
- **Source:** <git SHA | work-unit slug>
```

A **`PAT-*`** class is shaped differently — it *aggregates* incidents, so it's Title + prose +
Watch-for/Signature + Guard (no Cause/Fix/Source), and lists its member IDs inline.

## The discipline

1. **Grep first.** Hit an error → grep the hub + `errors/*.md` for the string or symptom **before
   debugging**. Most are already here with a fix.
2. **Skim Part 1 before any build / deploy / migration** — the classes that recur.
3. **Add findings in place.** Append a new incident to the **bottom of the matching topical section**
   of the right `errors/<area>.md` (not global newest-first, not strictly numeric).
4. **Mint a `PAT-*` only when a failure has bitten more than once, across more than one area** — then
   cite its member incidents inline instead of duplicating them.
5. **IDs are immutable.** Monotonic per prefix, assigned at add-time, **never reused, never
   renumbered** — other docs and triage tooling cite them by plain-text ID, so a renumber silently
   breaks those references.
6. **Status vocabulary:** `FIXED` (resolved in code/config) / `OPEN` (unresolved → also rolled into
   Part 3). `Source:` is a git SHA or a work-unit / handoff slug.

## Why (the charter)

This registry *is* the seed-knowledge-infra rule (the live system codifies it as its own `PAT`
class): a project scaffolded **without** its knowledge-infra runs its most error-prone phase blind,
and retrofitting costs more than seeding. So a new project should ship, from day one, **this hub +
per-area files + a triage stub + a state-doc skeleton + a `MEMORY.md` + an SOP index**, pre-seeded
with the portable `PAT-*` taxonomy. The payoff compounds because the file is **machine-consumed**
too — verify/triage tooling matches failed checks against the registry to surface the known fix —
which is exactly why *signature-first* and *stable IDs* are load-bearing, not cosmetic.

## How it fits the system

- **[Memory](../Memory/)** holds durable facts; this registry holds durable failures — complementary
  halves of the project's long-term knowledge.
- **[Handoff](../Handoff/)** feeds it: a gotcha discovered mid-session is appended here as an incident
  (and promoted to a `PAT-*` if it's a repeat) rather than dying with the session.
- **[Scratch](../Scratch/)** is the counter-rule for secrets: a `PAT`-guarded "never leak a secret"
  incident points at the scratch `.gitignore` discipline.

## Known issues / caveats

*(Issues with **this tool** are tracked in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). The list below is
about the **live registry this tool was distilled from**; the shipped templates correct the first
three and standardize the fourth.)*

*(The live registry exhibits these; the shipped templates correct the first three and standardize the
fourth.)*

1. **Numbering has no enforcement → duplicate IDs happen.** The live `infra.md` reuses `IN-38` twice.
   **Add-time check:** grep the prefix for the highest number in use before assigning; never trust a
   plain count.
2. **Hardcoded `PAT` ranges in headers drift.** Area headers that say "PAT-1…10" go stale the moment
   the hub adds PAT-11. The template writes **`PAT-*`** instead — keep it that way.
3. **The `Last compiled:` stamp goes stale on appends.** It means *last full rebuild*, not last edit;
   the template labels it as such.
4. **Two entry styles fragment grep.** The live `infra.md` mixes a compact `**IN-N**` bullet style and
   a `## IN-N` header style — `grep '^\*\*IN-'` misses half of it. The template standardizes on the
   `## AA-N` header style; **`grep -E 'AA-[0-9]+'` is the reliable locator** regardless of style.
5. **Open items live in two places.** Each `OPEN` item sits in both the hub's Part 3 and its area
   file's Open-items section — update both on a status change, or FIXED-here / OPEN-there drift hides.
6. **Beware foreign ID namespaces.** The live system also cites a separate `BUG-NN` n8n-workflow
   tracker inside entries; it is **not** part of this registry. Don't conflate external trackers with
   the `PAT/AA` IDs.

## Adapting it

The IDs and area names here (`HC-*` harness, `IN-*` infra, `/studio/...`) are the **studio's**
instance — pick your own short per-area prefixes and paths. What transfers is the two-tier shape and
the signature-first entry format.

## Quickstart — one incident's lifecycle

```sh
# 1. hit an error → GREP the registry FIRST (hub + area files)
grep -rn "ECONNREFUSED" ERRORS_AND_FINDINGS.md errors/

# 2. not found? copy Tooling/v1.0.0/templates/incident-entry.md.template to the bottom of the
#    matching topical section in errors/<area>.md — Signature line FIRST

# 3. close the loop: Status: FIXED <sha>, and add a Guard so the class can't recur

# 4. if it has now bitten twice across areas, mint a PAT-* in the hub and list
#    this incident as a member
```

Lifecycle: **grep → (miss) → add entry (signature-first) → fix + guard → mark FIXED → promote to a
`PAT-*` on the second occurrence.**

## Provenance

Mirrors the live studio registry: `/studio/ERRORS_AND_FINDINGS.md` (hub, `PAT-1…15`) + `errors/*.md`
(`HC-*` harness, `IN-*` infra, `TE-*`/`MO-*`/`EL-*` clients), wired into `harness/triage.ts` for
verify-time known-fix matching. The templates here are the generic, drift-corrected distillation of
that system.


**Committed self-check:** from `Tooling/v1.0.0/`, run `bash tests/verify.sh` — **32/32**, exit 0, last run 2026-09-01 and recorded verbatim at [`Tests/v1.0.0/verify.log`](Tests/v1.0.0/verify.log). There is no `run-tests.sh` in this tool; `tests/verify.sh` is the whole suite. It checks the template structure and the drift-fixes, then on a fixture registry verifies signature greppability, the compact-grep-vs-`ID-[0-9]+` fragmentation caveat (live), index↔catalog consistency, and a duplicate-ID guard that reproduces the live `IN-38` bug.
