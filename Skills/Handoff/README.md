# Handoff — session → durable handoff document

`/handoff` compiles the current Claude Code session into a single, curated **handoff document** — what
was accomplished, current state, open questions, concrete next steps, environment facts, and the
load-bearing memory nodes — and writes it to `~/.claude/data/handoffs/` under a timestamped,
topic-slugged filename. It is the clean seam between sessions: run it before `/clear` or `/compact`,
and the next session (or a collaborator) orients from the document alone instead of re-reading a
transcript.

Invoked by the `/handoff` slash command (optionally `/handoff <topic-slug>`).

## What's here

| Path | Installs to | Role |
|------|-------------|------|
| `commands/handoff.md` | `~/.claude/commands/handoff.md` | The `/handoff` slash command — the procedure itself. |
| `templates/handoff-template.md` | `~/.claude/data/templates/handoff-template.md` | The fixed section structure every handoff fills. |

Both are shipped **verbatim** from the live system — this package is a faithful mirror, not a
re-implementation.

## Install

```sh
cp commands/handoff.md            ~/.claude/commands/
mkdir -p ~/.claude/data/handoffs ~/.claude/data/templates
cp templates/handoff-template.md  ~/.claude/data/templates/
```

The skill writes into `~/.claude/data/handoffs/` — create it once (above) so the first run has a home.

## How it works

1. **Topic** — from the `<topic-slug>` argument, else inferred from the session's dominant subject
   (kebab-case); it asks only when genuinely ambiguous.
2. **Scope (the 4-hour rule)** — if the most-recent handoff is **< 4h old**, scope is *incremental*
   (only what changed since; frontmatter records `since-<prior-file>`); otherwise *full session*. This
   keeps a chain of related handoffs lean instead of re-stating everything each time.
3. **Template-driven** — reads `handoff-template.md` and fills every section; **fail-closed** if the
   template is missing or empty (a handoff without the agreed structure is worse than none).
4. **Memory-linked** — reads the project memory index and lists the load-bearing nodes as
   `[[wikilinks]]` under *Related memory*, tying the session back to the durable store.
5. **Curated, not dumped** — decisions, state, and gotchas in; abandoned approaches, superseded plans,
   and raw tool output out. A *Pruned* line records what was deliberately dropped so a later session
   doesn't try to re-derive it.
6. **Written** to `~/.claude/data/handoffs/handoff_<topic>_<YYYY-MM-DDTHH-MM>.md` (UTC). It writes
   **only** there — never touches memory, plans, or templates.

## How it fits the system

Handoff and **[Memory](../Memory/)** are the two complementary halves of continuity:

- **Handoff** is *session-scoped* — "what happened here and what's next," written once, read by the
  next session, then it ages out.
- **Memory** is *durable* — facts that outlive any single session. A handoff's *Related memory*
  section wikilinks into that store, and a fact discovered mid-session gets **promoted** out of the
  handoff into a memory node so it survives beyond the next `/clear`.

Rule of thumb: **true only for this thread → handoff; true across threads → memory.**

## Known issues / caveats

1. **Hard-coded studio paths.** The output dir (`~/.claude/data/handoffs/`), the template path, and
   the memory-index path (`~/.claude/projects/-studio/memory/MEMORY.md`) are baked into the procedure.
   On a fresh install, create the two `data/` dirs (see Install); if the memory index isn't present,
   the *Related memory* step degrades to "None" rather than failing.
2. **The 4h scope test is mtime-based and topic-blind.** It picks the single most-recent handoff
   regardless of subject — so an unrelated handoff written in the last 4h makes a new one scope
   "incremental since &lt;that unrelated file&gt;." Pass an explicit `<topic-slug>` and sanity-check the
   `session_scope` frontmatter when you've been switching topics.
3. **Curation is model judgment, not deterministic.** Include/exclude and the *Pruned* note are
   editorial — quality tracks how well the session's arc is understood. A distinct topic slug helps.
4. **A snapshot, not the store.** The handoff captures a moment; durable facts still need promoting
   into a memory node (see *How it fits the system*), or they age out with the file.

## Verified

The live skill, in daily use — every `handoff_*.md` under `~/.claude/data/handoffs/` is its output,
including the handoffs produced during the session that authored this package. The fail-closed
template check and the incremental/full scope switch are both exercised in normal operation.
