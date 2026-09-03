# Implementations — how Skills/Executor is actually used

Each entry cites the form it applies in [`TEMPLATES.md`](TEMPLATES.md)
(PROCESS.md §3). Ids are free slugs per `process.yaml` →
`definitions.impl-id / template-id`.

| Id | Implementation | Template |
|---|---|---|
| [imp-adopt-a-repo](#imp-adopt-a-repo) | Bring a repository under the process | [tpl-executor-process-yaml](TEMPLATES.md#tpl-executor-process-yaml), [tpl-executor-process-md](TEMPLATES.md#tpl-executor-process-md) |
| [imp-install-the-gate](#imp-install-the-gate) | Wire the conformance checks into CI | [tpl-process-gate-workflow](TEMPLATES.md#tpl-process-gate-workflow) |
| [imp-run-a-t1-change](#imp-run-a-t1-change) | Make a standard change | [tpl-pr-body](TEMPLATES.md#tpl-pr-body) |
| [imp-run-a-t2-change](#imp-run-a-t2-change) | Make a blast-radius change | [tpl-pr-body](TEMPLATES.md#tpl-pr-body) |

---

## imp-adopt-a-repo

**Bring a repository under the process**

**Template:** [TEMPLATES.md#tpl-executor-process-yaml](TEMPLATES.md#tpl-executor-process-yaml),
[TEMPLATES.md#tpl-executor-process-md](TEMPLATES.md#tpl-executor-process-md)

1. Copy `Tooling/v1.0.0/templates/executor-process.yaml.template` to
   `process.yaml` at the repo root, and
   `EXECUTOR_PROCESS.md.template` to `PROCESS.md` beside it.
2. **Fill every slot.** An unfilled slot is a placeholder in angle brackets; the
   gate reports `DEFER` on the checks that depend on it rather than passing them.
   `s8_t2_paths` and `s9_excluded` may legitimately be empty lists — the gate
   reports `SKIP` and says so.
3. **Choose the adoption commit** and record it as `s10_adoption`. Everything
   before it is `legacy` and exempt from reciprocity. Nothing is backfilled: a
   counterpart cannot be manufactured for a change history that never happened,
   which INV-5 forbids outright.
4. Keep the `slots` block flat — scalars, inline lists, single-level block lists.
   The checker is stdlib-only by design and its parser is narrow.

Verify with the gate before opening the first PR:

```
python3 .github/bin/process-gate --config process.yaml
```

With no PR body it reports the checks it cannot answer. That is the intended
output, not a failure.

---

## imp-install-the-gate

**Wire the conformance checks into CI**

**Template:** [TEMPLATES.md#tpl-process-gate-workflow](TEMPLATES.md#tpl-process-gate-workflow)

1. Vendor `Tooling/v1.0.0/bin/process-gate` to `.github/bin/process-gate` and
   mark it executable.
2. Copy `process-gate.yml.template` to `.github/workflows/process-gate.yml`.
3. **Replace the `runner` job's `run:` step with `s1_runner`.** It ships failing
   on purpose — the one value the template cannot know is the repo's own test
   command, and a gate that silently skips the evidence check is the failure mode
   the whole thing exists to prevent.
4. Copy `PULL_REQUEST_TEMPLATE.md.template` to
   `.github/PULL_REQUEST_TEMPLATE.md`, so authors are handed the structure the
   gate reads.

The `gate` job runs with `if: always()` and maps the runner's result to
`--runner-status`. A runner that never ran yields `unknown`, which **fails** a
T1+ change (INV-4) and defers a T0.

---

## imp-run-a-t1-change

**Make a standard change** — a bug fix, feature or refactor

**Template:** [TEMPLATES.md#tpl-pr-body](TEMPLATES.md#tpl-pr-body)

1. **Record first.** Open the issue record with X, Y and Z filled. Nothing is
   touched before this exists (INV-2).
2. Record the merge-base SHA and current release tag — the rollback point. No
   copy is taken.
3. Branch per `s3_naming`.
4. Work the loop: plan → execute → review → test → human gate, bounded to three
   rounds. On re-entry, append the failure to the issue record **before**
   replanning. Exhausting the bound escalates.
5. Open the PR from the template: tier `T1`, `Closes #<n>`, X/Y/Z/V/W filled,
   evidence linked.
6. Approval, then merge — separate acts (INV-8).
7. Append the outcome: merge commit and version to the change record, `resolved`
   to the issue record.

**V is the slot that carries the weight.** If a reviewer cannot answer yes or no
to it without re-deriving the problem, it is not an expected result yet.

---

## imp-run-a-t2-change

**Make a blast-radius change** — migration, deploy, credential rotation, deletion

**Template:** [TEMPLATES.md#tpl-pr-body](TEMPLATES.md#tpl-pr-body)

Everything in [imp-run-a-t1-change](#imp-run-a-t1-change), plus — **before
execution, not before merge**:

1. A written rollback plan in the PR's `Rollback:` section, naming the exact
   steps from `s11_rollback`, and **validated**. The gate checks the section is
   present and non-empty; only a human can check it was actually tried.
2. The named gate from `s4_approver_t2`, recorded.
3. Post-execution evidence recorded verbatim — including what a partial failure
   would have looked like.

**An irreversible operation is decomposed into reversible stages** — expand then
contract, or equivalent — so every gate has something to reverse. If it cannot be
decomposed, it escalates to a human to execute. Never a bare irreversible step
behind a single gate.

A path listed in `s8_t2_paths` cannot be declared below T2; the gate fails the
tier floor rather than trusting the declaration.
