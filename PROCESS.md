# Toolbelt — Process & Conventions

Binding rules for every tool in this repository, and for any agent or human
working in it. `process.yaml` alongside this file is the machine-readable form of
§6; where the two disagree, `process.yaml` is authoritative.

---

## 1. What this repo is

Templates for **proven, reusable** tools — so that standing up a repeatable tool
or process is a matter of copying a known-good template, not reinventing one.

Three things follow from that, and they are the reason the conventions below
exist at all:

- **Record how a tool is applied**, so an application method is written once.
- **Record every error and its fix**, so a fix is derived once, not re-derived on
  each encounter.
- **Make staleness visible**, so nobody builds on a tool that is broken or
  superseded.

This repo is **v2.0 of [`operand-packages`](https://github.com/4R1U5-RCL/operand-packages)**.
Not all packages have been transferred yet; absence here does not mean a tool
does not exist.

---

## 2. Layout

```
Toolbelt/
  Packages/     external tools reachable via API — a reusable map of how our
                system interacts with the external tool
  Skills/       Claude Code tooling — reusable implementations or infrastructure
                for the Claude Code harness
  Workflows/    multi-step or multi-tool processes involving several agents or
                complex sequencing
```

The descriptions are a loose match to contents; place a tool by its dominant
character.

---

## 3. Canonical files

Every tool directory (`<Area>/<Tool>/`) carries these five. Filenames are
**UPPERCASE**, exactly as written — the repo already follows this and mixed
casing breaks cross-links.

| File | Holds |
|---|---|
| `README.md` | What the tool is and how to use it |
| `IMPLEMENTATIONS.md` | How the tool is used in each different use case, each linking to its template in `TEMPLATES.md` |
| `TEMPLATES.md` | The templates themselves — production-ready application forms |
| `KNOWN_ISSUES.md` | Every issue found with the tool, each linking to the iteration that fixed it in `CHANGE_LOG.md` |
| `CHANGE_LOG.md` | Every iteration made in response to an issue in `KNOWN_ISSUES.md` |

`IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` and `KNOWN_ISSUES.md` ↔ `CHANGE_LOG.md` are
reciprocal pairs. An entry in one that does not cite its counterpart is
incomplete.

---

## 4. Code and test layout

Two versioned directories per tool. Both are binding.

| Directory | Holds |
|---|---|
| `Tooling/v<major>.<minor>.<patch>/` | The tool's code at that version |
| `Tests/v<major>.<minor>.<patch>/` | The recorded **results** of running that version's tests |

**Test code ships inside the version it tests** — `Tooling/v2.0.0/tests/` — because a
test belongs to the version it was written against. `Tests/v2.0.0/` holds *output*:
what the run actually produced, in a form a human can read and confirm.

**Versioning is how rollback works.** A released version directory is immutable.
An iteration never edits one; it seeds the next version from it and works there.
The previous directory therefore remains a permanent, in-repo rollback point —
this is safeguard 1 of §5 in concrete form, not a separate copy kept elsewhere.

**Bumping:** patch for a fix, minor for a backwards-compatible addition, major
for a breaking change. The version created by
an iteration is the `fix-version-id` in `process.yaml`, and it is what
`KNOWN_ISSUES.md` and `CHANGE_LOG.md` cite when the issue is closed.

---

## 5. Invariants

These are absolute. An agent that cannot proceed without breaking one stops and
reports instead.

1. **`KNOWN_ISSUES.md` is append-only.** Never overwritten. A fix appends a new
   entry carrying the version number of the iteration that resolved it.
2. **`IMPLEMENTATIONS.md` is append-only.** Never overwritten. A new
   implementation appends; it does not replace an existing one.
3. **Never apply a fix blindly.** The issue is logged and the iteration planned
   before any tooling file is touched.
4. **Never merge directly to `main`.** All work reaches `main` through a PR.
5. **A PR cannot merge without test files** demonstrating the fix works
   end-to-end, ideally producing output a human reviews.
6. **Never falsify a test result.** A test document must record what actually
   happened. A failing or unrun test is recorded as such.
7. **Same-turn logging.** If a session must iterate on a tool mid-work because of
   an error, `KNOWN_ISSUES.md` is appended **in the same turn as the iteration** —
   recording both the code error and what it resulted in, plus the fix — so the
   error cannot be forgotten.

### Escalation

**Escalate** is the single term for handing control back. It means: stop the run,
make no further changes, and report to the user with the current state — the
issue-id, the change-id, the branch, the round reached, and why the check could
not be answered.

An escalation is neither a rejection nor a failure verdict. It is the *absence*
of a verdict: the work is left exactly where it stands for the user to judge.
Waiting on an unanswered human gate (§8) is not an escalation — the process is
still running, it is simply waiting.

### The three safeguards against blind overwrite

Each is independently verifiable, and all three must hold:

1. The last released version directory (`Tooling/v<current>/`) is intact and
   untouched before any work begins — it **is** the rollback point (§4). No
   separate copy is taken.
2. All iteration happens on a **branch**, in a **new version directory**;
   existing files are never edited in place before merge.
3. Nothing reaches `main` except through a PR carrying passing test files and
   human approval.

---

## 6. The fix procedure

Full dependency spec: **`process.yaml`**. In prose:

**Step 1 — Record, before touching anything.** Two reciprocal entries, appended:

- `KNOWN_ISSUES.md` gains: an error occurred producing **outcome X** → it
  occurred because of **cause Y** → iteration **Z** is planned to resolve it,
  recorded in `CHANGE_LOG.md`.
- `CHANGE_LOG.md` gains: because of **cause Y**, **outcome X** occurred → to
  resolve Y, iteration **Z** is planned, expected to produce **result V** → to
  reach V we are changing **W**.

Each entry cites the other's id.

**Step 2 — Fix the rollback point.** Confirm `Tooling/v<current>/` is complete and
record it as the rollback point for this iteration. It stays untouched until the
work merges.

**Step 3 — Branch, then open the next version directory.** Open a git branch off
`main`, then seed `Tooling/v<next>/` from `Tooling/v<current>/`. All work happens
in the new directory.

**Step 4 — Iterate under the loop.** Plan → execute → review → test → human gate.
Any of review, test, or human may send the work back to planning. The loop is
bounded to **3 rounds** (`process.yaml: loops.fix_loop.max_rounds`); exhausting
the bound **escalates** rather than continuing.

**Step 5 — Open a PR.** It must contain test files that corroborate the fix
end-to-end.

**Step 6 — Human approval, then merge.** The user approves; the agent performs
the merge. An unanswered gate leaves the PR open and the process waiting. Merge
is the only path to `main`.

**Step 7 — Record the version.** `CHANGE_LOG.md` records the merged version and
commit; `KNOWN_ISSUES.md` marks the issue resolved, citing that version.

---

## 7. Test tracks

### Track A — Error Resolution

1. An error occurred.
2. The error is logged in `KNOWN_ISSUES.md` with a planned iteration.
3. The plan is shown to the user and approved.
4. The plan is executed.
5. The executed iteration produces outcome **X**, which resolves the error as
   demonstrated by evidence **Y**.
6. **If** outcome X does not resolve the error, as demonstrated by evidence
   **Z**, then `KNOWN_ISSUES.md` is appended with the failure and the loop
   returns to step 1 of §6.

Test outcomes must **corroborate that the fix resolves the logged error** — a
green suite that does not exercise the failure is not corroboration.

### Track B — Conformance

Checks that a tool carries the documents and layout §3 and §4 require. Run in
two places:

1. **On a new tool**, before its first version is released.
2. **On an existing tool**, when the fix procedure next touches it (§9).

| Check | Passes when |
|---|---|
| Canonical files | all five of §3 exist and are non-empty |
| Reciprocity | every `KNOWN_ISSUES.md` entry cites a `CHANGE_LOG.md` id and vice versa; every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` id and vice versa |
| Code layout | the tool's code sits under `Tooling/v<version>/` |
| Test layout | recorded results exist under `Tests/v<version>/` for the current version |
| Version agreement | `README.md`, the newest `Tooling/` directory and the newest `CHANGE_LOG.md` entry name the same current version |

A tool failing Track B cannot release a new version. Failures are logged in
`KNOWN_ISSUES.md` like any other issue and fixed through §6.

---

## 8. Pull requests

- Branch off `main`; never commit to `main`.
- The PR must contain versioned test results under `Tests/`.
- Tests must include an **end-to-end** test corroborating the fix, ideally with
  output a human reviews to confirm.
- Approval is a human gate. Rejection returns the work to planning inside the
  fix loop; it does not end the process.
- **Approval and merge are separate.** The user approves; the agent performs the
  merge. An agent never merges without a recorded approval.
- An unanswered gate is not a rejection. The PR is left open for the user; the
  process waits and never auto-advances.
- On merge, `CHANGE_LOG.md` and `KNOWN_ISSUES.md` are updated in the same change.

---

## 9. Migration backlog

This document is the source of truth. The table below is the gap between it and
`main` as measured on 2026-08-31 — a backlog to close, not evidence against the
convention.

| Tool | README | IMPLEMENTATIONS | TEMPLATES | KNOWN_ISSUES | CHANGE_LOG | Tooling/ | Tests/ |
|---|---|---|---|---|---|---|---|
| `Packages/Poller` | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `Packages/Scrape` | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| `Packages/Telegram` | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| `Skills/Errors` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `Skills/Handoff` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `Skills/Memory` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `Skills/Scratch` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `Workflows/Audit` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `Workflows/Review` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `Workflows/Sprint` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `Workflows/Validate` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

Summary: **no tool has `CHANGE_LOG.md`**; only `Telegram` has `TEMPLATES.md`; no
`Skills/` or `Workflows/` tool has `IMPLEMENTATIONS.md` or `KNOWN_ISSUES.md`; no
tool uses `Tooling/` or `Tests/`. Existing tools keep test *code* in a lowercase
`tests/` directory at the tool root, which moves into `Tooling/v<version>/tests/`.

### When a tool must conform

- **On next touch.** Any tool the fix procedure runs against is brought into
  conformance as part of that change. Its current code becomes
  `Tooling/v<current>/` and the iteration opens `Tooling/v<next>/`.
- **Missing canonical files are created empty-but-valid** at that point —
  `CHANGE_LOG.md` with its header, `TEMPLATES.md` with the templates already in
  use, `KNOWN_ISSUES.md` for tools that lack one.
- **No tool is exempt.** A tool that has never had an issue still needs the five
  canonical files, because their absence is what makes staleness invisible.
- **A tool that has never been versioned starts at `v1.0.0`.** Its current code
  becomes `Tooling/v1.0.0/` regardless of any version its README claims; the README
  is corrected to match.

---

## 10. Decisions

All settled 2026-08-31.

| # | Decision | Resolution |
|---|---|---|
| 1 | Test tracks beyond Track A | **Track B — Conformance** (§7): correct documents in place, for new and existing tools |
| 2 | Loop bound | **3 rounds**, then escalate |
| 3 | Hash identity | **`summary` alone.** Two errors are the same error when described the same way |
| 4 | Unanswered human gate | **Never auto-advance.** The PR is left open for the user; the process waits |
| 5 | Who merges | **The agent**, after a recorded human approval |
| 6 | Initial version for an unversioned tool | **`v1.0.0`** |

Identity deliberately excludes the cause: an id must be computable at
`check_existing`, which runs before the cause is determined. It also excludes
`occurred_at` (which would prevent any two occurrences matching) and the tool
(each tool has its own `KNOWN_ISSUES.md`).

### Sentences reconstructed from the source draft

Three sentences in the source were incomplete. Reconstructed as follows and
confirmed by the owner 2026-08-31:

- *"tests outcomes must corroborate that the…"* → §7, "corroborate that the fix
  resolves the logged error."
- *"…then a PR to merge, before a PR can be merged, there must be …, so that we
  can roll back to a previous version if needed"* → §8, versioned test results
  under `Tests/`.
- *"You must never falsify test documents,"* → §5 invariant 6.
