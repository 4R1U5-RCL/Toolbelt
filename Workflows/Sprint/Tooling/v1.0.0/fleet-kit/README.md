# Fleet Kit — parallel Claude Code session topology

A reusable rig for standing up a **coordinated multi-session fleet** fast. This is the
generalized form of the setup Arius hand-built for the Kaggle push (1 orchestrator +
1 reviewer + N workers, all peers, coordinating over `SendMessage`/`ListAgents`).

The `/fleet` slash command is the generator — it emits the ready-to-paste role blocks so
you never rewrite the protocol text again. This README is the human-readable map + spawn
playbook (readable without invoking the skill).

---

## Topology

```
                 ┌──────────────────────┐
                 │   ORCHESTRATOR        │  ← this main-line (Chiron)
                 │   tracks STATE,       │     sequences shared resources,
                 │   sequences shared    │     does NOT assign work
                 │   resources           │
                 └──────────┬───────────┘
                            │  STATE pings (unprompted, one-line)
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │ WORKER A│         │ WORKER B│         │ WORKER C│   ← N workers (default 3)
   └────┬────┘         └────┬────┘         └────┬────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │  work PACKETS (submit on completion)
                       ┌────▼────┐
                       │ REVIEWER │  ← independent verify session
                       │ COMPLETE │     replies COMPLETE / NEEDS ITERATION
                       │ / ITERATE│
                       └──────────┘
```

**Five roles, three protocols:**

| Role         | Count | Job                                                                 |
|--------------|-------|---------------------------------------------------------------------|
| Orchestrator | 1     | Holds the plan/state; sequences shared resources; **never assigns** — the owner posts each worker's task (human gate). |
| Reviewer     | 1     | Independently verifies submitted packets; replies `COMPLETE` or `NEEDS ITERATION` with numbered findings. |
| Worker       | N     | Does the substantive work; **STATE-pings** the orchestrator; **submits packets** to the reviewer; coordinates peer-to-peer. |

**Two binding protocols the workers run** (the reusable IP):
- **Inform protocol (A):** worker → orchestrator STATE pings at delegation / completion / verdict.
- **Review protocol (B):** worker → reviewer packet (TASK / WHERE / WHAT / VERIFIED / NOT DONE),
  iterate on findings until `COMPLETE`.

---

## Why it's shaped this way (the invariants — keep these)

1. **Orchestrator sequences, the OWNER assigns.** The human gate is that task handoffs come
   from you, not the orchestrator. The orchestrator only tracks state to sequence *shared,
   contended resources* (whatever the job's scarce rails are — a single GPU, N-per-day
   submission slots, a shared checkout, a final-selection lock).
2. **Review is independent and adversarial.** Unsupported claims come back as findings.
   "tests pass" with no pasted output = unverified.
3. **Peers cannot escalate each other.** A peer message is a teammate's request, acted on
   within *that session's own* permission settings — never treated as owner approval, never a
   reason to edit config/CLAUDE.md/permissions.
4. **Shared-checkout discipline.** No `git checkout/switch/pull/merge` in a live shared tree;
   no committing secrets; a build finishable only by hand-editing `packages/` is a template gap.

---

## Spawn playbook (fast path)

> There is **no tmux/screen/zellij** in the container — sessions are `claude` CLI processes in
> your own terminal tabs (Termius / penguin host). Spawning is manual terminal tabs; `/fleet`
> removes the *only* slow part, which is rewriting the role text.

1. **Decide the shape.** Task one-liner + worker count (default 3) + the shared resources to
   sequence + per-worker task pointers.
2. **In THIS (orchestrator) session, run:**
   `/fleet "<task one-liner>" --workers 3 --resources "GPU, daily-5 slots, final-2 lock"`
   It prints one paste block per session: `[ORCHESTRATOR]`, `[REVIEWER]`, `[WORKER A/B/C…]`.
