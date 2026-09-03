# Templates — Skills/Executor

The production-ready forms this tool ships. Each cites the implementation that
applies it in [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) (PROCESS.md §3).

Every template lives under `Tooling/v1.0.0/templates/` and is shipped **verbatim**
— the files here are the same bytes the tests exercise.

| Id | Template | Applied by |
|---|---|---|
| [tpl-executor-process-yaml](#tpl-executor-process-yaml) | `executor-process.yaml.template` | [imp-adopt-a-repo](IMPLEMENTATIONS.md#imp-adopt-a-repo) |
| [tpl-executor-process-md](#tpl-executor-process-md) | `EXECUTOR_PROCESS.md.template` | [imp-adopt-a-repo](IMPLEMENTATIONS.md#imp-adopt-a-repo) |
| [tpl-process-gate-workflow](#tpl-process-gate-workflow) | `process-gate.yml.template` | [imp-install-the-gate](IMPLEMENTATIONS.md#imp-install-the-gate) |
| [tpl-pr-body](#tpl-pr-body) | `PULL_REQUEST_TEMPLATE.md.template` | [imp-run-a-t1-change](IMPLEMENTATIONS.md#imp-run-a-t1-change), [imp-run-a-t2-change](IMPLEMENTATIONS.md#imp-run-a-t2-change) |

---

## tpl-executor-process-yaml

**The normative spec** — `Tooling/v1.0.0/templates/executor-process.yaml.template`

**Applied by:** [imp-adopt-a-repo](IMPLEMENTATIONS.md#imp-adopt-a-repo)

Installs to `process.yaml` at the adopting repo's root.

Sections: `slots` (the only block a repo edits), `scope`, `triggers`, `tiers`,
`tasks` (the dependency graph), `loops`, `branches`, `invariants`, `constraints`,
`definitions`.

**This file is authoritative.** The prose form states no rule this one does not,
and where they disagree the prose is the defect. Ships with every slot unfilled;
`Templates.test_yaml_template_ships_unfilled` asserts that, so a filled-in
placeholder can never leak into the template.

The `slots` block is deliberately flat — the checker parses it without a YAML
library so an adopting repo installs nothing.

---

## tpl-executor-process-md

**The prose form** — `Tooling/v1.0.0/templates/EXECUTOR_PROCESS.md.template`

**Applied by:** [imp-adopt-a-repo](IMPLEMENTATIONS.md#imp-adopt-a-repo)

Installs to `PROCESS.md` beside the yaml. Thirteen sections: scope, slots, tiers,
the record, invariants, the procedure, the loop and escalation, versioning,
evidence, T2 rollback, conformance, adoption and legacy, decisions.

**Explanatory, never normative.** Its preamble says so, and
`Templates.test_prose_declares_yaml_normative` fails if that sentence is ever
removed. `Templates.test_every_invariant_in_prose_exists_in_yaml` fails if the
prose numbers an invariant the yaml does not define — the specific drift that
left two tools in this repo unmergeable.

§13 carries the ten decisions settled at adoption, in the form `PROCESS.md` §10
uses.

---

## tpl-process-gate-workflow

**The CI gate** — `Tooling/v1.0.0/templates/process-gate.yml.template`

**Applied by:** [imp-install-the-gate](IMPLEMENTATIONS.md#imp-install-the-gate)

Installs to `.github/workflows/process-gate.yml`. Two jobs:

- **`runner`** — runs the repo's declared runner. **Ships failing on purpose.**
  `s1_runner` is the one value no template can know, and a gate that quietly
  skips its evidence check is precisely the failure it exists to prevent.
- **`gate`** — `if: always()`, so it reports even when the runner failed. It
  collects the PR body and the changed-path list, maps the runner's result to
  `pass` / `fail` / `unknown`, and runs the checker.

Requires `.github/bin/process-gate` vendored alongside. Triggers on `opened`,
`edited`, `synchronize` and `reopened` — `edited` matters, because the tier and
the rollback plan live in the PR body and can change after review.

---

## tpl-pr-body

**The PR body the gate reads** —
`Tooling/v1.0.0/templates/PULL_REQUEST_TEMPLATE.md.template`

**Applied by:** [imp-run-a-t1-change](IMPLEMENTATIONS.md#imp-run-a-t1-change), [imp-run-a-t2-change](IMPLEMENTATIONS.md#imp-run-a-t2-change)

Installs to `.github/PULL_REQUEST_TEMPLATE.md`. Carries the tier line, the
`Closes #` citation, the five record slots X/Y/Z/V/W, an evidence section, and a
`Rollback:` section for T2.

The headings are **load-bearing**: `process-gate` greps this structure. Renaming
`Rollback:` makes every T2 change fail the rollback check; dropping the tier line
fails `tier-declared` on every change in the repo.

Only `closes`, `fixes` or `resolves` followed by `#<n>` counts as a citation —
`Checks.test_bare_hash_is_not_a_citation` pins that. A bare `#12` in prose is a
reference, not a reciprocal link, and GitHub will not close the issue on it.
