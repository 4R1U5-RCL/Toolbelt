"""Where the sweep gets its hosts and its baselines — and the guard that keeps
those two things out of this repository.

The split this module enforces is the whole publishing story for Sentinel:

    the METHOD is in the repo        — checks, classification, config fragment
    the DATA is not                  — hostnames, IPs, kernels, db fingerprints

A baseline record names a host, its address, its kernel version and the exact
fingerprint of its integrity database. That is a reconnaissance package. This
repository may be made public. So the baselines directory is resolved at run
time from outside the tree, and `assert_outside_repo` refuses the run if anyone
ever points it back inside.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .errors import BoundaryError, ConfigError

ENV_BASELINES = "SENTINEL_BASELINES_DIR"
DEFAULT_BASELINES = "~/.claude/data/baselines"

# Every check Sentinel knows how to run. A host may select any subset.
KNOWN_CHECKS = ("aide", "aide_db_fingerprint", "debsums", "rkhunter", "chkrootkit")


@dataclass(frozen=True)
class Host:
    """One host in the sweep."""

    name: str
    target: str
    checks: tuple[str, ...]
    aide_db: str = "/var/lib/aide/aide.db"
    aide_config: str = "/etc/aide/aide.conf"
    timeout: int = 3600
    local: bool = False
    identity: str = ""
    notes: str = ""


@dataclass(frozen=True)
class SweepConfig:
    baselines_dir: Path
    hosts: tuple[Host, ...] = field(default_factory=tuple)

    def host(self, name: str) -> Host:
        for candidate in self.hosts:
            if candidate.name == name:
                return candidate
        known = ", ".join(h.name for h in self.hosts) or "none configured"
        raise ConfigError(f"no host named {name!r} in the sweep config (have: {known})")

    def fingerprint_path(self, host: Host) -> Path:
        return self.baselines_dir / host.name / "aide.db.sha256"


def repo_root(start: Path | None = None) -> Path | None:
    """The Toolbelt checkout this code is running from, or None if detached.

    Identified by PROCESS.md at the root — not by `.git`, because a worktree or
    an exported copy may have neither, and the rule we are enforcing is about
    the repository's *contents*, not its git metadata.
    """
    here = (start or Path(__file__)).resolve()
    for parent in [here, *here.parents]:
        if (parent / "PROCESS.md").is_file():
            return parent
    return None


def assert_outside_repo(path: Path, root: Path | None = None) -> None:
    """Refuse a baselines directory that sits inside the Toolbelt checkout.

    Raises BoundaryError rather than warning. A warning would be ignored on the
    one run that mattered, and the cost of getting this wrong is publishing the
    fleet's integrity fingerprints.
    """
    root = root if root is not None else repo_root()
    if root is None:
        return
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return
    raise BoundaryError(
        f"baselines directory {resolved} is inside the Toolbelt repo at {root}. "
        "Baselines name hosts, addresses and kernel versions and this repo may be "
        f"published; keep them outside it (default: {DEFAULT_BASELINES})."
    )


def resolve_baselines_dir(explicit: str | None = None, environ: dict | None = None) -> Path:
    """Resolve the baselines directory: argument, then env, then default."""
    environ = environ if environ is not None else os.environ
    raw = explicit or environ.get(ENV_BASELINES) or DEFAULT_BASELINES
    return Path(raw).expanduser()


def load(explicit: str | None = None, environ: dict | None = None,
         root: Path | None = None) -> SweepConfig:
    """Load hosts.json from the resolved baselines directory."""
    baselines = resolve_baselines_dir(explicit, environ)
    assert_outside_repo(baselines, root)

    if not baselines.is_dir():
        raise ConfigError(
            f"baselines directory {baselines} does not exist. Sentinel ships the "
            "method, not the data — create it and add hosts.json (see "
            "examples/hosts.example.json)."
        )

    manifest = baselines / "hosts.json"
    if not manifest.is_file():
        raise ConfigError(f"no hosts.json in {baselines} (see examples/hosts.example.json)")

    try:
        raw = json.loads(manifest.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{manifest} is not valid JSON: {exc}") from exc

    entries = raw.get("hosts")
    if not isinstance(entries, list) or not entries:
        raise ConfigError(f"{manifest} has no 'hosts' array")

    hosts = []
    for index, entry in enumerate(entries):
        hosts.append(_parse_host(entry, index, manifest))
    return SweepConfig(baselines_dir=baselines, hosts=tuple(hosts))


def _parse_host(entry: dict, index: int, manifest: Path) -> Host:
    where = f"{manifest} hosts[{index}]"
    if not isinstance(entry, dict):
        raise ConfigError(f"{where} is not an object")

    name = entry.get("name")
    if not name:
        raise ConfigError(f"{where} has no 'name'")

    local = bool(entry.get("local", False))
    target = entry.get("target", "")
    if not target and not local:
        raise ConfigError(f"{where} ({name}) has no 'target' and is not marked local")

    checks = tuple(entry.get("checks") or ("aide", "aide_db_fingerprint"))
    unknown = [c for c in checks if c not in KNOWN_CHECKS]
    if unknown:
        raise ConfigError(
            f"{where} ({name}) names unknown check(s) {unknown}; "
            f"known: {', '.join(KNOWN_CHECKS)}"
        )

    return Host(
        name=name,
        target=target,
        checks=checks,
        aide_db=entry.get("aide_db", "/var/lib/aide/aide.db"),
        aide_config=entry.get("aide_config", "/etc/aide/aide.conf"),
        timeout=int(entry.get("timeout", 3600)),
        local=local,
        identity=entry.get("identity", ""),
        notes=entry.get("notes", ""),
    )