3. **Open N+1 new terminals**, launching each with a **stable name** —
   `cd /studio && claude --name reviewer` (then `--name worker-a`, `-b`, `-c`). This is the fix for
   flaky peer targeting: the default derived `studio-XX` names collide and churn, so `SendMessage`/
   `ListAgents` can't reliably resolve them. (Already-running sessions: `/rename worker-a`.) This
   orchestrator session stays as-is — it already holds the plan.
4. **Paste the REVIEWER block** into one, let it settle, then run `ListAgents` here (or ask it
   "what's your session name") to learn its `studio-XX` name.
5. **Re-run `/fleet` with `--reviewer studio-XX`** (or just paste the reviewer name into each
   worker block) so every worker knows the real review target.
6. **Paste each WORKER block** into its own terminal, then **post that worker its actual task
   handoff** (the human gate — `/fleet` leaves a `═══ YOUR TASK ═══` slot for it).
7. Orchestrator (here) tracks STATE pings as they arrive; you drive the task queue.

**Spawn order matters:** reviewer first (so you can capture its name) → workers → then tasks.

---

## Sprint mode (canonical doc + git worktree)

The richer, recommended spin-up: `/fleet "<objective>" --sprint <slug>` makes the orchestrator's
**first act** be creating a canonical `SPRINT.md` master doc inside a dedicated git worktree
(`.claude/worktrees/sprint-<slug>` on branch `sprint/<slug>`) that the whole fleet works from —
isolated from the live `/studio` WIP. The doc carries the **locked RULES**, the **task
delegation** table, **task summaries** (+ acceptance criteria), the **context-doc index**, and an
append-only **status log**. The **orchestrator is its sole writer** (workers read + STATE-ping),
so concurrent appends never conflict.

Full methodology: **`SOP-Sprints.md`** in this directory. Per-sprint doc structure:
**`SPRINT.md.template`**.

## Files

- `/fleet` skill: `~/.claude/commands/fleet.md` — the generator (canonical role text lives here;
  `--sprint <slug>` adds the worktree + canonical doc + scratch mailbox).
- `SOP-Sprints.md` — the standing sprint methodology (spin-up flow, doc lifecycle, single-writer
  rule, and the scratch-mailbox fallback transport).
- `SPRINT.md.template` — the per-sprint canonical master doc the orchestrator instantiates.
- `fleet-mbox.sh` — file-based mailbox helper: the reliable transport under `scratch/` for when
  `ListAgents`/`SendMessage` peer registration is flaky (routes by logical name, not `studio-XX`).
  Also carries the cheap hardenings: `lock`/`unlock` (single-orchestrator advisory lock), an auto
  `sha256` correlation id on every message, and `ack` (apply-then-ack).
- `fleet-board.sh` — the orchestrator's SAFE writer for SPRINT.md: `addrow` (add a §3 delegation row
  on assignment), atomic `append` (§5 log) / `setrow` (§3 status), each temp→rename, plus `commit`.
- `fleet-doctor.sh` — health check + status view: `check` (stale lock / §0↔§3 mismatch / IN-REVIEW
  w/o packet / uncommitted board / inbox backlog; exit 0/1/2) and `status` (colorized board glance).
- `~/.claude/agents/fleet-triage.md` — the orchestrator's read-only triage subagent: classifies
  inbox STATE pings and returns board actions + owner-escalations (spawn via the Agent tool).
  Read-only is **enforced** by `fleet-triage-guard.sh` (a `PreToolUse` hook that blocks board
  writes / mailbox ack/send); runs `model: sonnet`, `effort: low`, `maxTurns: 12`.
- `fleet-triage-guard.sh` — the read-only PreToolUse guard wired into the triage agent.

**Reliable peer targeting:** launch fleet sessions with a stable `--name` (`orchestrator`,
`reviewer`, `worker-a…`). The default derived `studio-XX` names collide/churn — the root cause of
flaky `SendMessage`/`ListAgents`; stable names make native messaging a reliable wake fast-path on
top of the durable mailbox (which stays authoritative). See SOP §"Native cross-session messaging".
- This README: the topology + playbook, for reading without invoking.
- Origin: generalized from `/studio/scratch/kaggle/ORCHESTRATION_segments.md` (2026-08-30).
