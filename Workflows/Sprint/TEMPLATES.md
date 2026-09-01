# Templates — Sprint

The production-ready application forms this tool ships. Every one of them lives
under `Tooling/v1.0.0/` and is reproduced here by reference, not by copy — the
file in the version directory is authoritative.

One is a template in the literal sense (a file with `<PLACEHOLDER>` tokens an
agent fills in). The rest are **installable artifacts**: files copied verbatim to
a fixed path in `~/.claude/`, where the harness picks them up. Both kinds are
application forms, so both are listed.

| ID | Template | File | Kind | Used by |
|---|---|---|---|---|
| [T-01](#t-01) | Canonical sprint board | `fleet-kit/SPRINT.md.template` | Fill-in template | [IMP-02](IMPLEMENTATIONS.md#imp-02), [IMP-05](IMPLEMENTATIONS.md#imp-05) |
| [T-02](#t-02) | `/fleet` slash command | `commands/fleet.md` | Installable artifact | [IMP-01](IMPLEMENTATIONS.md#imp-01), [IMP-02](IMPLEMENTATIONS.md#imp-02), [IMP-03](IMPLEMENTATIONS.md#imp-03) |
| [T-03](#t-03) | Role blocks (orchestrator / reviewer / worker) | embedded in `commands/fleet.md` | Emitted fill-in form | [IMP-02](IMPLEMENTATIONS.md#imp-02), [IMP-03](IMPLEMENTATIONS.md#imp-03) |
| [T-04](#t-04) | `fleet-triage` subagent | `agents/fleet-triage.md` | Installable artifact | [IMP-04](IMPLEMENTATIONS.md#imp-04) |
| [T-05](#t-05) | Triage read-only guard hook | `fleet-kit/fleet-triage-guard.sh` | Installable artifact | [IMP-04](IMPLEMENTATIONS.md#imp-04) |
| [T-06](#t-06) | Sprint SOP | `fleet-kit/SOP-Sprints.md` | Installable artifact | [IMP-01](IMPLEMENTATIONS.md#imp-01) |

---

<a name="t-01"></a>
## T-01 — Canonical sprint board (`SPRINT.md.template`)

**File:** `Tooling/v1.0.0/fleet-kit/SPRINT.md.template`
**Installs to:** `~/.claude/data/templates/fleet-kit/SPRINT.md.template`
**Instantiated to:** `<WT>/SPRINT.md` inside the sprint worktree.

The only true fill-in template in the tool. Six numbered sections, in this order:

| § | Section | Filled by |
|---|---|---|
| 0 | Meta — objective, worktree/branch/base, orchestrator + reviewer session names, lock holder, workers, deadline, contended resources | `/fleet` at creation |
| 1 | RULES — LOCKED (7 standing rules + slots 8/9 for sprint-specific ones) | ships pre-filled; `/fleet` seeds the extras |
| 2 | CONTEXT — the reading list table every session loads | orchestrator |
| 3 | TASK DELEGATION — the live board table (`ID · Worker · Task · Status · Review · Blocked-on · Updated`) | `fleet-board addrow` / `setrow` |
| 4 | TASK SUMMARIES — one commented-out skeleton block per task, with acceptance criteria | orchestrator on assignment |
| 5 | STATUS LOG — append-only, newest last | `fleet-board append` |
| 6 | DECISIONS / CONFLICTS | orchestrator |

**Placeholder tokens:** `<NAME>`, `<SLUG>`, `<BASE>`, `<ORCHESTRATOR_SESSION>`,
`<REVIEWER_SESSION>`, `<LABELS>`, `<SHARED_RESOURCES>`, `<TS>`, `<WHO>`.

**Status vocabulary (§3):** `QUEUED → ASSIGNED → IN-PROGRESS → IN-REVIEW →
NEEDS-ITERATION → COMPLETE`, plus `BLOCKED` / `PARKED`.

**Binding property:** the orchestrator is the sole writer. §1 rule 7 makes the
doc authoritative — on conflict a session stops and surfaces rather than
overwriting.

Implementations: [IMP-02](IMPLEMENTATIONS.md#imp-02) (creation),
[IMP-05](IMPLEMENTATIONS.md#imp-05) (the `fleet-board` / `fleet-doctor` operations on it).

---

<a name="t-02"></a>
## T-02 — The `/fleet` slash command

**File:** `Tooling/v1.0.0/commands/fleet.md`
**Installs to:** `~/.claude/commands/fleet.md`

Frontmatter declares `allowed-tools: [Read, Write, Bash]` and the argument hint:

```
"<task>" [--sprint <slug>] [--workers N] [--reviewer studio-XX]
         [--resources "GPU, slots, lock"] [--labels "A,B,C"] [--base <ref>]
```

Defaults it specifies: `--workers 3`, labels `A,B,…` sized to N, `--base main`,
`<SHARED_RESOURCES>` left as a token when `--resources` is absent.

Its sprint-mode body is a seven-step procedure the generating session executes
before emitting anything: verify base ref → create the `sprint/<slug>` worktree
under `.claude/worktrees/` → instantiate [T-01](#t-01) → initial-commit on the
sprint branch only → `fleet-mbox init` the mailbox → acquire the single-
orchestrator lock → bind `WT`/`DOC`/`FLEET_ROOT`/`MBOX`/`BOARD`/`DOCTOR`.

Two hard constraints written into it: the timestamp comes from `date -u` and is
never invented, and the worktree step never switches the live checkout's branch.

Implementations: [IMP-01](IMPLEMENTATIONS.md#imp-01),
[IMP-02](IMPLEMENTATIONS.md#imp-02), [IMP-03](IMPLEMENTATIONS.md#imp-03).

---

<a name="t-03"></a>
## T-03 — The emitted role blocks

**Source:** the "Emit — in this exact order" section of
`Tooling/v1.0.0/commands/fleet.md`.

`/fleet` prints one fenced block per session — orchestrator, reviewer, then one
per worker label — each a paste-ready system prompt. Rules the command imposes on
its own output:

- Header line: `Fleet: <task> — <N> workers, reviewer <name|TBD>[, sprint <slug> @ <WT>]`.
- Every `<…>` is filled before printing.
- Lines marked `‹sprint›` are included only in sprint mode and dropped otherwise.
- The `═══ YOUR TASK ═══` section is deliberately **left empty** — the owner fills
  it per worker. That emptiness is the human gate, not an oversight.

Implementations: [IMP-02](IMPLEMENTATIONS.md#imp-02),
[IMP-03](IMPLEMENTATIONS.md#imp-03).

---

<a name="t-04"></a>
## T-04 — The `fleet-triage` subagent

**File:** `Tooling/v1.0.0/agents/fleet-triage.md`
**Installs to:** `~/.claude/agents/fleet-triage.md`

Frontmatter: `tools: [Read, Bash, Grep]`, `model: sonnet`, `effort: low`,
`maxTurns: 12`, and a `PreToolUse` hook on `Bash` pointing at [T-05](#t-05).

Contract: read-only. It peeks the orchestrator inbox, never `read`/`ack`s, and
never writes the board. It classifies each message into exactly one of
`status-update · blocked · resource-request · conflict · verdict-relay · noise`,
then proposes literal `fleet-board append` / `fleet-board setrow` commands the
orchestrator can paste.

**Correlation gate:** it may propose `COMPLETE` only when the verdict cites the
`sha256:` of the task's *current* head packet. A stale or absent sha becomes a
`conflict` + escalation instead — the verdict may be judging a superseded packet.

**Fixed output shape:**

```
TRIAGE — <slug> — <n> messages
APPLY (orchestrator runs these, then acks):
  <fleet-board … command>            # <why, incl. task ID>
ESCALATE TO OWNER:
  - <one-liner>  (or "none")
NOTES: <ordering/dedup/consistency caveats, or "none">
```

Implementation: [IMP-04](IMPLEMENTATIONS.md#imp-04).

---

<a name="t-05"></a>
## T-05 — The triage read-only guard hook

**File:** `Tooling/v1.0.0/fleet-kit/fleet-triage-guard.sh`
**Installs to:** `~/.claude/data/templates/fleet-kit/fleet-triage-guard.sh`

A `PreToolUse` hook that enforces [T-04](#t-04)'s read-only contract
mechanically rather than by prose. It parses the tool input JSON on stdin, then
exits 2 (blocking the Bash call) when the command matches any of: `fleet-board`
at all; `fleet-mbox` with `read|ack|send|lock|unlock|init`; a redirect,
`tee`, `sed -i`, `mv` or `cp` touching `SPRINT.md`; an `mv`/`rm` under
`/inbox/`; or a bare `rm`.

**Install caveat, verbatim from the tool README:** the agent file references this
hook by the absolute path `/root/.claude/data/templates/fleet-kit/fleet-triage-guard.sh`.
If `$HOME` is not `/root`, that path must be edited to match.

Implementation: [IMP-04](IMPLEMENTATIONS.md#imp-04).

---

<a name="t-06"></a>
## T-06 — The sprint SOP

**File:** `Tooling/v1.0.0/fleet-kit/SOP-Sprints.md` (221 lines)
**Installs to:** `~/.claude/data/templates/fleet-kit/SOP-Sprints.md`

The standing methodology `/fleet` cites as its governance: spin-up flow, doc
lifecycle, the single-writer rule, transport, and the validated hardenings. It is
a document rather than a code artifact, but it is a required part of a correct
install — `commands/fleet.md` names it as governance, so a fleet stood up without
it is running unsourced.

Implementation: [IMP-01](IMPLEMENTATIONS.md#imp-01).

---

## Not templates

`fleet-kit/README.md` (install-path topology view) and `docs/topology.html`
(self-contained system diagram) are documentation, not application forms.
`fleet-mbox.sh`, `fleet-board.sh` and `fleet-doctor.sh` are executables invoked
by the roles, not forms to fill in; they are described in
[IMPLEMENTATIONS.md](IMPLEMENTATIONS.md), not here.
