# Implementations — Sprint

How this tool is actually used. Each implementation below is derived from
`README.md` and from the shipped code under `Tooling/v1.0.0/` — the `/fleet`
command body, the `fleet-triage` agent definition, and the four `fleet-kit`
scripts. Nothing here is aspirational; where a capability is claimed but not
demonstrable in this repo, it is called out as such.

Append-only (PROCESS.md §5.2). A new use case adds an entry; it never rewrites one.

| ID | Implementation | Template |
|---|---|---|
| [IMP-01](#imp-01) | Install the kit into `~/.claude/` | [T-02](TEMPLATES.md#t-02), [T-06](TEMPLATES.md#t-06) |
| [IMP-02](#imp-02) | Sprint mode — worktree + canonical board + mailbox | [T-01](TEMPLATES.md#t-01), [T-02](TEMPLATES.md#t-02), [T-03](TEMPLATES.md#t-03) |
| [IMP-03](#imp-03) | Block-only mode — role blocks with no durable state | [T-02](TEMPLATES.md#t-02), [T-03](TEMPLATES.md#t-03) |
| [IMP-04](#imp-04) | The orchestrator's triage turn | [T-04](TEMPLATES.md#t-04), [T-05](TEMPLATES.md#t-05) |
| [IMP-05](#imp-05) | Running the sprint — mailbox + board + doctor | [T-01](TEMPLATES.md#t-01) |

---

<a name="imp-01"></a>
## IMP-01 — Install the kit into `~/.claude/`

**When.** Once per host, before the first `/fleet` run. Everything else assumes
these paths exist, because the command body and the agent frontmatter address
them absolutely.

**How** (from `README.md`, with the paths updated for the `Tooling/` layout):

```sh
cd Tooling/v1.0.0
cp commands/fleet.md            ~/.claude/commands/
cp agents/fleet-triage.md       ~/.claude/agents/
mkdir -p ~/.claude/data/templates/fleet-kit
cp fleet-kit/*                  ~/.claude/data/templates/fleet-kit/
chmod +x ~/.claude/data/templates/fleet-kit/*.sh
```

**The one path to check.** `agents/fleet-triage.md` names the guard hook by the
absolute path `/root/.claude/data/templates/fleet-kit/fleet-triage-guard.sh`. If
`$HOME` is not `/root`, edit it to wherever the script actually landed — the
guard silently does nothing if the path is wrong, and the read-only contract of
[T-04](TEMPLATES.md#t-04) then rests on prose alone.

Templates: [T-02](TEMPLATES.md#t-02), [T-06](TEMPLATES.md#t-06).

---

<a name="imp-02"></a>
## IMP-02 — Sprint mode: worktree + canonical board + mailbox

**When.** A piece of work is large enough to want several sessions on it at once
and a durable board that survives any one of them dying.

**Invocation**, from the orchestration session, in the repo:

```
/fleet "<objective>" --sprint <slug> --workers 3 --resources "<contended rails>"
```

**What it does before printing anything** (seven steps in `commands/fleet.md`):

1. Verifies the base ref exists (`git rev-parse --verify <base>`, default `main`).
2. Creates the worktree `.claude/worktrees/sprint-<slug>` on branch
   `sprint/<slug>`, idempotently — it skips creation if the worktree already
   lists. This never switches the live checkout's branch.
3. Instantiates [T-01](TEMPLATES.md#t-01) into `<WT>/SPRINT.md`, filling the
   placeholder tokens and stamping the timestamp from `date -u`.
4. Commits that doc on the sprint branch only; never pushes unless asked.
5. Creates the mailbox: `FLEET_ROOT=/studio/scratch/fleet/<slug> fleet-mbox.sh
   init orchestrator reviewer <LABELS...>`.
6. Acquires the single-orchestrator advisory lock. **If it reports `LOCK HELD`,
   another orchestrator is already live — stop and tell the owner rather than
   running a second one**, because two writers on a sole-writer board corrupt it.
7. Binds `WT`, `DOC`, `FLEET_ROOT`, `MBOX`, `BOARD`, `DOCTOR` for the emitted
   blocks.

Then it emits the role blocks ([T-03](TEMPLATES.md#t-03)).

**The two human gates.** The owner prompts twice: once to plan, then once per
worker to hand it its task. `/fleet` deliberately leaves `═══ YOUR TASK ═══`
empty; the orchestrator never hands out tasks itself (§1 rule 1 of the board).

**Bring-up checklist.** Open one terminal per session, each with a stable name
(`claude --name reviewer`, `--name worker-a`, …) — default `studio-XX` names churn
and collide, which is why the mailbox exists at all. Paste each session its
block; the owner posts each worker its task.

Templates: [T-01](TEMPLATES.md#t-01), [T-02](TEMPLATES.md#t-02),
[T-03](TEMPLATES.md#t-03).

---

<a name="imp-03"></a>
## IMP-03 — Block-only mode: role blocks with no durable state

**When.** A short parallel push that does not warrant a branch, a board or a
mailbox — you want the coordination *prompts* and nothing else.

**Invocation:** omit `--sprint`.

```
/fleet "<objective>" --workers 2
```

**What changes.** All seven sprint-mode steps are skipped: no worktree, no
`SPRINT.md`, no mailbox, no lock. The emitted blocks drop every line marked
`‹sprint›`, including the `cd`, doc and mailbox lines.

**What you give up.** There is no durable board and no transport, so the Inform
and Review protocols fall back to native `SendMessage`/`ListAgents` — which the
README records as unreliable under default session names (known issue 3). Use
this mode only when losing a status ping is acceptable.

Templates: [T-02](TEMPLATES.md#t-02), [T-03](TEMPLATES.md#t-03).

---

<a name="imp-04"></a>
## IMP-04 — The orchestrator's triage turn

**When.** Every turn the orchestrator has inbox traffic.

**How.** The orchestrator spawns the `fleet-triage` subagent
([T-04](TEMPLATES.md#t-04)), passing `FLEET_ROOT`, `WT`, `MBOX` and `BOARD` in
its prompt. Triage reads the board once, **peeks** (never reads/acks) the
orchestrator inbox, classifies each message, and returns an `APPLY` block of
literal `fleet-board` commands plus an `ESCALATE TO OWNER` list.

The orchestrator then runs the `APPLY` block verbatim and acks:

```sh
FLEET_ROOT=… FLEET_SESSION=orchestrator "$MBOX" ack orchestrator
```

**Why the split.** Peek-then-apply-then-ack keeps the orchestrator the sole
writer *and* the single reader; triage only ever observes. The split is enforced
by [T-05](TEMPLATES.md#t-05), a `PreToolUse` hook that blocks the Bash call
outright if triage tries to write the board, ack, send, lock or delete.

**The gate that matters.** Triage proposes `COMPLETE` only when the reviewer's
verdict cites the `sha256:` of the task's current head packet. Stale or missing
sha → `conflict` + escalate, never `COMPLETE`.

Templates: [T-04](TEMPLATES.md#t-04), [T-05](TEMPLATES.md#t-05).

---

<a name="imp-05"></a>
## IMP-05 — Running the sprint: mailbox, board, doctor

**The three executables**, all under `Tooling/v1.0.0/fleet-kit/`. None of them
resolves a sibling by relative path — each takes its target from an argument or
the environment, so they work from wherever they are installed.

### `fleet-mbox.sh` — transport

Environment: `FLEET_ROOT` (required), `FLEET_SESSION` (this session's logical
name, for `send`/`lock`/`ack`).

| Command | Does |
|---|---|
| `init <name>…` | create `inbox/` + `processed/` per name |
| `send <to> [subject]` | body on stdin → one file in `<to>`'s inbox, written temp then atomically renamed |
| `check [who]` / `ls [who]` | count / list unread |
| `peek [who]` | print unread **without** acking |
| `read [who]` | print unread, then move to `processed/` |
| `ack [who]` | move unread → `processed/` without printing |
| `lock` / `unlock` / `lock-status` | advisory single-writer lock via atomic `mkdir` |
| `hash` | sha256 of stdin, for citing a packet by hand |

One file per message, addressed by stable logical name (`orchestrator`,
`reviewer`, `A`, `B`, `C`) rather than by session id. Every message header
carries an auto `sha256:` of its body — the correlation id a review packet and
its verdict both cite.

### `fleet-board.sh` — the sole writer's safe primitives

`addrow <WT> <ID> <WORKER> <task…>` · `append <WT> <text…>` ·
`setrow <WT> <ID> <STATUS>` · `commit <WT> [msg]` · `show <WT>`.

Every mutation is written to a temp file and atomically renamed, so an
interrupted turn cannot leave a half-written board. `addrow` refuses a duplicate
ID (exit 3) and inserts directly under the §3 table separator; `setrow` exits 3
if the row is not found; `append` inserts the timestamped bullet just before the
`## 6.` heading so it stays inside §5.

### `fleet-doctor.sh` — what the human runs to look

`fleet-doctor [check|status] <WT> [--root <FLEET_ROOT>]`. `FLEET_ROOT` defaults
to `/studio/scratch/fleet/<slug>` derived from the worktree basename.

`check` runs seven checks — mailbox structure; lock staleness (warns past
`FLEET_LOCK_STALE_H`, default 6h); §0 workers vs §3 workers; `IN-REVIEW` rows
with an empty reviewer mailbox; uncommitted `SPRINT.md`; inbox backlog > 20; and
scratch disk usage as info. It exits 0 green, 1 on warnings, 2 on failures.
`status` prints a colorized board glance: lock holder, §3 rows by status,
per-inbox unread counts, and the last five §5 lines.

Template: [T-01](TEMPLATES.md#t-01) (the board these operate on).

---

## Honest gap

No implementation above has an automated test in this repository. See
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) and [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md).
