# Templates — the production application forms

Per PROCESS.md §3, this file holds the templates themselves: the production-ready
forms in which this tool is applied. Each entry names the implementation in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) that uses it (reciprocity, §3).

`process.yaml` defines an id format for `issue-id` and `change-id` only; it
defines none for template or implementation entries. The anchors below are
therefore plain slugs of the entry name, not `<description>_<hash8>` ids.

**This tool ships exactly one template.** It is a file, not a snippet — the
entry below documents what is actually in
`Tooling/v1.0.0/templates/`, which contains one item.

---

<a name="scratch-gitignore"></a>
## `scratch-gitignore` — the drop-in ignore block

| Field | Value |
|---|---|
| **Artifact** | `Tooling/v1.0.0/templates/scratch.gitignore` |
| **Form** | A `.gitignore` fragment, appended to a repository's own `.gitignore` |
| **Used by** | [`IMPLEMENTATIONS.md#append-the-ignore-block`](IMPLEMENTATIONS.md#append-the-ignore-block), [`IMPLEMENTATIONS.md#prove-the-block-in-a-throwaway-repo`](IMPLEMENTATIONS.md#prove-the-block-in-a-throwaway-repo) |
| **Tested by** | `Tooling/v1.0.0/tests/verify.sh` — all 29 checks exercise this file |

The file is organised in four labelled sections. What is actually in it:

| Section | Rows |
|---|---|
| Untracked working surfaces | `scratch/`, `.runstate/`, `.worktrees/`, `.claude/worktrees/`, `clients/`, `labs/` |
| Secrets — values never | `.env`, `*.env`, `.env.*.bak`, `.env.bak-*`, `*.pem`, `*.key`, `*_token`, `*.token` |
| Build / cache noise | `node_modules/`, `.pnpm-store/`, `.next/`, `.vercel/`, `*.tsbuildinfo`, `*.log` |
| Editor / OS / IDE / notebook cruft | `*.swp`, `*.swo`, `*~`, `*.tmp`, `.DS_Store`, `Thumbs.db`, `.idea/`, `.vscode/`, `.ipynb_checkpoints/` |

Its own header states the adaptation rule: adjust the names to your tree, because
the transferable part is the **shape** — one block covering every working surface
and every secret file.

Nine of these rows are asserted present by the suite (`scratch/`, `.runstate/`,
`.claude/worktrees/`, `clients/`, `labs/`, `.env`, `*.key`, `*.pem`, `_token`);
ten paths are then proved ignored in a real repository, and the remaining rows
are covered by section membership rather than by a named check.

---

## Templates that do not exist

Stated explicitly so their absence is not read as an oversight:

- There is **no template for the surface-selection discipline** (repo `scratch/`
  vs session scratchpad vs `clients/<slug>/`). That half of the tool is prose in
  `README.md` and rules in `IMPLEMENTATIONS.md`; nothing in `templates/`
  expresses it, and no file in this tool generates or checks it.
- There is **no pre-commit hook, secret-scanner config, or CI template.**
  `README.md` names gitleaks as the thing to add "on top" when hard enforcement
  is needed, but this tool ships no such artifact.
