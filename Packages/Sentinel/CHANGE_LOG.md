# Change log — Packages/Sentinel

Every iteration made in response to an issue in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), each citing the issue it resolves
(PROCESS.md §3).

Ids follow `process.yaml` → `definitions.change-id`: `<description>_<hash8>`,
hashed over the `iteration` field alone.

| Id | Iteration | Resolves | Version |
|---|---|---|---|
| [read-the-exit-code-as-a-bitmask-and-clas_e650916f](#read-the-exit-code-as-a-bitmask-and-clas_e650916f) | Classify AIDE's exit code as the bitmask it is | [aide-check-exits-non-zero-when-it-succee_d4ecdc86](KNOWN_ISSUES.md#aide-check-exits-non-zero-when-it-succee_d4ecdc86) | `v1.0.0` |
| [resolve-the-baselines-directory-at-run-t_6aebf499](#resolve-the-baselines-directory-at-run-t_6aebf499) | Baselines outside the repo, enforced by a guard | [host-baselines-were-committed-into-the-t_9d09c448](KNOWN_ISSUES.md#host-baselines-were-committed-into-the-t_9d09c448) | `v1.0.0` |
| [narrow-the-not-installed-heuristic-to-th_a252c780](#narrow-the-not-installed-heuristic-to-th_a252c780) | Absent-tool detection reads stderr only | [the-not-installed-heuristic-matched-not_a90badf2](KNOWN_ISSUES.md#the-not-installed-heuristic-matched-not_a90badf2) | `v1.0.0` |
| [add-an-identity-field-to-the-host-config_09a88e07](#add-an-identity-field-to-the-host-config_09a88e07) | Configurable ssh identity | [the-ssh-runner-had-no-way-to-name-an-ide_86ed9055](KNOWN_ISSUES.md#the-ssh-runner-had-no-way-to-name-an-ide_86ed9055) | `v1.0.0` |
| [pass-an-explicit-config-path-to-aide-con_ab659d01](#pass-an-explicit-config-path-to-aide-con_ab659d01) | AIDE gets an explicit `--config` | [aide-check-was-invoked-without-config-so_7932f6e0](KNOWN_ISSUES.md#aide-check-was-invoked-without-config-so_7932f6e0) | `v1.0.0` |
| [capture-the-indented-file-and-hash-lines_c597ad8e](#capture-the-indented-file-and-hash-lines_c597ad8e) | rkhunter warnings name their file | [rkhunter-evidence-captured-only-the-warn_f8ba0431](KNOWN_ISSUES.md#rkhunter-evidence-captured-only-the-warn_f8ba0431) | `v1.0.0` |
| [make-the-command-timeout-configurable-pe_e9639fc9](#make-the-command-timeout-configurable-pe_e9639fc9) | Per-host timeout, 3600s default | [the-runner-s-fixed-900-second-command-ti_b1115836](KNOWN_ISSUES.md#the-runner-s-fixed-900-second-command-ti_b1115836) | `v1.0.0` |

All seven carry an empty `merge_commit`: the work is on branch
`feat/packages-sentinel` and has not merged. PROCESS.md §6 step 7 fills these in
and moves the issues to `resolved`.

---

## read-the-exit-code-as-a-bitmask-and-clas_e650916f

| Field | Value |
|---|---|
| **id** | `read-the-exit-code-as-a-bitmask-and-clas_e650916f` |
| **resolves** | [`KNOWN_ISSUES.md#aide-check-exits-non-zero-when-it-succee_d4ecdc86`](KNOWN_ISSUES.md#aide-check-exits-non-zero-when-it-succee_d4ecdc86) |
| **iteration** | Read the exit code as a bitmask and classify it, rather than letting a non-zero code propagate: 0 is clean, 1 to 7 decompose into new, removed and changed files, 14 and above are AIDE's own errors, and any unmapped code is an error rather than clean |
| **expected_result** | A detected change produces a `finding` verdict with the categories named, and no wrapper dies on a successful detection |
| **change** | `sentinel/classify.py` — `classify_aide`, `describe_aide_bits`, the `AIDE_*` constants; `bin/sentinel` runs without `set -e` and says why; `TEMPLATES.md#tpl-cron-wrapper` carries the same warning |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because AIDE overloads exit status as a findings bitmask
(cause Y), a `set -e` wrapper terminated silently on precisely the runs that
detected something (outcome X). Iteration Z maps the code explicitly, defaulting
every unmapped value to `error` so that no unanticipated code can render as a
clean host.

**Evidence.** `Tests/v1.0.0/run-tests.log` — `TestAideExitCodes` covers 0, all of
1–7, the error floor at 14, and unmapped 8/13/99/−1.

---

## resolve-the-baselines-directory-at-run-t_6aebf499

| Field | Value |
|---|---|
| **id** | `resolve-the-baselines-directory-at-run-t_6aebf499` |
| **resolves** | [`KNOWN_ISSUES.md#host-baselines-were-committed-into-the-t_9d09c448`](KNOWN_ISSUES.md#host-baselines-were-committed-into-the-t_9d09c448) |
| **iteration** | Resolve the baselines directory at run time from outside the repository, and refuse the run with a BoundaryError if it ever resolves inside the checkout |
| **expected_result** | The repository can be published without exposing any host; pointing Sentinel at an in-repo baselines path fails closed with a message that explains why |
| **change** | `sentinel/config.py` — `resolve_baselines_dir`, `repo_root`, `assert_outside_repo`; `sentinel/errors.py` — `BoundaryError`; `examples/hosts.example.json` replaces real host data; the baselines themselves moved to `~/.claude/data/baselines` and commit `89a376b` was reset off the branch |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because the baselines were placed by asking where they fit
under PROCESS.md rather than whether they belonged in a publishable repo at all
(cause Y), a commit existed carrying two hosts' addresses, kernels and integrity
fingerprints (outcome X). Iteration Z moves the data out and makes the tool
enforce the split, since a rule that depends on being remembered will be
forgotten on the run that matters.

**Deliberate ordering.** The guard runs before the directory-exists check, so an
in-repo path fails on the boundary rather than on a missing file — the operator
learns the rule instead of being sent to create the directory.

**Evidence.** `Tests/v1.0.0/boundary-guard-2026-09-03.log` (live, exit 2 in both
in-repo cases) and `TestBoundaryGuard` in `Tests/v1.0.0/run-tests.log`.

---

## narrow-the-not-installed-heuristic-to-th_a252c780

| Field | Value |
|---|---|
| **id** | `narrow-the-not-installed-heuristic-to-th_a252c780` |
| **resolves** | [`KNOWN_ISSUES.md#the-not-installed-heuristic-matched-not_a90badf2`](KNOWN_ISSUES.md#the-not-installed-heuristic-matched-not_a90badf2) |
| **iteration** | Narrow the not-installed heuristic to the shell's own complaint on stderr, so output that merely contains the phrase cannot turn a finding into a skip |
| **expected_result** | `debsums` reporting a missing packaged file classifies as `finding`; a genuinely absent tool still classifies as `skipped` |
| **change** | `sentinel/classify.py` — `_not_installed` accepts exit 127, or `command not found` / `: not found` in stderr only |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because the heuristic searched stdout and stderr as one blob
for "not found" (cause Y), a missing system binary — close to the most
interesting thing this tool can report — would have been rendered as a skipped
check (outcome X). Iteration Z restricts the match to the stream that carries the
shell's own complaint.

**Direction matters.** Mistaking an absent tool for a finding costs a false
alarm. Mistaking a finding for an absent tool costs the point of the sweep. The
heuristic is now biased toward the first.

**Evidence.** `TestDebsums::test_missing_file_output_is_not_mistaken_for_an_absent_tool`
in `Tests/v1.0.0/run-tests.log`, asserting on the real debsums output format.

---

## add-an-identity-field-to-the-host-config_09a88e07

| Field | Value |
|---|---|
| **id** | `add-an-identity-field-to-the-host-config_09a88e07` |
| **resolves** | [`KNOWN_ISSUES.md#the-ssh-runner-had-no-way-to-name-an-ide_86ed9055`](KNOWN_ISSUES.md#the-ssh-runner-had-no-way-to-name-an-ide_86ed9055) |
| **iteration** | Add an identity field to the host config and pass it to ssh as -i, so a sweep authenticates with the key it was configured with |
| **expected_result** | A sweep against a host with a configured key succeeds unattended, with no agent loaded and no interactive fallback |
| **change** | `sentinel/config.py` — `Host.identity` and its parsing; `sentinel/runner.py` — `SshRunner(target, identity)` appending `-i` with `~` expanded; `sentinel/cli.py` — `runner_for` passes it through; `TEMPLATES.md#tpl-hosts-json` documents the field |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because key selection was left to ssh's defaults while
`BatchMode=yes` removed the interactive fallback (cause Y), the first live sweep
returned `Permission denied (publickey)` against a reachable host whose key was
present on the machine (outcome X). Iteration Z makes the key part of the host's
configuration.

**Found by running it.** This defect is invisible to review — the code reads
correctly — and appeared on the first contact with a real host. It is the
argument for PROCESS.md invariant 5 in miniature.

**Evidence.** `TestSshIdentity` in `Tests/v1.0.0/run-tests.log`, and the live
two-host sweep in `Tests/v1.0.0/live-sweep-2026-09-03.log` that only became
possible after this change.


---

## pass-an-explicit-config-path-to-aide-con_ab659d01

| Field | Value |
|---|---|
| **id** | `pass-an-explicit-config-path-to-aide-con_ab659d01` |
| **resolves** | [`KNOWN_ISSUES.md#aide-check-was-invoked-without-config-so_7932f6e0`](KNOWN_ISSUES.md#aide-check-was-invoked-without-config-so_7932f6e0) |
| **iteration** | Pass an explicit --config path to aide, configurable per host and defaulting to /etc/aide/aide.conf, and classify AIDE's configuration-error codes as an error that names the config it could not read |
| **expected_result** | `aide --check` runs on Debian/Ubuntu hosts and returns a real integrity verdict; a genuinely bad config path produces an error that says which path failed |
| **change** | `sentinel/checks.py` — `aide_command()` and `AIDE_CMD` retired in its favour; `sentinel/config.py` — `Host.aide_config`; `sentinel/classify.py` — `AIDE_CONFIG_ERRORS` message names the path; `tests/test_checks.py` — new file asserting the **command strings** |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because the bare `aide --check` cannot work on a distribution that
compiles in no default config path, and because no test asserted on the command string
(cause Y), the primary integrity check returned `ERROR` on both hosts on the first full
production sweep (outcome X). Iteration Z passes the path explicitly and adds the missing
layer of test coverage.

**The coverage lesson, stated plainly.** 55 tests passed while the tool's headline check
could not execute. Every one of them fed the classifier its inputs directly, so the suite
proved the classifier and proved nothing about what the tool ran. **A test that supplies
its own inputs to a pure function cannot fail for the reason the tool is about to fail.**
`tests/test_checks.py` exists to close that class, not just this instance.

**What kept it from being worse.** `classify_aide` maps unrecognised codes to `error`,
never `clean` — so this surfaced as a loud failure rather than a passing check that never
ran. That default was written for exactly this, and it is the reason a broken v1.0.0 could
not have shipped a false all-clear.

---

## capture-the-indented-file-and-hash-lines_c597ad8e

| Field | Value |
|---|---|
| **id** | `capture-the-indented-file-and-hash-lines_c597ad8e` |
| **resolves** | [`KNOWN_ISSUES.md#rkhunter-evidence-captured-only-the-warn_f8ba0431`](KNOWN_ISSUES.md#rkhunter-evidence-captured-only-the-warn_f8ba0431) |
| **iteration** | Capture the indented File: and hash lines that follow each rkhunter warning, so every warning names the file it is about |
| **expected_result** | Each rkhunter warning in a report names its subject, so an operator can triage from the report instead of from the host's log |
| **change** | `sentinel/classify.py` — `_rootkit_records()` walks header + indented continuation lines; `classify_rootkit` emits one entry per record |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because rkhunter's property warnings are three-line records and the
filter kept only the header (cause Y), 22 warnings rendered as 22 identical lines naming no
file (outcome X). Iteration Z attaches the continuation lines to their header.

**What the missing lines actually were.** `su`, `sudo`, `login`, `mount`, `cp`, `fsck` and
16 more — changed by an unattended upgrade one day after the rkhunter baseline was taken,
and independently confirmed as legitimate distribution binaries by `debsums` passing on the
same host in the same sweep. The right conclusion was reachable from data the sweep already
held; the report simply did not carry it.

**Evidence.** `Tests/v1.0.0/rkhunter-format-2026-09-03.log` — the real three-line record
format this parses, captured from the run that exposed the defect.


---

## make-the-command-timeout-configurable-pe_e9639fc9

| Field | Value |
|---|---|
| **id** | `make-the-command-timeout-configurable-pe_e9639fc9` |
| **resolves** | [`KNOWN_ISSUES.md#the-runner-s-fixed-900-second-command-ti_b1115836`](KNOWN_ISSUES.md#the-runner-s-fixed-900-second-command-ti_b1115836) |
| **iteration** | Make the command timeout configurable per host and raise the sweep default to 3600 seconds, and report a timeout as its own verdict rather than as a transport failure |
| **expected_result** | A full AIDE walk on a large host completes inside the timeout; a check that genuinely overruns is reported as having timed out, naming the check and the limit, and the host's remaining checks still run |
| **change** | `sentinel/config.py` — `Host.timeout`; `sentinel/errors.py` — `CheckTimeout`; `sentinel/runner.py` — raises `CheckTimeout`, accepts a per-call timeout; `sentinel/checks.py` — `sweep_host` passes the host's timeout and handles a timeout separately from a transport failure; `tests/test_sweep.py` — `TestTimeout` |
| **version** | `v1.0.0` |
| **merge_commit** | — |

**Why (Y → X → Z).** Because 900 seconds was guessed before any check had touched a real
host, and because `FakeRunner` returns instantly so no test could contradict it (cause Y),
a working AIDE check on the larger host was cut off at 920 seconds and would have been
recorded as **"host unreachable"** (outcome X). Iteration Z raises the default to a
measured 3600, makes it per-host, and gives a timeout its own vocabulary.

**Why the wrong word mattered more than the wrong number.** A too-short timeout costs a
re-run. Calling the result "unreachable" invents an infrastructure fault, and — because
`sweep_host` breaks out of the loop on transport failure — silently drops the remaining
checks for that host, including the `debsums` pass that would have shown the box was fine.

**A timeout no longer ends the host's sweep.** It is one failed check, not a dead machine,
so the sweep continues to the next check rather than abandoning the host.

**Evidence.** `TestTimeout` in `Tests/v1.0.0/run-tests.log`, and the measured 920-second
run recorded in `Tests/v1.0.0/aide-corrected-2026-09-03.log`.
