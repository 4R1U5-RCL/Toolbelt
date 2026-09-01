# Templates — Skills/Memory v1.0.0

The production application forms this tool ships. Both are real files under
`Tooling/v1.0.0/templates/`, shipped verbatim from the live system, and both are
installed to `~/.claude/data/templates/`. Nothing else in this tool is a
template: there are no command files, no n8n workflows and no config forms.

Each entry names the implementation in [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md)
that applies it. Entries are delimited by a level-2 heading whose text is the
bare id (`process.yaml: definitions.entry`), and no other line in this file
begins with `## ` at column 0. Quoted template content that carries its own
`## ` lines is shown as an indented code block rather than a fenced one, for
exactly that reason — a fence does not stop a line-based entry scanner.

**Coverage.** Two templates, both present and both exercised by
`Tooling/v1.0.0/tests/verify.sh` (18/18 — see [`Tests/v1.0.0/`](Tests/v1.0.0/)).
No template exists for the *discipline* half of this tool (dedup-first,
index-in-the-same-change, promotion out of a handoff): that is prose in
`README.md`, not a form, and no file in this tool encodes it.

---

## memory-md-template

**`MEMORY.md.template` — the index skeleton**

**File:** `Tooling/v1.0.0/templates/MEMORY.md.template`
**Installs to:** `~/.claude/data/templates/MEMORY.md.template`
**Applied by:** [IMPLEMENTATIONS.md#new-memory-directory](IMPLEMENTATIONS.md#new-memory-directory),
[IMPLEMENTATIONS.md#drift-check](IMPLEMENTATIONS.md#drift-check)

A blank `MEMORY.md` for a new memory directory. Its contents, indented four
spaces for display — the file on disk has no indent, but four of its lines begin
with `## `, and a line beginning `## ` at column 0 in *this* document is an entry
heading (PROCESS.md §10 decision 13) whatever it is nested inside:

    # Memory Index

    <!-- One line per memory file. Format: - [Title](file.md) — one-line hook (under ~150 chars) -->
    <!-- Types: user | feedback | project | reference -->

    ## User
    <!-- Who the user is, their role, expertise, preferences -->

    ## Feedback
    <!-- How Claude should behave in this project — corrections and confirmed approaches -->

    ## Project
    <!-- Ongoing work, decisions, deadlines, goals -->

    ## Reference
    <!-- Pointers to external systems, dashboards, docs, channels -->

What it fixes:

- **Four sections**, one per memory type, in the order `User`, `Feedback`,
  `Project`, `Reference`.
- **No frontmatter.** The index carries none — the linter treats a leading `---`
  as a defect (`INDEX_HAS_FRONTMATTER`).
- **One row per file**, shaped `- [Title](file.md) — one-line hook`. The
  separator is an em dash; the linter's row check
  (`INDEX_ROWS_MALFORMED`) rejects anything else.
- The README's ~200-line ceiling applies to the file this template seeds
  (`MAXLEN_OK`).

---

## memory-entry-md-template

**`memory-entry.md.template` — one fact, one file**

**File:** `Tooling/v1.0.0/templates/memory-entry.md.template`
**Installs to:** `~/.claude/data/templates/memory-entry.md.template`
**Applied by:** [IMPLEMENTATIONS.md#record-a-memory](IMPLEMENTATIONS.md#record-a-memory),
[IMPLEMENTATIONS.md#drift-check](IMPLEMENTATIONS.md#drift-check)

A single memory file with the correct frontmatter. Verbatim contents:

```markdown
---
name: {{short-kebab-case-slug}}
description: {{one-line summary — used to decide relevance in future conversations}}
metadata:
  type: {{user | feedback | project | reference}}
---

{{Memory content.}}

<!-- For feedback/project types, use this structure: -->
<!-- Lead with the rule or fact. -->
<!-- **Why:** The reason or motivation behind it. -->
<!-- **How to apply:** When/where this kicks in. -->
<!-- Link related memories with [[their-name]]. -->
```

What it fixes:

- The three required frontmatter keys: `name`, `description`, `metadata.type`.
- `type` is an enum: `user | feedback | project | reference`.
- `name` must equal the file stem — the linter fails an entry where it does not.
- The `{{…}}` placeholders are fill points; the `<!-- … -->` lines are guidance
  and are dropped when the template is cut (see `mem_tool.py build`).
