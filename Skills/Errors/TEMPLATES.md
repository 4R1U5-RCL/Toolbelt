# Templates — Skills/Errors

The production application forms shipped by this tool. All three live in
[`Tooling/v1.0.0/templates/`](Tooling/v1.0.0/templates/) and are the *only* files this
tool ships besides its self-check; the tool has no runtime code and no `bin/`.

Each entry names the file, where an installed copy lands, what it contains, and which
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) entries use it.

| id | File | Installs to |
|---|---|---|
| [`TPL-hub`](#tpl-hub) | `templates/ERRORS_AND_FINDINGS.md.template` | repo root, as `ERRORS_AND_FINDINGS.md` |
| [`TPL-area`](#tpl-area) | `templates/errors-area.md.template` | `errors/<area>.md` |
| [`TPL-entry`](#tpl-entry) | `templates/incident-entry.md.template` | snippet — pasted into an `errors/<area>.md` section |

---

<a name="tpl-hub"></a>
## `TPL-hub` — the registry hub

**File:** `Tooling/v1.0.0/templates/ERRORS_AND_FINDINGS.md.template` (83 lines).

Contains, verbatim in the shipped file:

- A **Purpose** blockquote and a **How to use this file** block whose first instruction is
  to grep the hub plus `errors/*.md` before debugging.
- A **Layout note** stating that per-incident detail is externalized to `errors/<area>.md`
  and that there is intentionally **no Part 2**.
- A `_Last full rebuild: <YYYY-MM-DD>._` stamp, explicitly labelled as the last full
  recompile rather than the last edit.
- **`## Index — per-area catalogs`** — a four-column table (Area / File / Scope / IDs) with
  two placeholder rows.
- **`## Part 1 — Recurring Failure Classes`**, pre-seeded with three portable classes:
  `PAT-1` (empty HTTP-200 body → `res.json()` throws), `PAT-2` (secret leaked into a URL,
  log line, or commit), `PAT-3` (knowledge-infra not seeded at scaffold).
- **`## Part 3 — Open Items`** — three priority buckets (Security/critical,
  Blocked/functional, Hardening/lower priority), each `_(none yet)_`.

Placeholders to fill: `<Project>`, `<YYYY-MM-DD>`, the Index rows and their ID prefixes.

**Used by:** [`IMP-scaffold`](IMPLEMENTATIONS.md#imp-scaffold),
[`IMP-promote`](IMPLEMENTATIONS.md#imp-promote),
[`IMP-selfcheck`](IMPLEMENTATIONS.md#imp-selfcheck).

---

<a name="tpl-area"></a>
## `TPL-area` — a per-area incident catalog

**File:** `Tooling/v1.0.0/templates/errors-area.md.template` (37 lines).

Contains:

- A header `# Errors & Findings — <Area>` and a blockquote binding the file back to
  `../ERRORS_AND_FINDINGS.md`, restating the entry format
  (**ID — Title · Signature · Cause · Fix · Guard · Status · Source**).
- An HTML comment carrying the ID rules: short stable unique prefix, monotonic per prefix,
  never reused, immutable once minted, appended to the **bottom of the matching topical
  section**, and "before assigning a number, grep the prefix for the highest in use".
- Two topical-section placeholders (`## <Topic / stage one>`, `## <Topic / stage two>`) with
  one worked `## AA-1` entry showing all six fields.
- An **`## Open items (this component)`** section, kept in sync with the hub's Part 3.

Placeholders to fill: `<Area>`, the topic headings, and the ID prefix (`AA-*`).

**Used by:** [`IMP-scaffold`](IMPLEMENTATIONS.md#imp-scaffold),
[`IMP-selfcheck`](IMPLEMENTATIONS.md#imp-selfcheck).

---

<a name="tpl-entry"></a>
## `TPL-entry` — one incident

**File:** `Tooling/v1.0.0/templates/incident-entry.md.template` (18 lines).

A snippet, not a whole file. An `## AA-N — <short, specific title>` heading followed by six
bullets in fixed order — **Signature**, **Cause**, **Fix**, **Guard**, **Status**,
**Source** — with the Signature first because that is what makes the registry greppable and
machine-matchable. Leading and trailing HTML comments state the canonical format, where the
finished entry is appended, and that a failure which has now bitten across more than one
area should also be minted as a `PAT-*` in the hub.

**Used by:** [`IMP-incident`](IMPLEMENTATIONS.md#imp-incident),
[`IMP-selfcheck`](IMPLEMENTATIONS.md#imp-selfcheck).
