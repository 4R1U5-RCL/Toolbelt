# Known issues — Packages/Sentinel

Every issue found with this tool, each citing the iteration that addressed it in
[`CHANGE_LOG.md`](CHANGE_LOG.md) (PROCESS.md §3).

**Append-only** (PROCESS.md §5.1). Entries are never removed; a fix appends a new
entry carrying the version that resolved it. Ids follow `process.yaml` →
`definitions.issue-id`: `<description>_<hash8>`, hashed over the `summary` field
alone (PROCESS.md §10.3).

**Note on history.** All seven entries were found while building `v1.0.0` —
five of them by running the tool rather than by reading it, and the last three by the
first full production sweep and the corrected AIDE run that followed it, before release. None is `legacy`:
no prior version exists for them to predate, so all four are bound by the §7
reciprocity check.

| Id | Summary | Status |
|---|---|---|
| [aide-check-exits-non-zero-when-it-succee_d4ecdc86](#aide-check-exits-non-zero-when-it-succee_d4ecdc86) | `aide --check` exits non-zero when it succeeds at detecting, so a wrapper under `set -e` dies when the check works | in-progress |
| [host-baselines-were-committed-into-the-t_9d09c448](#host-baselines-were-committed-into-the-t_9d09c448) | Host baselines were committed into the Toolbelt repository, publishing addresses and integrity fingerprints if it is made public | in-progress |
| [the-not-installed-heuristic-matched-not_a90badf2](#the-not-installed-heuristic-matched-not_a90badf2) | The not-installed heuristic matched "not found" anywhere in output, so a real finding classified as an absent tool | in-progress |
| [the-ssh-runner-had-no-way-to-name-an-ide_86ed9055](#the-ssh-runner-had-no-way-to-name-an-ide_86ed9055) | The SSH runner could not name an identity file, so a working key returned Permission denied | in-progress |
| [aide-check-was-invoked-without-config-so_7932f6e0](#aide-check-was-invoked-without-config-so_7932f6e0) | `aide --check` ran without `--config`, so AIDE exited 17 and the primary integrity check never ran on either host | in-progress |
| [rkhunter-evidence-captured-only-the-warn_f8ba0431](#rkhunter-evidence-captured-only-the-warn_f8ba0431) | rkhunter evidence named no file — 22 changed-file warnings rendered as 22 identical lines | in-progress |
| [the-runner-s-fixed-900-second-command-ti_b1115836](#the-runner-s-fixed-900-second-command-ti_b1115836) | The 900s command timeout is shorter than a full AIDE check on a large host, so a slow check reads as an unreachable host | in-progress |

**Why all seven are `in-progress` and not `resolved`.** `merge_commit` is empty in
every cited change entry: the work sits unmerged on branch
`feat/packages-sentinel`. `process.yaml → definitions.issue-status` is explicit —
"`resolved` is never written while merge_commit is empty; an approved-but-unmerged
fix is still `in-progress`". They move to `resolved` at PROCESS.md §6 step 7, on
merge.

---

## aide-check-exits-non-zero-when-it-succee_d4ecdc86

| Field | Value |
|---|---|
| **id** | `aide-check-exits-non-zero-when-it-succee_d4ecdc86` |
| **summary** | aide --check exits non-zero when it succeeds at detecting a change, so any wrapper running under set -e dies at the moment the check works |
| **outcome** | A sweep wrapper terminated silently on exactly the runs that found something, and reported nothing. The failure is invisible in the only case that matters |
| **cause** | AIDE overloads its exit status: it is a bitmask of what was found (1 new, 2 removed, 4 changed), not a success/failure flag. `set -e` reads any non-zero as failure |
| **iteration** | Read the exit code as a bitmask and classify it, rather than letting a non-zero code propagate: 0 is clean, 1 to 7 decompose into new, removed and changed files, 14 and above are AIDE's own errors, and any unmapped code is an error rather than clean |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#read-the-exit-code-as-a-bitmask-and-clas_e650916f`](CHANGE_LOG.md#read-the-exit-code-as-a-bitmask-and-clas_e650916f), fix-version `v1.0.0` |
| **occurrences** | 1 — hit 2026-09-01 on a production host during the negative-control run that proved AIDE detection works |

### Outcome (X)

The negative control was a scoped baseline over a temporary tree: check clean,
append one byte to a watched file, re-check. It behaved like this:

```
GOOD tree      -> exit=0   AIDE found NO differences
TAMPERED tree  -> exit=4   Changed entries: 1
  File: .../config.conf
   Size    : 17        | 26
   SHA256  : UWrXs4iy… | 99ug/cMM…
```

The detection worked. The wrapper around it did not survive it. A scheduled
sweep built that way is worse than no sweep: it produces a clean-looking history
of runs that silently aborted the instant they found anything.

### Cause (Y)

AIDE's exit status encodes findings, not success. Codes 1, 2 and 4 are bit flags
that combine (7 = all three); 14 and above are AIDE's own error conditions. Shell
convention says non-zero is failure, and `set -e` enforces that convention
without knowing this program breaks it.

### Iteration (Z)

`classify.classify_aide` maps the code deliberately, and the mapping's default
is `error`, never `clean` — an exit code nobody anticipated must not be able to
render as a clean host. `bin/sentinel` and the wrapper template both carry the
absence of `set -e` as a commented decision so it cannot be "tidied up" later.
Exercised by `tests/test_classify.py::TestAideExitCodes`, including every
difference code 1–7 and the unmapped codes 8, 13, 99 and −1.

---

## host-baselines-were-committed-into-the-t_9d09c448

| Field | Value |
|---|---|
| **id** | `host-baselines-were-committed-into-the-t_9d09c448` |
| **summary** | Host baselines were committed into the Toolbelt repository, which would publish host addresses, kernel versions and integrity-database fingerprints if the repo is made public |
| **outcome** | A commit existed carrying two hosts' addresses, OS and kernel versions, AIDE versions, entry counts and `aide.db` fingerprints, on a branch of a repository intended for publication |
| **cause** | The baselines were treated as repo-level reference data — the same carve-out as `bin/` — which settles where they sit under PROCESS.md but never asks whether they belong in the repository at all |
| **iteration** | Resolve the baselines directory at run time from outside the repository, and refuse the run with a BoundaryError if it ever resolves inside the checkout |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#resolve-the-baselines-directory-at-run-t_6aebf499`](CHANGE_LOG.md#resolve-the-baselines-directory-at-run-t_6aebf499), fix-version `v1.0.0` |
| **occurrences** | 1 — found 2026-09-03 when the repository's publication was raised |

### Outcome (X)

Commit `89a376b` on branch `audit/host-baselines` added six files describing two
production hosts precisely enough to be useful to someone attacking them. It was
never pushed, so nothing was exposed — but the exposure was one `git push --all`
away, and the only thing preventing it was that nobody had run that command.

### Cause (Y)

The question asked was "where do baselines sit under PROCESS.md?", and
repo-level was the right answer to it. The question not asked was whether data
that describes the fleet belongs in a repository that may be published. A
convention that answers the first question fluently makes the second easy to
skip.

### Iteration (Z)

The data moved out of the repository entirely, and the tool now enforces the
split rather than documenting it: `config.resolve_baselines_dir` looks outside
the tree by default, and `config.assert_outside_repo` raises `BoundaryError`
before reading anything at all if the resolved path is inside the checkout.
The guard runs *ahead* of the directory-exists check deliberately, so pointing
Sentinel at an in-repo path fails on the boundary rather than on a missing file.

The same rule was then applied to recorded evidence: the live sweep log in
`Tests/v1.0.0/` has its host identifiers redacted, because a test result that
names the fleet reintroduces exactly what moving the baselines removed.

Proof: [`Tests/v1.0.0/boundary-guard-2026-09-03.log`](Tests/v1.0.0/boundary-guard-2026-09-03.log),
and `tests/test_config.py::TestBoundaryGuard`.

---

## the-not-installed-heuristic-matched-not_a90badf2

| Field | Value |
|---|---|
| **id** | `the-not-installed-heuristic-matched-not_a90badf2` |
| **summary** | The not-installed heuristic matched "not found" anywhere in a check's output, so debsums reporting a missing packaged file classified as debsums being absent |
| **outcome** | A real finding would have been reported as a skipped check — the sweep would say "debsums is not installed" about a host where debsums had just found a missing system binary |
| **cause** | The heuristic searched stdout and stderr together for the substring "not found", which is the shell's complaint about an absent command *and* ordinary vocabulary in a findings list |
| **iteration** | Narrow the not-installed heuristic to the shell's own complaint on stderr, so output that merely contains the phrase cannot turn a finding into a skip |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#narrow-the-not-installed-heuristic-to-th_a252c780`](CHANGE_LOG.md#narrow-the-not-installed-heuristic-to-th_a252c780), fix-version `v1.0.0` |
| **occurrences** | 1 — found 2026-09-03 while writing the classification suite, before any release |

### Outcome (X)

`debsums` reports a missing packaged file as
`debsums: missing file /usr/bin/foo (from bar package): not found`. A missing
system binary is close to the most interesting thing this tool can find. The
heuristic would have classified it as `skipped`, and a skipped check reads as
"nothing to see here".

This is the one direction the classifier must never fail in: mistaking an absent
tool for a finding costs a false alarm, mistaking a finding for an absent tool
costs the entire point of the sweep.

### Cause (Y)

Convenience. Concatenating stdout and stderr and searching the blob is shorter
than reasoning about which stream carries which claim — but the two streams are
making different statements, and only one of them is the shell's.

### Cause note

The same heuristic serves `debsums`, `rkhunter` and `chkrootkit`, so the defect
was three checks wide from one line.

### Iteration (Z)

`classify._not_installed` now accepts only exit code 127, or `command not found`
/ `: not found` **in stderr**. Locked by
`tests/test_classify.py::TestDebsums::test_missing_file_output_is_not_mistaken_for_an_absent_tool`,
which asserts that exact debsums line classifies as a finding.

---

## the-ssh-runner-had-no-way-to-name-an-ide_86ed9055

| Field | Value |
|---|---|
| **id** | `the-ssh-runner-had-no-way-to-name-an-ide_86ed9055` |
| **summary** | The SSH runner had no way to name an identity file, so a sweep authenticated as whatever key ssh selected and a working key returned Permission denied |
| **outcome** | The first live sweep failed with `Permission denied (publickey)` against a host that was reachable with a key present on the machine — a configuration gap that reads as a host problem |
| **cause** | `SshRunner` set `BatchMode` and `ConnectTimeout` but nothing else, leaving key selection to ssh's defaults; the host config had no field to express which key a sweep should use |
| **iteration** | Add an identity field to the host config and pass it to ssh as -i, so a sweep authenticates with the key it was configured with |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#add-an-identity-field-to-the-host-config_09a88e07`](CHANGE_LOG.md#add-an-identity-field-to-the-host-config_09a88e07), fix-version `v1.0.0` |
| **occurrences** | 1 — hit 2026-09-03 on the first live run against the real fleet |

### Outcome (X)

`ssh -o BatchMode=yes root@<host> hostname` returned `Permission denied
(publickey)` while the correct key sat unused in `~/.ssh/`. The sweep would have
recorded a `TransportError` — correctly classified as an error, never as clean —
but the operator's reading of that error points at the host, not at the config.
An unattended sweep that cannot authenticate is indistinguishable from one whose
hosts have all been taken away.

### Cause (Y)

Two defaults met. `BatchMode=yes` is right — an unattended sweep must fail fast
rather than block on a password prompt — but it removes the interactive fallback
that would otherwise mask the missing key. And leaving key selection implicit
assumes an agent is loaded, which is exactly what an unattended context does not
guarantee.

### Iteration (Z)

`Host.identity` in the config, `-i <expanded path>` on the ssh command line, and
`~` expanded at construction so a config written with a tilde works from cron.
Covered by `tests/test_sweep.py::TestSshIdentity`. Verified live the same day
against both hosts: [`Tests/v1.0.0/live-sweep-2026-09-03.log`](Tests/v1.0.0/live-sweep-2026-09-03.log).


---

## aide-check-was-invoked-without-config-so_7932f6e0

| Field | Value |
|---|---|
| **id** | `aide-check-was-invoked-without-config-so_7932f6e0` |
| **summary** | aide --check was invoked without --config, so on Debian and Ubuntu installs AIDE exited 17 with a missing-configuration error and the primary file-integrity check never ran |
| **outcome** | The first full production sweep returned `ERROR` for AIDE on **both** hosts. The headline check of the whole tool — the one the baselines exist for — did not execute, on either machine, on its first real run |
| **cause** | `AIDE_CMD` was the bare `aide --check`. Debian and Ubuntu ship AIDE with no compiled-in default config path, so it exits 17 (`invalid configureline`) demanding `--config`, `--before` or `--after`. Every test in the suite fed `classify_aide` an exit code directly, so nothing ever exercised the command string itself |
| **iteration** | Pass an explicit --config path to aide, configurable per host and defaulting to /etc/aide/aide.conf, and classify AIDE's configuration-error codes as an error that names the config it could not read |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#pass-an-explicit-config-path-to-aide-con_ab659d01`](CHANGE_LOG.md#pass-an-explicit-config-path-to-aide-con_ab659d01), fix-version `v1.0.0` |
| **occurrences** | 1 — 2026-09-03, first full sweep of both hosts |

### Outcome (X)

```
## <host-a> — finding
  [ERROR] aide: AIDE failed to run (exit 17)
      ERROR: missing configuration (use '--config' '--before' or '--after' ...)
```

Identically on both hosts. The classifier behaved correctly — 17 is above the error
floor, so it reported `error` and not `clean`, and the sweep verdict was not a false
all-clear. **That is the only reason this was survivable.** Had the mapping defaulted
to clean for unrecognised codes, the tool would have reported a passing integrity check
that never ran, on every host, indefinitely.

### Cause (Y)

Two things, and the second is the real one.

1. Debian/Ubuntu build AIDE without a default config path, so the bare command cannot work there.
2. **The suite could not have caught it.** Every AIDE test called `classify_aide(host, code, output)`
   directly. The commands in `checks.py` were never asserted against — so the module holding
   the one string that had to be right was the module with no test coverage at all. A test
   that supplies its own inputs to a classifier proves the classifier, and quietly proves
   nothing about what the tool actually runs.

### Iteration (Z)

`Host.aide_config` (default `/etc/aide/aide.conf`), an `aide_command()` builder, and
`AIDE_CONFIG_ERRORS` classified as an error whose message names the config path that
failed. Tests now assert on the **command string**, not only on the classification —
`test_checks.py::TestCommands`.


---

## rkhunter-evidence-captured-only-the-warn_f8ba0431

| Field | Value |
|---|---|
| **id** | `rkhunter-evidence-captured-only-the-warn_f8ba0431` |
| **summary** | rkhunter evidence captured only the Warning: line, so twenty-two changed-file warnings were reported as twenty-two identical lines naming no file |
| **outcome** | The report said `rkhunter raised 25 warning(s)` and then printed `Warning: The file properties have changed:` twenty-two times, naming nothing. Unactionable: an operator cannot tell whether the changed files are `su` and `sudo` or a pair of manual pages, and has to go to the host log to find out |
| **cause** | `classify_rootkit` filtered stdout to lines containing `Warning:`. rkhunter puts the *subject* of a property warning on the indented `File:` line that follows it, so the filter kept the header and dropped the payload |
| **iteration** | Capture the indented File: and hash lines that follow each rkhunter warning, so every warning names the file it is about |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#capture-the-indented-file-and-hash-lines_c597ad8e`](CHANGE_LOG.md#capture-the-indented-file-and-hash-lines_c597ad8e), fix-version `v1.0.0` |
| **occurrences** | 1 — 2026-09-03, first full sweep |

### Outcome (X)

The count was right and the content was empty. In the run that produced this, the 22 files
turned out to be core system binaries — `su`, `sudo`, `login`, `mount`, `cp` — changed by an
unattended upgrade the day after the rkhunter baseline was taken, and confirmed legitimate
by `debsums` passing on the same host in the same sweep. **None of that was visible in the
report.** Establishing it took a separate SSH session and a read of `/var/log/rkhunter.log`.

A finding an operator must leave the tool to interpret is a finding the tool did not
deliver. The severity was right; the report was not usable.

### Cause (Y)

Line-oriented filtering against a record-oriented format. rkhunter's property warnings are
three-line records — a `Warning:` header, then indented `File:`, `Current hash:` and
`Stored hash:` lines. A `Warning:`-only filter is guaranteed to keep exactly the line that
carries no information, for exactly the warning class that matters most.

### Iteration (Z)

`classify_rootkit` now walks the output and attaches the indented continuation lines to
their header, emitting one evidence entry per record with the file named. Covered by
`test_classify.py::TestRootkitScanners::test_property_warning_names_the_file`, which asserts
against the real three-line rkhunter format captured in this run.


---

## the-runner-s-fixed-900-second-command-ti_b1115836

| Field | Value |
|---|---|
| **id** | `the-runner-s-fixed-900-second-command-ti_b1115836` |
| **summary** | The runner's fixed 900-second command timeout is shorter than a full AIDE check on a large host, so the check is cut off and reported as an unreachable host rather than as a slow one |
| **outcome** | A corrected AIDE run on the larger host was still executing at 920 seconds when its SSH session was cut. In a sweep this would have raised `TransportError` and been recorded as **"host unreachable"** — a verdict that is not merely unhelpful but actively wrong: the host was reachable and the check was working |
| **cause** | `runner.DEFAULT_TIMEOUT = 900` was chosen before any check had been run against a real host. A full `aide --check` walks every watched file and hashes it; on 132,000 entries that exceeds 900 seconds. The timeout was a guess, and nothing in the suite could contradict it because `FakeRunner` returns instantly |
| **iteration** | Make the command timeout configurable per host and raise the sweep default to 3600 seconds, and report a timeout as its own verdict rather than as a transport failure |
| **status** | `in-progress` |
| **resolved_by** | [`CHANGE_LOG.md#make-the-command-timeout-configurable-pe_e9639fc9`](CHANGE_LOG.md#make-the-command-timeout-configurable-pe_e9639fc9), fix-version `v1.0.0` |
| **occurrences** | 1 — 2026-09-03, corrected AIDE run following the first full sweep |

### Outcome (X)

Measured on the host: `aide` at 920 seconds elapsed, 100% CPU, output file still empty
(AIDE buffers its report until the walk completes). The SSH session had already been
terminated; the remote process survived it, which is why a result was recoverable at all.

The damage is in the vocabulary. `sweep_host` catches `TransportError` and records
**"host unreachable"**, then *stops sweeping that host* — so a merely slow machine would
be reported as an unreachable one, with its remaining checks silently skipped. Of the two
ways to be wrong here, this is the worse one: it invents an infrastructure problem that
does not exist and hides the checks that would have disproved it.

### Cause (Y)

An unvalidated constant, and a test seam that could not challenge it. `FakeRunner` returns
immediately by construction, so no test — however many — could have discovered that 900
seconds is the wrong number. This is the same shape as
[`…_7932f6e0`](#aide-check-was-invoked-without-config-so_7932f6e0): the suite exercises
everything except the values that only contact with a real host can validate.

### Iteration (Z)

`Host.timeout` (default 3600), threaded through `sweep_host` to the runner, and a distinct
`TimeoutError` mapped to its own message so a slow check never again reads as an
unreachable host. The 3600 default is drawn from measurement — the larger host's full walk
— not from a second guess.
