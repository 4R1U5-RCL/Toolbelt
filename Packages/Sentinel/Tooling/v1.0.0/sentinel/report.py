"""Rendering a sweep into something a human reads and a machine can store.

The report has one rule beyond formatting, and it is a claim about honesty
rather than layout: **a clean sweep is never rendered as "the host is clean".**

AIDE proves that no watched file changed since the baseline was taken. If
something was already present when the baseline was taken, the baseline
enshrined it. debsums and signature scanning speak without a prior baseline and
are real evidence — and a competent implant defeats all three. Every rendered
report carries that caveat, because a report that reads as an all-clear will be
believed as one.
"""

from __future__ import annotations

import json

from .classify import CLEAN, ERROR, FINDING, SKIPPED, UNBASELINED, CheckResult, worst

MARKS = {CLEAN: "ok", FINDING: "FINDING", ERROR: "ERROR",
         SKIPPED: "skipped", UNBASELINED: "unbaselined"}

CAVEAT = (
    "A clean result proves no watched file changed since the baseline was taken. "
    "It does not prove the host is clean: a first baseline enshrines whatever was "
    "already there, and a competent implant defeats file-integrity, distribution "
    "checksums and signature scanning alike."
)


def render_text(results: list[CheckResult], taken_at: str = "") -> str:
    """A plain-text sweep report, grouped by host."""
    lines = ["Sentinel — host integrity sweep"]
    if taken_at:
        lines.append(f"Run: {taken_at}")
    lines.append(f"Verdict: {worst(results).upper()}")
    lines.append("")

    for host in _hosts_in_order(results):
        host_results = [r for r in results if r.host == host]
        lines.append(f"## {host} — {worst(host_results)}")
        for result in host_results:
            lines.append(f"  [{MARKS[result.verdict]}] {result.check}: {result.headline}")
            if result.detail:
                lines.append(f"      {result.detail}")
            for item in result.evidence:
                lines.append(f"      | {item}")
        lines.append("")

    lines.append(f"Note: {CAVEAT}")
    return "\n".join(lines)


def render_json(results: list[CheckResult], taken_at: str = "") -> str:
    payload = {
        "verdict": worst(results),
        "taken_at": taken_at,
        "caveat": CAVEAT,
        "results": [
            {
                "host": r.host,
                "check": r.check,
                "verdict": r.verdict,
                "headline": r.headline,
                "detail": r.detail,
                "exit_code": r.exit_code,
                "evidence": r.evidence,
            }
            for r in results
        ],
    }
    return json.dumps(payload, indent=2)


def exit_code_for(results: list[CheckResult]) -> int:
    """0 clean, 1 something needs a human, 2 a check could not be run.

    Findings outrank errors: a sweep that both errored and found something must
    exit as a finding, or a cron wrapper watching for 1 will miss it.
    """
    verdict = worst(results)
    if verdict == FINDING:
        return 1
    if verdict in (ERROR,):
        return 2
    if verdict in (UNBASELINED,):
        return 1
    return 0


def _hosts_in_order(results: list[CheckResult]) -> list[str]:
    seen: list[str] = []
    for result in results:
        if result.host not in seen:
            seen.append(result.host)
    return seen
