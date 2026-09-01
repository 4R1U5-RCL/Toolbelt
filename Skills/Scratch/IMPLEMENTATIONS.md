# Implementations — how this tool is actually used

Per PROCESS.md §3, each entry describes one use case and links to the template it
applies in [`TEMPLATES.md`](TEMPLATES.md). Append-only (§5 invariant 2).

Entry headings are the bare id and nothing else (`process.yaml:
definitions.entry`, PROCESS.md §10.13) — the heading text *is* the anchor a
`FILE.md#<id>` citation resolves against. The two closing sections below carry
no heading at all, so nothing that is not an entry can be mistaken for one.

Everything below is derived from what is in this tool directory: `README.md`,
`Tooling/v1.0.0/templates/scratch.gitignore` and
`Tooling/v1.0.0/tests/verify.sh`. This tool has **no `bin/`, no commands, no
`examples/` and no configuration** — it is a discipline plus one droppable file,
as its README says. Nothing here is executed in normal use except the self-check.

---

<a name="append-the-ignore-block"></a>
## append-the-ignore-block

**enforce the discipline in a repository**

**Template:** [`TEMPLATES.md#scratch-gitignore`](TEMPLATES.md#scratch-gitignore)

The primary and normal use. Append the shipped block to a repository's own
`.gitignore` once, then work inside the surfaces it covers. From the README's
Quickstart, with the path updated for the current layout:

```sh
# 1. append the ignore block once, per repo
cat Skills/Scratch/Tooling/v1.0.0/templates/scratch.gitignore >> .gitignore

# 2. do throwaway work in scratch/
mkdir -p scratch && node scratch/try-thing.mjs > scratch/out.json

# 3. git never sees it
git status                 # scratch/ does not appear

# 4. promote only the durable result into the tracked tree
cp scratch/out.json logs/decision-input.json && git add logs/decision-input.json
```

Adapt the row names to the target tree; the README is explicit that the paths in
it (`/studio`, `~/.claude`, `clients/<slug>/`) are the studio's concrete
instance and that what transfers is the shape.

**Choosing a surface** is part of this implementation, and the README's table is
the decision rule: durable cross-session junk and transport go in the repo's
persistent `scratch/`; per-session temporary files go to the harness session
scratchpad (never `/tmp`); a run's evidence stays in `clients/<slug>/` and is not
cleaned up; parallel-agent worktrees live in `.claude/worktrees/`. `logs/` is the
opposite of scratch — the committed, owner-facing rail — and `labs/` holds
separate nested repos, so neither is a scratch surface.

**The rule the block cannot enforce.** `.gitignore` is advisory: `git add -f`,
copying a file into a tracked path, a symlink or a stray editor temp all bypass
it. The never-commit rule is a discipline kept by habit; the block covers the
common case only. This is caveat 6 of the README and is recorded again in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md).

---

<a name="prove-the-block-in-a-throwaway-repo"></a>
## prove-the-block-in-a-throwaway-repo

**the committed self-check**

**Template:** [`TEMPLATES.md#scratch-gitignore`](TEMPLATES.md#scratch-gitignore)

The second use of the same artifact: verifying that a change to the block still
does what it claims, before relying on it. This is the tool's only executable
surface.

```sh
cd Skills/Scratch/Tooling/v1.0.0 && bash tests/verify.sh
```

It builds a real throwaway git repository under a `mktemp -d` sandbox (removed on
exit), applies the shipped block as that repo's `.gitignore`, creates a file on
every surface plus real source, and asserts with `git check-ignore` that the
scratch and secret paths are ignored while source stays trackable — then runs
`git add -A` and asserts no secret or scratch path was staged. It prints
`== scratch smoke: <n> passed, <n> failed ==` and exits non-zero on any failure.

Run it after editing `templates/scratch.gitignore`: the ignore rows and the
assertions are coupled by name, so a renamed or dropped row fails the suite
rather than silently weakening the block. The recorded result for the current
version is in [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md).

There is **no `run-tests.sh`** in this tool, so the script is invoked directly.
`process.yaml`'s `test_decision` branch tests `./run-tests.sh exits 0`; that
entrypoint does not exist here. Recorded as an open point in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) rather than invented as part of a migration.

---

**Uses this tool does not support** — prose, not an entry:

- **No cross-host coordination.** Repo `scratch/` is shared between sessions on
  one filesystem (including container↔host across a bind mount) but not between
  different hosts.
- **No durable storage in the session scratchpad.** It is session-scoped and
  wiped; durable state belongs in the repo's `scratch/` or the assistant's data
  directory.
- **No automatic pruning.** Nothing in this tool deletes anything. Scratch
  accretes and is curated by hand.
