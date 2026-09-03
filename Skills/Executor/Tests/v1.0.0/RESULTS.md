# Test results — Skills/Executor v1.0.0

Recorded output of running this version's tests. **Verbatim** — a failing,
skipped or unrun check is recorded as such (PROCESS.md §5.6).

**Declared runner:** `bash Tooling/v1.0.0/tests/verify.sh`
**Run:** 2026-09-03, container `python3 3.11.2`, branch `feat/skills-executor`

| Artifact | What it holds |
|---|---|
| [`run-tests.log`](run-tests.log) | The suite, verbatim — 30 tests |
| [`track-b.log`](track-b.log) | Conformance check against PROCESS.md §3, §4, §7 |
| [`dogfood.log`](dogfood.log) | The gate run against this change's own PR body |

---

## Suite — 30/30 OK

`Ran 30 tests in 0.125s — OK`. Four classes:

| Class | Tests | Covers |
|---|---|---|
| `SlotsParser` | 6 | scalars, inline lists, block lists, dedent termination, absent config, placeholder detection |
| `Checks` | 16 | all seven checks, each in both directions |
| `EndToEnd` | 4 | the CLI exactly as CI invokes it — exit codes and full output |
| `Templates` | 4 | the shipped templates stay internally consistent |

The `Templates` class is the drift guard. `test_prose_declares_yaml_normative`
fails if the prose stops declaring the yaml authoritative, and
`test_every_invariant_in_prose_exists_in_yaml` fails if the prose numbers an
invariant the yaml does not define. That pair exists because **this repo has
already lost a week to exactly that drift** — PROCESS.md decision 15, where §5.5
and §8 were amended and `process.yaml` was not, leaving two tools unmergeable
while the preamble made the stale file authoritative.

### End-to-end corroboration

PROCESS.md §5.5 requires evidence that exercises the logged failure, not merely a
green suite. Both issues in `KNOWN_ISSUES.md` are covered:

| Issue | Test that exercises it |
|---|---|
| `process-gate-cannot-enforce-the-approval_de559760` | `Checks.test_approval_always_defers` — asserts `DEFER` on an otherwise fully conformant T1 change, so the check can never regress to `PASS` |
| `the-executor-placeholder-was-committed-a_e6332913` | `track-b.log` — "no bare README placeholder" and the five canonical files, checked directly |

## Track B — conformance

All checks pass at the recorded run. **Two failed on the first pass and are
recorded here because they are the process working, not noise:**

1. **`README` (no extension) still present** — the placeholder was still on disk.
   This is issue `the-executor-placeholder-was-committed-a_e6332913`, caught by
   the check written to catch it.
2. **`TEMPLATES.md` reciprocity BROKEN, 4/4 entries** — every template cited its
   implementation from the summary table at the top of the file, but not from
   inside the entry body. §7 requires *the entry* to cite its counterpart, and a
   table row is not an entry. Fixed by adding an **Applied by** line to each of
   the four entries.

The second is worth keeping visible: the citations *looked* present to a reader
skimming the file, and only a check that resolved ids per-entry found otherwise.
That is the whole argument for mechanical conformance over careful authorship.

## Dogfood — the gate on its own PR

`dogfood.log` records `process-gate` run against this change's own body and
changed-file list: 4 PASS, 3 SKIP, 1 DEFER, 0 failures, exit 0.

**The config used there is hypothetical.** Toolbelt has not adopted Executor —
there is no `process.yaml` at this repo's root and no CI to run the gate in. The
run demonstrates the checker against a realistic slots block; it is not evidence
that this repository is under the process. Recording it as adoption would be the
falsification INV-5 forbids.

## Honest gaps

1. **No CI ran this.** The suite was run by hand in the container. Toolbelt has no
   workflows at all, so nothing re-runs it on push — the condition Executor was
   written to end, still true of the repo it ships in.
2. **The gate has never run on real GitHub Actions.** The workflow template is
   unexercised: its `github.event.pull_request.body` plumbing and the
   `needs.runner.result` mapping are reasoned, not observed. First real adoption
   is where they get tested.
3. **`fnmatch` globbing is untested against deep paths in anger.** `migrations/*`
   matching `migrations/a/b.sql` is asserted in the suite but has not met a real
   repo's layout.
