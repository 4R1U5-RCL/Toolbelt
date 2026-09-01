# Implementations — how Skills/Memory is actually used

Memory is not a `/command`; nothing executes it. Every implementation below is
therefore a **method plus a template**, not an invocation — except the last,
which uses the test helper that ships inside the version directory.

Everything here is derived from `README.md` and from the files actually present
under `Tooling/v1.0.0/`. Each entry cites the form it applies in
[`TEMPLATES.md`](TEMPLATES.md).

---

## new-memory-directory

**Stand up a memory directory for a project**

**Template:** [TEMPLATES.md#memory-md-template](TEMPLATES.md#memory-md-template)

One memory directory per project, laid out as:

```
<project>/memory/
  MEMORY.md            # the index — loaded wholesale every session
  <slug>.md            # one fact per file
```

Method, per `README.md`:

1. Create `<project>/memory/`.
2. Copy `Tooling/v1.0.0/templates/MEMORY.md.template` to
   `<project>/memory/MEMORY.md` — it arrives with the four type sections and no
   frontmatter.
3. Confirm the **live** root before anyone writes to it. README caveat 4: recall
   reads exactly one directory, and writing to an archived root means the note is
   never loaded again. The studio's live root is
   `~/.claude/projects/-studio/memory/`.

Only `MEMORY.md` is loaded in full each session; an entry file is read on demand
when its index line looks relevant.

---

## record-a-memory

**Record one durable fact**

**Template:** [TEMPLATES.md#memory-entry-md-template](TEMPLATES.md#memory-entry-md-template)

The working discipline from `README.md`, in order:

1. **Dedup first.** Look for an existing file that already covers the fact and
   update it rather than create a near-duplicate. Delete memories that turn out
   to be wrong.
2. **Write one file, one fact**, cut from `memory-entry.md.template`. Fill
   `name` (matching the file stem), `description`, and `metadata.type` from the
   enum. For `feedback` and `project` entries, follow the fact with **Why:** and
   **How to apply:** lines.
3. **Add the index pointer** to `MEMORY.md` — `- [Title](file.md) — hook` — *in
   the same change*. An entry absent from the index is never loaded; README
   caveat 2 calls this the most common "why didn't it remember?" cause.
4. **Link** related entries with `[[slug]]` wikilinks, liberally. An unresolved
   wikilink is fine — it marks a memory worth writing later.
5. **Convert relative dates to absolute** ("today" → `2026-08-30`) so the fact
   stays true when re-read months later.

Choosing the type: `user` (who the user is), `feedback` (how to work — always
with the why), `project` (ongoing work and constraints not derivable from code
or git), `reference` (pointers to external resources).

What not to save: anything git history, the repo or `CLAUDE.md` already records;
ephemeral task state. If asked to remember one of those, save what was
non-obvious about it instead.

**Boundary with Handoff.** True only for this thread → a
[Handoff](../Handoff/); true across threads → a memory entry. A durable fact
found mid-session is promoted out of the handoff into a memory node.

---

## drift-check

**Check a memory directory for drift**

**Templates:** [TEMPLATES.md#memory-md-template](TEMPLATES.md#memory-md-template)
and [TEMPLATES.md#memory-entry-md-template](TEMPLATES.md#memory-entry-md-template)
— the linter checks exactly the invariants those two forms fix.

`Tooling/v1.0.0/tests/mem_tool.py` is stdlib-only Python with two subcommands:

```bash
python3 Tooling/v1.0.0/tests/mem_tool.py build <memdir> <templatedir>
python3 Tooling/v1.0.0/tests/mem_tool.py lint  <memdir>
```

`lint` prints shell-assignable variables — `ENTRIES`, `INDEXED_OK`, `ORPHANS`,
`DANGLING_INDEX`, `FRONTMATTER_BAD`, `WL_RESOLVED`, `WL_DANGLING`,
`INDEX_HAS_FRONTMATTER`, `INDEX_ROWS_MALFORMED`, `MAXLEN_OK` — which is how it
catches the failure modes `README.md` names: orphaned (un-indexed) entries,
index rows pointing at files that do not exist, invalid or mismatched
frontmatter, and an index past the 200-line ceiling.

**Honest scope.** `mem_tool.py` lives under `tests/` and is written as the test
suite's helper, not as a shipped, supported command — the README describes
Memory as a discipline and says nothing enforces it (caveat 1). Pointing it at a
real memory directory works and is read-only, but it is being used outside its
stated role.

The full self-check is `bash Tooling/v1.0.0/tests/verify.sh` — 18 assertions
over a sandboxed fixture, including a live drift demo. Recorded output:
[`Tests/v1.0.0/`](Tests/v1.0.0/).
