# Executor — the change process for tracked artifacts

**Current version: `v1.0.0`** — templates and code live in `Tooling/v1.0.0/`;
recorded test results in `Tests/v1.0.0/`.

A repeatable process for **making changes to a repository so they are tracked and
versioned over time**. It governs any **executor** — human or agent — that edits
a tracked artifact and pushes it. The repository is the unit of truth: if a
change is not in git, it did not happen.

Executor is a **spec plus a checker**. The spec is machine-readable and
normative; the checker is a CI gate that enforces the parts of it that can be
enforced, and says so plainly about the parts that cannot.

## Where it comes from

Ported from this repository's own `PROCESS.md` / `process.yaml`, which govern
tool iteration here. That process is **error-triggered** and versions a tool by
copying its directory — both correct for a template repo, neither correct for a
codebase. Executor keeps the discipline and rebuilds the mechanics on git:

| `PROCESS.md` mechanism | Executor |
|---|---|
| `Tooling/v<next>/` seeded copy | the branch — git is already copy-on-write |
| released version directory is the rollback point | merge-base SHA + release tag |
| `Tests/v<version>/` recorded output | the CI run, linked from the PR |
| issue-id / change-id `<slug>_<hash8>` | GitHub issue and PR numbers |
| reciprocity via heading anchors | `Closes #<n>` — GitHub links both directions |
| one trigger (`error_detected`) | three (fix / addition / chore), one schema |
| one weight of ceremony | three tiers (T0 / T1 / T2) |

## What's here

| Path | Installs to | Role |
|------|-------------|------|
| `Tooling/v1.0.0/templates/executor-process.yaml.template` | `process.yaml` | **The normative spec.** Slots, tiers, graph, loop, invariants |
| `Tooling/v1.0.0/templates/EXECUTOR_PROCESS.md.template` | `PROCESS.md` | The prose form — explanatory, never normative |
| `Tooling/v1.0.0/templates/process-gate.yml.template` | `.github/workflows/process-gate.yml` | The CI gate |
| `Tooling/v1.0.0/templates/PULL_REQUEST_TEMPLATE.md.template` | `.github/PULL_REQUEST_TEMPLATE.md` | The PR body the gate reads |
| `Tooling/v1.0.0/bin/process-gate` | `.github/bin/process-gate` | The checker — python3, stdlib only |

## The shape of it

**Slots, not hardcoding.** Nothing about a specific repo lives in the template. An
adopting repo fills a flat `slots` block — its test runner, default branch,
approvers, which paths force T2, which paths a pipeline owns, and its adoption
commit. A hardcoded test runner is what broke conformance for four tools in this
repo (`PROCESS.md` decision 15); Executor cannot repeat it because it names no
runner at all.

**Tiers, so the process is not bypassed.** T0 trivial, T1 standard, T2
blast-radius. A uniform ritual is fatal both ways — too heavy and it gets
skipped, too light and it is useless for a migration. A bypassed process is worse
than none, because the record then *looks* complete.

**One record schema.** Five slots — X, Y, Z, V, W. The trigger renames only the
first two: outcome/cause for a fix, need/rationale for an addition. So there is
one entry format, one reciprocity rule, and one conformance check rather than a
parallel format per kind of work.

**The yaml is normative and the prose is not.** Inverted deliberately from
`PROCESS.md`, where the prose carried rules the yaml lacked and two tools stayed
silently unmergeable as a result. Making the prose non-normative removes that
failure class instead of managing it.

## Adopting a repo

See [`IMPLEMENTATIONS.md#imp-adopt-a-repo`](IMPLEMENTATIONS.md#imp-adopt-a-repo).
In short: copy the two templates, fill the slots, vendor the checker, install the
workflow, and record the adoption commit — everything before it is `legacy` and
exempt, because a counterpart cannot be manufactured for history that never
happened.

## Known issues / caveats

1. **Approval cannot be enforced here.** A free private repo has no branch
   protection, so nothing prevents a merge without review. The gate *reports*
   approval and never claims to enforce it —
   [`KNOWN_ISSUES.md#process-gate-cannot-enforce-the-approval_de559760`](KNOWN_ISSUES.md#process-gate-cannot-enforce-the-approval_de559760).
2. **The `slots` block must stay flat.** The checker ships stdlib-only so adopting
   repos need install nothing, which means a narrow parser: scalars, inline lists
   and single-level block lists. Nesting `slots` silently drops keys.
3. **Globs are `fnmatch`, not git pathspecs.** `*` crosses `/`. `migrations/*`
   matches `migrations/a/b.sql` — usually what you want, occasionally not.
4. **The gate reads the PR body**, so it re-runs on `edited`. A tier corrected
   after review re-triggers the checks; that is intended, not a loop.
5. **This repo has no CI.** The workflow template exists but Toolbelt has not
   installed it, so Executor's own invariants rest on an executor choosing to run
   the suite — the condition Executor was written to end.

## Verified

`bash Tooling/v1.0.0/tests/verify.sh` — **30/30**, recorded verbatim in
[`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md). Coverage: the slots parser
(scalars, inline lists, block lists, dedent termination), all seven checks in
both directions, the CLI as CI invokes it, and four template-consistency checks
that fail if the prose and the yaml drift apart.
