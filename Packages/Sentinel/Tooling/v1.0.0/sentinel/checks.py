"""The checks themselves: what command each one runs, and where it sends the
output for classification.

Deliberately thin. A check knows its command line and nothing about verdicts;
`classify` knows verdicts and nothing about SSH. That split is what lets the
suite exercise every verdict path without a host.

All of these read root-owned paths. Point the host's `target` at a root-capable
account rather than teaching Sentinel to escalate privilege.
"""

from __future__ import annotations

from pathlib import Path

from . import classify
from .classify import CheckResult
from .config import Host, SweepConfig
from .errors import TransportError
from .runner import Runner

# `aide --check` is run WITHOUT any `set -e` wrapper and its exit code is read
# rather than trusted to be zero. See classify.classify_aide.
AIDE_CMD = "aide --check"
DEBSUMS_CMD = "debsums -c"
RKHUNTER_CMD = "rkhunter --check --skip-keypress --report-warnings-only"
CHKROOTKIT_CMD = "chkrootkit -q"


def run_aide(runner: Runner, host: Host, config: SweepConfig) -> CheckResult:
    result = runner.run(AIDE_CMD)
    return classify.classify_aide(host.name, result.exit_code, result.stdout, result.stderr)


def run_aide_db_fingerprint(runner: Runner, host: Host, config: SweepConfig) -> CheckResult:
    recorded = read_recorded_fingerprint(config.fingerprint_path(host))
    result = runner.run(f"sha256sum {host.aide_db}")
    observed = result.stdout if result.exit_code == 0 else None
    return classify.classify_fingerprint(host.name, observed, recorded)


def run_debsums(runner: Runner, host: Host, config: SweepConfig) -> CheckResult:
    result = runner.run(DEBSUMS_CMD)
    return classify.classify_debsums(host.name, result.exit_code, result.stdout, result.stderr)


def run_rkhunter(runner: Runner, host: Host, config: SweepConfig) -> CheckResult:
    result = runner.run(RKHUNTER_CMD)
    return classify.classify_rootkit(host.name, "rkhunter", result.exit_code,
                                     result.stdout, result.stderr)


def run_chkrootkit(runner: Runner, host: Host, config: SweepConfig) -> CheckResult:
    result = runner.run(CHKROOTKIT_CMD)
    return classify.classify_rootkit(host.name, "chkrootkit", result.exit_code,
                                     result.stdout, result.stderr)


CHECKS = {
    "aide": run_aide,
    "aide_db_fingerprint": run_aide_db_fingerprint,
    "debsums": run_debsums,
    "rkhunter": run_rkhunter,
    "chkrootkit": run_chkrootkit,
}


def read_recorded_fingerprint(path: Path) -> str | None:
    """The off-host sha256 record for a host's aide.db, or None if unrecorded."""
    if not path.is_file():
        return None
    text = path.read_text().strip()
    return text or None


def sweep_host(runner: Runner, host: Host, config: SweepConfig) -> list[CheckResult]:
    """Run every check configured for one host.

    A transport failure ends that host's sweep and is recorded as an error —
    never as an absence of findings. An unreachable host is not a clean host,
    and the report must not be able to imply that it is.
    """
    results: list[CheckResult] = []
    for name in host.checks:
        try:
            results.append(CHECKS[name](runner, host, config))
        except TransportError as exc:
            results.append(CheckResult(host.name, name, classify.ERROR,
                                       "host unreachable", detail=str(exc)))
            break
    return results
