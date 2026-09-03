# Packages/Sentinel

**Current version: `v1.0.0`** — code at [`Tooling/v1.0.0/`](Tooling/v1.0.0/),
recorded results at [`Tests/v1.0.0/`](Tests/v1.0.0/).

Host integrity sweep. Runs file-integrity, distribution-checksum and
signature-based rootkit checks across a set of configured hosts, classifies what
comes back, and reports one verdict per host.

Sentinel is the answer to a narrow question — *has anything on these machines
changed that I did not change?* — and it is careful never to answer a wider one.

## The split that makes this publishable

```
the METHOD is in this repo      checks, exit-code semantics, classification, report
the DATA is not                 hostnames, addresses, kernels, aide.db fingerprints
```

A baseline record names a host, its address, its kernel version and the exact
fingerprint of its integrity database. That is a reconnaissance package for the
fleet it describes. So Sentinel ships **no baselines at all**: it resolves them at
run time from a directory outside the repository, and
[`config.assert_outside_repo`](Tooling/v1.0.0/sentinel/config.py) **refuses the
run** — `BoundaryError`, exit 2 — if that directory ever resolves inside the
checkout. Proof it does:
[`Tests/v1.0.0/boundary-guard-2026-09-03.log`](Tests/v1.0.0/boundary-guard-2026-09-03.log).

Resolution order: `--baselines DIR`, then `$SENTINEL_BASELINES_DIR`, then
`~/.claude/data/baselines`.

## Use

```bash
cd Tooling/v1.0.0
./bin/sentinel hosts                                  # what is configured
./bin/sentinel sweep --dry-run                        # what would run; executes nothing
./bin/sentinel sweep                                  # the full sweep
./bin/sentinel sweep --only aide_db_fingerprint       # one cheap check across the fleet
./bin/sentinel sweep --host n8n.example --json        # one host, machine-readable
```

Exit codes are the interface for a scheduler: **0** clean, **1** something needs a
human (a finding, or a host with no baseline), **2** a check could not be run at
all. A finding outranks an error, so a sweep that both errored and found
something exits 1 — a wrapper watching for 1 cannot miss it.

**Cost.** A full sweep is minutes to tens of minutes per host: `aide --check`
hashes every watched file. Measured at ~15 min for 88,000 entries and longer for
132,000. `--only aide_db_fingerprint` is one `sha256sum` and takes seconds — use
it for the frequent check and reserve the full sweep for a weekly slot.

## The checks

| Check | Command | Needs a prior baseline? |
|---|---|---|
| `aide` | `aide --config <aide_config> --check` | yes |
| `aide_db_fingerprint` | `sha256sum <aide_db>` vs the off-host record | yes |
| `debsums` | `debsums -c` | **no** — the distribution's own checksums are the reference |
| `rkhunter` | `rkhunter --check --skip-keypress --report-warnings-only` | no |
| `chkrootkit` | `chkrootkit -q` | no |

The `--config` is not optional: Debian and Ubuntu compile AIDE with no default
config path, so a bare `aide --check` exits 17 and checks nothing. Set
`aide_config` per host if yours is not at `/etc/aide/aide.conf`.

`aide_db_fingerprint` is the tamper-evidence check and the reason a copy of the
hash lives off the host at all: **a compromised host can rewrite its own
database, but it cannot rewrite the record kept elsewhere.** A mismatch is not a
verdict — re-baselining after a legitimate patch produces the identical signal —
so it is reported as a finding to be explained, in those words.

## What a clean sweep does and does not mean

Every report, including a clean one, carries this and it is not boilerplate:

> A clean result proves no watched file changed since the baseline was taken. It
> does not prove the host is clean: a first baseline enshrines whatever was
> already there, and a competent implant defeats file-integrity, distribution
> checksums and signature scanning alike.

The two hosts this was built against were baselined on 2026-09-01 after running
4 days and 2.5 weeks respectively with no security tooling installed. A first
baseline records whatever state a host is already in. `debsums` and the
signature scanners are the checks that speak *without* a prior baseline, which
is why they are in the default set.

## Setting a host up

1. Install AIDE, tune the config (see the exclude fragment in your baselines
   directory), and take the first baseline.
2. Record the `aide.db` sha256 and a short host record **in the baselines
   directory, not here**.
3. Add the host to `hosts.json` there —
   [`Tooling/v1.0.0/examples/hosts.example.json`](Tooling/v1.0.0/examples/hosts.example.json)
   is the shape.
4. `./bin/sentinel sweep --host <name> --dry-run`, then for real.

Re-baseline after any legitimate change to system binaries or config, and update
the recorded hash **in the same change**, with a note saying what caused it. A
baseline whose hash is stale is worse than none, because it trains the reader to
ignore mismatches.

**On a host running unattended upgrades, that is not an occasional event.** Both
hosts this was built against auto-upgrade daily, and both baselines went stale
within 24 hours of being taken: a security update replaced `util-linux`,
`coreutils`, `login` and `openssl`, and the next sweep reported 1,843 changed
entries — every one of them legitimate, and every one of them indistinguishable
from a real finding *in the report*. Corroborating with `debsums` is what
separates the two, since it compares against the distribution rather than
against a local baseline. Plan for this before scheduling a sweep, or the sweep
will cry wolf daily and be ignored inside a fortnight.

## Tests

Declared runner: **`./run-tests.sh`** (`python3 -m unittest`, stdlib only).

The suite drives the whole sweep through `runner.FakeRunner`, so every verdict
path — including an unreachable host and an unmapped exit code — is exercised
without a host, a key or a network. Results:
[`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md).

## Files

| Path | Holds |
|---|---|
| [`README.md`](README.md) | This file |
| [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) | The three ways this is applied, each citing its template |
| [`TEMPLATES.md`](TEMPLATES.md) | The application forms themselves |
| [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) | Four issues, all found building v1.0.0 |
| [`CHANGE_LOG.md`](CHANGE_LOG.md) | The iterations that answered them |
| [`Tooling/v1.0.0/`](Tooling/v1.0.0/) | The code at v1.0.0, tests inside it |
| [`Tests/v1.0.0/`](Tests/v1.0.0/) | Recorded results: suite run, boundary guard, live sweep, Track B |

## History

Sentinel replaces `Workflows/Audit`, a reserved name that carried one sentence
and no implementation. That directory is retired at `v1.1.0` and points here.
