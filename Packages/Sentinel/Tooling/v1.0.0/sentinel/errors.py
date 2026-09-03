"""Sentinel's error vocabulary.

Every error a run can stop on is one of these. They exist so a caller can tell
a *configuration* problem (fix the setup) from a *boundary* problem (the run
was refused on purpose) from a *transport* problem (the host was unreachable).
"""


class SentinelError(Exception):
    """Base for every error Sentinel raises deliberately."""


class ConfigError(SentinelError):
    """The host config or baselines directory is missing, unreadable or malformed."""


class BoundaryError(SentinelError):
    """A run was refused because it would place host data inside the repository.

    This is not a failure of the sweep. It is the guard in `config` doing its
    job: baselines name hosts, IPs and kernel versions, and this repository may
    be published. See README.md, "Why the baselines are not in this repo".
    """


class TransportError(SentinelError):
    """A host could not be reached, or the remote command could not be started."""


class CheckTimeout(SentinelError):
    """A check overran its time limit.

    Deliberately NOT a TransportError. A slow check is one failed check on a
    reachable host; a transport failure means the host is gone. Conflating them
    invents an infrastructure fault and — because a transport failure ends the
    host's sweep — hides every check that would have disproved it. See
    KNOWN_ISSUES.md#the-runner-s-fixed-900-second-command-ti_b1115836.
    """
