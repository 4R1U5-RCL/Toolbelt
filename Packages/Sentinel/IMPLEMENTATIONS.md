# Implementations — Packages/Sentinel

How Sentinel is applied. Each entry cites its form in
[`TEMPLATES.md`](TEMPLATES.md) (PROCESS.md §3, reciprocal pair).

**Append-only** (PROCESS.md §5.2). A new way of applying the tool appends; it
does not replace an existing one.

| Id | Use case | Template |
|---|---|---|
| [imp-scheduled-sweep](#imp-scheduled-sweep) | Unattended sweep on a timer, reporting only when something needs a human | [tpl-cron-wrapper](TEMPLATES.md#tpl-cron-wrapper) |
| [imp-fleet-config](#imp-fleet-config) | Describing a fleet to Sentinel without putting the fleet in the repo | [tpl-hosts-json](TEMPLATES.md#tpl-hosts-json) |
| [imp-rebaseline](#imp-rebaseline) | Re-baselining a host after a legitimate change, and keeping the record honest | [tpl-rebaseline](TEMPLATES.md#tpl-rebaseline) |

---

## imp-scheduled-sweep

**Use case.** A sweep that runs on a timer and stays silent when there is
nothing to say, because an alert that fires on every run is an alert nobody
reads.

**Shape.** The wrapper runs `sentinel sweep --json`, keys on the exit code, and
notifies only on 1 or 2. It captures the report to a file either way, so a quiet
week still leaves evidence that the sweep ran — silence from a scheduler is
ambiguous between "clean" and "not running", and that ambiguity is how integrity
monitoring dies.

**The trap this template exists to avoid.** The wrapper must not run under
`set -e`. Sentinel exits non-zero when it *finds* something, exactly as `aide
--check` does, so `set -e` kills the wrapper at the moment the tool works. See
[`KNOWN_ISSUES.md#aide-check-exits-non-zero-when-it-succee_d4ecdc86`](KNOWN_ISSUES.md#aide-check-exits-non-zero-when-it-succee_d4ecdc86).

**Prove it runs before you trust the schedule.** A scheduled sweep that errors is
indistinguishable from one that is clean if nobody reads the report, and the first
production run of this tool returned `ERROR` for AIDE on every host because of a
missing `--config`. Run it by hand once per host and read the output before wiring
it to a timer.

**Cadence.** Daily for `aide_db_fingerprint` (one `sha256sum` per host, seconds).
Weekly for the full sweep — `aide --check` over ~88,000 entries plus `debsums`
plus `rkhunter` is minutes of CPU, and one of the hosts this was built for holds
4.4 GB of a 7.9 GB machine in a Java process.

**Form:** [tpl-cron-wrapper](TEMPLATES.md#tpl-cron-wrapper).

---

## imp-fleet-config

**Use case.** Telling Sentinel which hosts to sweep, which checks each one
takes, and which key to use — without any of that entering the repository.

**Shape.** A single `hosts.json` in the baselines directory, alongside the
per-host records it refers to. Host `name` must match the baseline record
directory name; that is how a host's `aide.db.sha256` is found.

**Why it lives there and not here.** It names addresses and identity-file paths.
The repo may be published; the baselines directory is not. Sentinel refuses to
load config from inside the checkout rather than trusting anyone to remember —
`config.assert_outside_repo`.

**Form:** [tpl-hosts-json](TEMPLATES.md#tpl-hosts-json).

---

## imp-rebaseline

**Use case.** A host was legitimately changed — a distribution upgrade, a
package install, a deliberate config edit — so its baseline no longer describes
it and every subsequent sweep would report a finding.

**Shape.** Re-run `aideinit`, promote the new database, take its sha256, and
update the off-host record **in the same change** with a note naming the cause.

**Why the note is not optional.** A mismatch means one of two things: legitimate
re-baselining whose record was not updated, or a replaced database. If stale
records are common, the first explanation is always available and the check
stops meaning anything. The note is what keeps a mismatch a finding.

**Form:** [tpl-rebaseline](TEMPLATES.md#tpl-rebaseline).
