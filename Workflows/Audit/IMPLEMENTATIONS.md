# Implementations — Workflows/Audit

How this tool is used in each different use case, each entry citing its template
in [`TEMPLATES.md`](TEMPLATES.md) (PROCESS.md §3).

**Status: empty-but-valid.** There are no implementations to document.

---

## Why this file is empty

PROCESS.md §9 requires the five canonical files on every tool, "empty-but-valid"
where the content does not exist yet, "because their absence is what makes
staleness invisible". This is that case.

`Workflows/Audit` contains no implementation. As of 2026-08-31 the tool
directory held exactly one file, `README.md`, whose entire content is the
sentence *"This folder contains the audit workflow."* There is no script, no
`bin/`, no `lib/`, no `commands/`, no `examples/`, no config and no test — see
[`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log) for the verbatim
`find` output that establishes this.

An implementation entry states how the tool is actually invoked: the command, its
inputs, its outputs, and the template it applies. None of that is derivable here.
The README does not name an audit target, a trigger, an output, or a participant.
A full-text search for "audit" across the Toolbelt repo returns only this tool's
README, its row in the PROCESS.md §9 backlog table, and unrelated uses of the
phrase "audit trail" in `Packages/Poller`, `Packages/Telegram` and
`Workflows/Sprint` — none of which describe this workflow.

Writing a plausible-looking implementation here would be fabrication, and would
do the opposite of what this repo is for: someone would copy it as a proven
method. So nothing is written.

## What a first entry will need

When the workflow is implemented, append an entry — this file is append-only
(PROCESS.md §5.2) — carrying at least:

| Field | Content |
|---|---|
| Use case | The situation this application of the tool addresses |
| Invocation | The exact command or trigger, copy-pasteable |
| Inputs | What it needs, and where those come from |
| Outputs | What it produces, and where that lands |
| Template | A link to the corresponding [`TEMPLATES.md`](TEMPLATES.md) entry |

## Reciprocity

Track B requires that every entry here cites a `TEMPLATES.md` entry and vice
versa. With zero entries on both sides that check is satisfied vacuously — there
is no uncited entry in either file. It becomes a real constraint the moment
either file gains its first entry: the counterpart entry is appended in the same
change.
