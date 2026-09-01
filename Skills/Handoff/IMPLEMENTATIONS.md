# Implementations — Skills/Handoff

How this tool is actually used. Every entry cites the form it applies in
[`TEMPLATES.md`](TEMPLATES.md).

Everything below is derived from `README.md`,
`Tooling/v1.0.0/commands/handoff.md`, `Tooling/v1.0.0/templates/handoff-template.md`
and `Tooling/v1.0.0/tests/verify.sh` as they stand at **v1.0.0**. The package has
no `examples/` directory and no config file; there is nothing else to derive
from.

| id | Use case |
|---|---|
| [`IMPL-01`](#impl-01) | Install the skill into a live `~/.claude/` |
| [`IMPL-02`](#impl-02) | End-of-session handoff, full-session scope |
| [`IMPL-03`](#impl-03) | Follow-on handoff within 4 hours, incremental scope |
| [`IMPL-04`](#impl-04) | Offline self-check of the shipped package |

---

<a name="impl-01"></a>
## `IMPL-01` — Install into a live `~/.claude/`

**Applies** [`TMPL-01`](TEMPLATES.md#tmpl-01) and [`TMPL-02`](TEMPLATES.md#tmpl-02).

Both files are copied verbatim; the package is a mirror of the live skill, not a
re-implementation. Run from this tool's root:

```sh
cp Tooling/v1.0.0/commands/handoff.md            ~/.claude/commands/
mkdir -p ~/.claude/data/handoffs ~/.claude/data/templates
cp Tooling/v1.0.0/templates/handoff-template.md  ~/.claude/data/templates/
```

`~/.claude/data/handoffs/` must exist before the first run — the skill writes
there and creates nothing else.

---

<a name="impl-02"></a>
## `IMPL-02` — End-of-session handoff, full-session scope

**Applies** [`TMPL-02`](TEMPLATES.md#tmpl-02) filling [`TMPL-01`](TEMPLATES.md#tmpl-01).

Invoke `/handoff` (or `/handoff <topic-slug>`) before `/clear` or `/compact`.
With no prior handoff in the last four hours the scope is the **whole session**
and the frontmatter records `session_scope: full`.

The command topic-slugs the session, reads the template (aborting if it is
missing or empty), reads the memory index for `[[wikilinks]]`, curates the
session into the seven sections, and writes exactly one file:

```
~/.claude/data/handoffs/handoff_<topic>_<YYYY-MM-DDTHH-MM>.md      # UTC
```

It writes nowhere else — not to memory, plans or templates.

---

<a name="impl-03"></a>
## `IMPL-03` — Follow-on handoff within 4 hours, incremental scope

**Applies** [`TMPL-02`](TEMPLATES.md#tmpl-02) filling [`TMPL-01`](TEMPLATES.md#tmpl-01).

Same invocation. The difference is state on disk: if the most recent file in
`~/.claude/data/handoffs/` has an mtime **less than 14400 seconds** old, the
command compiles only what has happened since it and records
`session_scope: since-<prior-filename>`. This keeps a chain of related handoffs
lean instead of restating the same ground.

The test to pass an explicit `<topic-slug>` here is not cosmetic — the scope
check is mtime-based and topic-blind (see `KNOWN_ISSUES.md`).

---

<a name="impl-04"></a>
## `IMPL-04` — Offline self-check of the shipped package

**Applies** [`TMPL-01`](TEMPLATES.md#tmpl-01) — it is the artefact under test.

```sh
bash Tooling/v1.0.0/tests/verify.sh
```

Runs entirely inside a `mktemp -d` sandbox HOME and never touches the real
`~/.claude`. Fifteen assertions in seven groups: install, the fail-closed
template guard (present / missing / empty), the 4h scope rule (empty dir /
recent / stale), the filename convention, end-to-end generation and section
conformance against `TMPL-01`, memory-link degradation to `None`, and the
write-scope invariant. Exits non-zero on any failure.

Recorded output for the current version: [`Tests/v1.0.0/`](Tests/v1.0.0/).
