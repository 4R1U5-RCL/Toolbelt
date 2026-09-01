# Templates — Skills/Handoff

The production-ready application forms this tool ships. Both are copied
**verbatim** into a live `~/.claude/` at install time; neither is generated.

Current version: **v1.0.0** — the files below live under
`Tooling/v1.0.0/`.

| id | File in the package | Installs to |
|---|---|---|
| [`TMPL-01`](#tmpl-01) | `Tooling/v1.0.0/templates/handoff-template.md` | `~/.claude/data/templates/handoff-template.md` |
| [`TMPL-02`](#tmpl-02) | `Tooling/v1.0.0/commands/handoff.md` | `~/.claude/commands/handoff.md` |

---

<a name="tmpl-01"></a>
## `TMPL-01` — `handoff-template.md`, the handoff document form

**Used by** [`IMPL-01`](IMPLEMENTATIONS.md#impl-01),
[`IMPL-02`](IMPLEMENTATIONS.md#impl-02),
[`IMPL-03`](IMPLEMENTATIONS.md#impl-03),
[`IMPL-04`](IMPLEMENTATIONS.md#impl-04).

The fixed structure every handoff fills. It is the only file in the package's
`templates/` directory.

**Frontmatter** — three keys:

```
---
topic: {{topic}}
session_scope: {{full | since-<prior-filename>}}
created: {{YYYY-MM-DDTHH-MMZ}}
---
```

**Sections** — seven `## ` headers, in this order, each carrying an HTML-comment
instruction rather than prose:

1. `## What was accomplished` — completed work, decisions and why, issues hit
   and how resolved, operational gotchas. Explicitly *omits* abandoned
   approaches, superseded plans and raw tool output.
2. `## Current state` — one paragraph: done / not done / partially done.
3. `## Open questions` — one bullet per unresolved item; `None.` if empty.
4. `## Immediate next steps` — numbered, confirmed, ordered actions.
5. `## Environment facts` — runtime facts not derivable from the repo or config.
6. `## Related memory` — `- [[node-name]]` wikilinks; `None.` if empty.
7. `## Pruned from this handoff` — one or two lines on what was dropped and why.

Sections are separated by `---` rules.

**This form is load-bearing, not decorative.** `TMPL-02` step 3 aborts if this
file is missing or empty (fail-closed), and `Tooling/v1.0.0/tests/verify.sh`
asserts that every `## ` header in this file appears in a generated document.

---

<a name="tmpl-02"></a>
## `TMPL-02` — `commands/handoff.md`, the `/handoff` slash command

**Used by** [`IMPL-01`](IMPLEMENTATIONS.md#impl-01),
[`IMPL-02`](IMPLEMENTATIONS.md#impl-02),
[`IMPL-03`](IMPLEMENTATIONS.md#impl-03).

The procedure itself, as an installable Claude Code command file. It lives in
the package's `commands/` directory, **not** in `templates/` — it is listed here
because it is a shipped production form installed verbatim, and because
`IMPLEMENTATIONS.md` entries need something to cite.

Frontmatter it declares:

```
description:   Compile the current session into a handoff document (state, decisions,
               open tasks, next steps) and save it to ~/.claude/data/handoffs/ using
               the handoff template
argument-hint: [<topic-slug>]
allowed-tools: [Read, Write, Bash]
```

Seven-step body: 1 determine topic → 2 determine scope (the 4h rule) → 3 load
the template, fail-closed → 4 load the memory index
(`~/.claude/projects/-studio/memory/MEMORY.md`) → 5 compile, curating → 6
generate the UTC filename and write → 7 report back.

**Fixed strings the command hard-codes** (see `KNOWN_ISSUES.md`):
`~/.claude/data/handoffs/`, `~/.claude/data/templates/handoff-template.md`,
`~/.claude/projects/-studio/memory/MEMORY.md`, the 4-hour threshold, and the
output filename form `handoff_<topic>_<YYYY-MM-DDTHH-MM>.md` (UTC).
