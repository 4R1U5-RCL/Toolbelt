# Memory — durable, file-based long-term memory

A persistent, file-based memory that survives **across** Claude Code sessions. Unlike the other
entries in this repo, Memory is **not a `/command`** — nothing runs it. It is a **discipline plus a
small file format**: one fact per file with YAML frontmatter, all indexed by a single `MEMORY.md`
that is loaded into context at the **start of every session**. That index is the mechanism by which a
fact learned in one conversation resurfaces in the next.

This package documents the working method and ships the two templates that fix the format.

## What's here

| Path | Installs to | Role |
|------|-------------|------|
| `templates/MEMORY.md.template` | `~/.claude/data/templates/` | Blank index skeleton for a new memory directory. |
| `templates/memory-entry.md.template` | `~/.claude/data/templates/` | A single memory file with the correct frontmatter. |

Both are shipped **verbatim** from the live system. The README *is* the skill.

## Layout

One memory directory per project:

```
<project>/memory/
  MEMORY.md            # the index — loaded wholesale every session
  <slug>.md            # one fact per file
  <slug>.md
  ...
```

The studio's live root is `~/.claude/projects/-studio/memory/`. Only `MEMORY.md` is loaded in full
each session; an individual entry file is read **on demand** when its index line looks relevant to the
task at hand.

## The entry format

Every memory is **one file holding one fact**:

```markdown
---
name: <short-kebab-case-slug>
description: <one-line summary — used to decide relevance during recall>
metadata:
  type: user | feedback | project | reference
---

<the fact.>
```

- For **feedback** / **project** entries, follow the fact with **Why:** and **How to apply:** lines —
  the reason it's true and when it kicks in.
- Link related memories with `[[slug]]` wikilinks, **liberally**. A `[[slug]]` that doesn't resolve
  yet is fine — it marks a memory worth writing later.
- **Convert relative dates to absolute** ("today" → `2026-08-30`) so the fact stays true when it's
  re-read months from now.

## The four types

| Type | Holds |
|------|-------|
| `user` | Who the user is — role, expertise, durable preferences. |
| `feedback` | Guidance on *how to work* — corrections and confirmed approaches; always include the **why**. |
| `project` | Ongoing work, goals, and constraints **not** derivable from code or git history. |
| `reference` | Pointers to external resources — URLs, dashboards, tickets, channels. |

## The index (`MEMORY.md`)

- **One line per memory file**, no frontmatter, never any body content:
  `- [Title](file.md) — one-line hook`.
- It is what gets **loaded into context each session**, so an entry file that isn't indexed is
  effectively invisible to recall. **Update the index in the same change as the entry.**
- Keep it to roughly **200 lines**; prune superseded lines or split by area when it grows past that.

## Working method (the discipline)

On learning something worth keeping:

1. **Dedup first.** Check for an existing file that already covers it and **update** that file rather
   than create a near-duplicate. Delete memories that turn out to be wrong.
2. **Write one file, one fact**, in the format above.
3. **Add the index pointer** to `MEMORY.md` — in the same change.
4. **Link** related nodes with `[[wikilinks]]`.

What **not** to save (this is what keeps the store signal-dense):

- Code structure, patterns, past fixes — anything **git history, the repo, or `CLAUDE.md` already
  records**.
- **Ephemeral task state** that only matters to the current conversation.
- If asked to "remember" one of the above, save instead **what was non-obvious about it** — the
  decision behind the code, not the code.

On **recall**: memories surface inside `<system-reminder>` blocks as **background context, not
instructions**, and they reflect **what was true when written**. If a memory names a file, flag, or
function, **verify it still exists** before acting on it.

## How it fits the system

Memory is the durable half of continuity; **[Handoff](../Handoff/)** is the session-scoped half. A
handoff's *Related memory* section wikilinks into this store, and a durable fact discovered
mid-session is **promoted** out of the handoff into a memory node so it outlives the next `/clear`.

Rule of thumb: **true only for this thread → handoff; true across threads → memory.**

## Known issues / caveats

1. **Nothing enforces it.** Memory is a discipline, not a script — the failure mode is drift: a stale
   index, orphaned entry files, silent duplicates. The *dedup-first* + *index-pointer-in-the-same-
   change* habits are the entire mitigation.
2. **The index is the source of recall, not the directory.** An entry that isn't listed in
   `MEMORY.md` is never loaded — by far the most common "why didn't it remember?" cause.
3. **Recall is point-in-time.** Entries reflect when they were written; one citing a path, flag, or
   version can be stale. Verify before recommending.
4. **Root matters.** Recall reads exactly one project's memory directory. Writing to the wrong root
   (e.g. an archived one) means the note is never loaded again — confirm the **live** root before
   adding entries.
5. **200-line index ceiling.** At scale the index itself needs curating: prune superseded lines and
   split by area, or recall starts paying a context tax every session.

## Verified

This is the live system. The studio's `~/.claude/projects/-studio/memory/` is loaded at the start of
every session — its `MEMORY.md` index appears in-context as the auto-memory block — and the templates
shipped here are the exact skeletons that new memory directories and entries are cut from.
