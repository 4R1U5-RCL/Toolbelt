"""Turning raw check output into a verdict.

This module is the part of Sentinel worth copying. Everything else is plumbing;
this is where the knowledge lives — what each tool's exit codes actually mean,
and which of them mean "I found something" rather than "I broke".

The load-bearing fact, learned the hard way on a production host on 2026-09-01:

    aide --check EXITS NON-ZERO WHEN IT SUCCEEDS AT DETECTING A CHANGE.

Under `set -e` a wrapper therefore dies at exactly the moment the tool works.
The bug is silent in the only case you care about. See
KNOWN_ISSUES.md#aide-check-exits-non-zero-when-it-succee_d4ecdc86.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- verdicts, worst last ---------------------------------------------------
CLEAN = "clean"
SKIPPED = "skipped"
UNBASELINED = "unbaselined"
ERROR = "error"
FINDING = "finding"

SEVERITY = {CLEAN: 0, SKIPPED: 1, UNBASELINED: 2, ERROR: 3, FINDING: 4}

# --- AIDE's exit code is a bitmask over what it found ------------------------
AIDE_NEW = 1
AIDE_REMOVED = 2
AIDE_CHANGED = 4
AIDE_DIFF_BITS = AIDE_NEW | AIDE_REMOVED | AIDE_CHANGED  # 7

# 14 and up are AIDE's own error codes (write error, invalid argument,
# unimplemented function, invalid config line, IO error, version mismatch).
AIDE_ERROR_FLOOR = 14

AIDE_BIT_LABELS = ((AIDE_NEW, "new files"),
                   (AIDE_REMOVED, "removed files"),
                   (AIDE_CHANGED, "changed files"))


@dataclass
class CheckResult:
    """One check on one host, classified."""

    host: str
    check: str
    verdict: str
    headline: str
    detail: str = ""
    exit_code: int | None = None
    evidence: list[str] = field(default_factory=list)

    @property
    def severity(self) -> int:
        return SEVERITY[self.verdict]


def describe_aide_bits(code: int) -> str:
    """Decompose an AIDE difference code into the categories it stands for."""
    found = [label for bit, label in AIDE_BIT_LABELS if code & bit]
    return ", ".join(found) if found else "differences"


def classify_aide(host: str, exit_code: int, stdout: str, stderr: str = "") -> CheckResult:
    """Classify an `aide --check` run.

    0            -> clean
    1..7         -> finding, decomposed from the bitmask
    >= 14        -> error (AIDE itself failed; says nothing about the host)
    anything else-> error, because an unmapped code must never read as clean
    """
    if exit_code == 0:
        return CheckResult(host, "aide", CLEAN, "no watched file changed since baseline",
                           exit_code=exit_code)

    if 0 < exit_code <= AIDE_DIFF_BITS:
        what = describe_aide_bits(exit_code)
        return CheckResult(
            host, "aide", FINDING,
            f"AIDE reports {what}",
            detail=_summarise_aide(stdout),
            exit_code=exit_code,
            evidence=_entry_lines(stdout),
        )

    if exit_code >= AIDE_ERROR_FLOOR:
        return CheckResult(host, "aide", ERROR,
                           f"AIDE failed to run (exit {exit_code})",
                           detail=(stderr or stdout).strip(), exit_code=exit_code)

    return CheckResult(host, "aide", ERROR,
                       f"unmapped AIDE exit code {exit_code} — treated as an error",
                       detail=(stderr or stdout).strip(), exit_code=exit_code)


def classify_fingerprint(host: str, observed: str | None, recorded: str | None) -> CheckResult:
    """Compare the on-host aide.db hash against the off-host record.

    This is the tamper-evidence check, and it is the reason a copy of the hash
    lives off the host at all: a compromised host can rewrite its own database,
    but it cannot rewrite the record kept elsewhere.

    A mismatch is NOT a verdict of compromise. Re-baselining after a legitimate
    patch produces exactly the same signal. It is a finding — something that
    must be explained — and the report says so in those words.
    """
    if recorded is None:
        return CheckResult(host, "aide_db_fingerprint", UNBASELINED,
                           "no recorded fingerprint for this host",
                           detail="Nothing to compare against. Record the current "
                                  "aide.db sha256 in the baselines directory.")
    if observed is None:
        return CheckResult(host, "aide_db_fingerprint", ERROR,
                           "could not read aide.db on the host",
                           detail="The database is missing or unreadable.")

    observed = observed.strip().split()[0] if observed.strip() else ""
    recorded = recorded.strip().split()[0] if recorded.strip() else ""

    if observed == recorded:
        return CheckResult(host, "aide_db_fingerprint", CLEAN,
                           "aide.db matches its off-host record")

    return CheckResult(
        host, "aide_db_fingerprint", FINDING,
        "aide.db does NOT match its off-host record",
        detail=("Either the host was legitimately re-baselined and the record was "
                "not updated, or the database was replaced. Neither is a verdict "
                "on its own — but an unexplained mismatch is a finding, not noise."),
        evidence=[f"recorded: {recorded}", f"observed: {observed}"],
    )


def classify_debsums(host: str, exit_code: int, stdout: str, stderr: str = "") -> CheckResult:
    """Classify `debsums -c` — every packaged file against the distro's checksums.

    Unlike AIDE this needs no prior baseline: the reference is the distribution's
    own record, so it speaks to a host that was never baselined.
    """
    if _not_installed(exit_code, stdout, stderr):
        return CheckResult(host, "debsums", SKIPPED, "debsums is not installed",
                           exit_code=exit_code)

    changed = [line.strip() for line in stdout.splitlines() if line.strip()]
    if exit_code == 0 and not changed:
        return CheckResult(host, "debsums", CLEAN,
                           "every packaged file matches the distribution checksum",
                           exit_code=exit_code)

    return CheckResult(host, "debsums", FINDING,
                       f"{len(changed)} packaged file(s) differ from the distribution",
                       detail="A modified packaged file is expected for some config "
                              "files and unexpected for a binary.",
                       exit_code=exit_code, evidence=changed[:40])


def classify_rootkit(host: str, tool: str, exit_code: int, stdout: str,
                     stderr: str = "") -> CheckResult:
    """Classify rkhunter / chkrootkit — the signature-based half.

    Both report findings in their output rather than reliably in an exit code,
    so the output is what gets read. Signature matching catches known implants
    and nothing else; a competent one defeats it. The report never upgrades a
    clean result here into a statement that the host is clean.
    """
    if _not_installed(exit_code, stdout, stderr):
        return CheckResult(host, tool, SKIPPED, f"{tool} is not installed",
                           exit_code=exit_code)

    warnings = [line.strip() for line in stdout.splitlines()
                if "Warning:" in line or "INFECTED" in line]
    if warnings:
        return CheckResult(host, tool, FINDING,
                           f"{tool} raised {len(warnings)} warning(s)",
                           exit_code=exit_code, evidence=warnings[:40])

    if exit_code not in (0, 1):
        return CheckResult(host, tool, ERROR, f"{tool} failed to run (exit {exit_code})",
                           detail=(stderr or stdout).strip(), exit_code=exit_code)

    return CheckResult(host, tool, CLEAN, f"{tool} matched no known signature",
                       exit_code=exit_code)


def worst(results: list[CheckResult]) -> str:
    """The host or sweep verdict: the most severe result in the set."""
    if not results:
        return SKIPPED
    return max(results, key=lambda r: r.severity).verdict


def _not_installed(exit_code: int, stdout: str, stderr: str) -> bool:
    """Is this "the tool is absent" rather than "the tool found something"?

    Only the shell's own complaint counts, and only from stderr. Matching
    "not found" anywhere in stdout would misread debsums listing a missing
    packaged file as debsums being uninstalled — turning a real finding into
    a skip, which is the one direction this must never fail in.
    """
    if exit_code == 127:
        return True
    complaint = stderr.lower()
    return "command not found" in complaint or ": not found" in complaint


def _entry_lines(stdout: str) -> list[str]:
    """Pull AIDE's per-file lines out of a check report, capped for readability."""
    lines = [line.rstrip() for line in stdout.splitlines()
             if line.startswith(("File:", "Directory:", "  ", "Added", "Removed", "Changed"))]
    return [line for line in lines if line.strip()][:40]


def _summarise_aide(stdout: str) -> str:
    for line in stdout.splitlines():
        if "Total number of entries" in line or "Number of entries" in line:
            return line.strip()
    return ""
