---
description: Compile the current session into a handoff document (state, decisions, open tasks, next steps) and save it to ~/.claude/data/handoffs/ using the handoff template
argument-hint: [<topic-slug>]
allowed-tools: [Read, Write, Bash]
---

Compile the current session into a handoff document and save it to `~/.claude/data/handoffs/`.

## Procedure

### 1. Determine topic

If `$ARGUMENTS` is provided, use it as the topic slug (kebab-case). If not, infer a short kebab-case topic from the dominant subject of the current conversation. If the topic is genuinely ambiguous, ask the user to confirm it before proceeding.

### 2. Determine scope

Run:
```
ls -t ~/.claude/data/handoffs/*.md 2>/dev/null | head -1
```

Check the mtime of the most recent file:
```
stat -c %Y ~/.claude/data/handoffs/<most-recent-file>.md 2>/dev/null
```

- If a file exists and its mtime is **less than 4 hours ago**: scope is **incremental** — compile only what has happened since that prior handoff. Note the prior handoff filename in `session_scope` frontmatter as `since-<prior-filename>`.
- Otherwise: scope is **full session** — compile the entire conversation. Set `session_scope: full`.

### 3. Load the template

Read `~/.claude/data/templates/handoff-template.md` to get the exact section structure. Every handoff must follow this template.

After reading, verify the template was loaded:
```bash
if [ ! -f "$HOME/.claude/data/templates/handoff-template.md" ]; then
  echo "ERROR: handoff-template.md not found at $HOME/.claude/data/templates/. Aborting — cannot produce a valid handoff without the template."
  exit 1
fi
```
If the template file exists but is empty, abort: `ERROR: handoff-template.md is empty. Aborting.`

### 4. Load memory index

Read `~/.claude/projects/-studio/memory/MEMORY.md`. Identify which memory nodes are load-bearing for this session's work (project, decision, or reference type). List them under `## Related memory` as `[[node-name]]` wikilinks.

### 5. Compile the handoff

Fill every section of the template. Editorial rules:

- **Include:** decisions made, current state of work, issues hit and their resolutions, open questions, next concrete steps, operational gotchas discovered this session.
- **Exclude:** dead-end explorations that were abandoned, superseded approaches, raw tool output that has been absorbed into decisions, off-topic discussion, anything a new session would never need to re-read.
- **Pruned section:** write one or two lines in `## Pruned from this handoff` noting what was deliberately left out and why. This prevents a future session from trying to re-derive dropped threads.

Curate ruthlessly. A lean handoff is more useful than a complete transcript dump.

### 6. Generate filename and write

Generate a UTC timestamp:
```
date -u +%Y-%m-%dT%H-%M
```

Filename format: `handoff_<topic>_<YYYY-MM-DDTHH-MM>.md`

Write to: `~/.claude/data/handoffs/handoff_<topic>_<timestamp>.md`

Do **not** write to any other directory. Do **not** modify memory files, plan files, or templates.

### 7. Report back

After writing, output:

```
Handoff saved: ~/.claude/data/handoffs/handoff_<topic>_<timestamp>.md
Scope: <full session | incremental since <prior-filename>>
Summary: <one sentence stating current state and immediate next step>

Next: run /clear to start a fresh session, or /compact to collapse this session while keeping the handoff in context.
```
