"""The error taxonomy.

The single most important distinction in this package is **transient vs fatal**.
A poller that retries a fatal error forever looks alive while reporting nothing
(KI-05); a poller that dies on a transient error is a poller that was not there
when it mattered (KI-02). Every failure path below is classified at the point it
is raised so the engine never has to guess.
"""


class PollerError(Exception):
    """Base class for every error this package raises deliberately."""


class ConfigError(PollerError):
    """The configuration is unusable. Always fatal, always before the loop starts."""


class SourceError(PollerError):
    """Base for failures while fetching from the watched source."""


class TransientSourceError(SourceError):
    """A fetch failed in a way that is expected to succeed later.

    Timeouts, connection resets, HTTP 429, HTTP 5xx. The engine backs off and
    keeps watching.
    """


class FatalSourceError(SourceError):
    """A fetch failed in a way that will not fix itself.

    Bad credentials (401/403), a wrong URL (404), or a response whose shape the
    source cannot parse at all. The engine reports the failure through the sinks
    and exits non-zero rather than spinning silently.
    """


class SinkError(PollerError):
    """A delivery attempt failed but may succeed on a later tick."""


class FatalSinkError(SinkError):
    """A sink is misconfigured (bad token, unknown channel). Never worth retrying."""


class AlreadyRunning(PollerError):
    """Another live instance holds the lock for this poller name."""
