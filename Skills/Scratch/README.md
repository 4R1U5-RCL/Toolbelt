# Scratch — the untracked working-space discipline

"Scratch" here isn't one directory — it's a **family of ephemeral / untracked working surfaces**
unified by a single rule: **nothing under scratch is ever committed to the project's git history.**
It's where intermediate results, throwaway scripts, run evidence, parallel-agent worktrees, and
cross-session transport live — kept deliberately *outside* the tracked tree so the repo stays clean
and secrets never leak in. This package documents the surfaces, the never-commit rule, and the
`.gitignore` that enforces them.

Not a `/command` — a discipline, like **[Memory](../Memory/)**.

## What's here

| Path | Role |
|------|------|
| `templates/scratch.gitignore` | Drop-in `.gitignore` block that ignores every scratch surface **plus** the never-commit secrets/clients rows. Append it to a repo's `.gitignore`. |

## The surfaces

One rule, several homes — pick by **lifetime** and **scope**:

| Surface | What it's for | Lifetime | Tracked? |
|---------|---------------|----------|----------|
| **Repo `scratch/`** | Persistent, cross-session junk drawer: one-off scripts, diagrams, working bundles, and durable cross-session transport (e.g. a fleet mailbox under `scratch/fleet/<slug>/`). | Lives on the volume until manually pruned; **shared across all sessions on the same filesystem**. | Gitignored whole. |
| **Session scratchpad** (`/tmp/.../scratchpad`) | The harness's per-session temp dir — intermediate results, temp scripts/config. Use it instead of `/tmp`. | **Ephemeral** — session-scoped, isolated, wiped; never durable state. | Not in the repo at all. |
| **Per-run artifacts** (`clients/<slug>/`) | A run's evidence trail: `run-*.log`, `cost-*.json`, `run-state.json`, `hard-spec.json`, `open_tasks.md`. **Leave them** — they're the crash-recovery evidence. | Persist with the client dir. | `clients/` gitignored whole; each client dir is its **own** repo that re-ignores these. |
| **`.claude/worktrees/`** | Parallel-agent / fleet git worktrees. | Duration of the parallel work, then pruned. | Gitignored. |
| **`.runstate/`** | Runtime state, created on demand. | Runtime-only. | Gitignored + on the NEVER-commit list. |

Adjacent but **not** scratch — don't conflate: `logs/` is the committed, owner-facing rail (the
*opposite* of scratch); `labs/` holds separate nested repos, not throwaway files.

## The rules (the discipline)

1. **Never commit scratch.** Nothing under any scratch surface enters the project's history —
   enforced by `.gitignore`, but the rule is yours to keep.
2. **Never commit secrets or client work.** `.env` values, tokens/keys of any kind, `clients/`,
   `.runstate/`. Names + status may appear in tracked docs; **values never.** This is the
   load-bearing rule of the whole system.
3. **Temp → session scratchpad, not `/tmp`.** All transient per-session files go to the harness
   scratchpad; reach for `/tmp` only if explicitly required.
4. **Durable coordination → repo `scratch/`; ephemeral temp → session scratchpad.** The split is
   deliberate: cross-session transport (a fleet mailbox) lives in **persistent** `scratch/`, because
   the session scratchpad is wiped and can't carry state between sessions.
5. **Leave run evidence.** Per-client run artifacts are the crash-recovery trail — never "clean them
   up" mid- or post-run.
6. **Scratch is a junk drawer, not a source of truth.** It accretes and isn't auto-pruned; nothing
   there is authoritative or guaranteed current. Promote anything durable into the repo, `logs/`, or
   memory.

## Enforcement (`.gitignore`)

Append `templates/scratch.gitignore` to the repo's `.gitignore`. The core of it:

```gitignore
# Untracked working surfaces — never enter git history
scratch/
.runstate/
.worktrees/
.claude/worktrees/
clients/
labs/
# Secrets — names/status may appear in docs, VALUES NEVER
.env
*.env
*.pem
*.key
*_token
```

Adjust names to your tree; the **shape** — ignore every working surface + every secret file — is the
point.

## How it fits the system

Scratch is the **untracked** side; its counterparts are the tracked / durable rails:

- `logs/` — the committed owner-facing record (verdicts, manifests).
- **[Memory](../Memory/)** / **[Handoff](../Handoff/)** — durable knowledge and session continuity.
- **[Sprint](../../Workflows/Sprint/)** — its file mailbox is *hosted on* persistent `scratch/`,
  which is exactly why it survives across sessions where peer messaging can't.

Rule of thumb: **throwaway or in-flight → scratch; a record someone reads later → logs / memory /
handoff.**

## Known issues / caveats

1. **Same-filesystem only.** Repo `scratch/` is shared between sessions (and container↔host on a
   bind mount) but **not across different hosts** — cross-host coordination can't ride scratch.
2. **The session scratchpad is ephemeral.** Session-scoped and wiped; never park durable state there.
   Durable → repo `scratch/` (persistent) or the assistant's data dir.
3. **The `clients/` double-repo trap.** "Gitignored in the monorepo" does **not** mean "safe to
   commit inside the client repo" — each client dir is its own repo whose `.gitignore` *also*
   excludes the run artifacts and `.env`. Check both.
4. **No auto-clean.** Scratch accretes stale one-offs; treat it as a junk drawer to curate manually,
   and never assume a file there is current or authoritative.
5. **Peer registration is unreliable** — the scratch-hosted mailbox exists precisely because
   session-to-session messaging can't be trusted; recipients poll, they don't rely on a wake.

## Provenance

Mirrors the live studio discipline: `/studio/.gitignore` ignores `scratch/`, `clients/`, `.runstate/`,
`labs/`, and `.claude/worktrees/`; the fleet mailbox runs out of `/studio/scratch/fleet/<slug>/`; and
per-client run artifacts persist under `clients/<slug>/` as the recovery trail. The `.gitignore` block
shipped here is lifted from that tree (plus the `anthro-bugbounty` secrets wall). Nothing here is
executed — it is a discipline + a droppable ignore file.
