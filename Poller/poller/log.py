"""Logging that cannot leak a secret.

Every credential the package reads is registered here, and the formatter
replaces registered values with `***` on the way out. This is belt-and-braces:
no code path deliberately logs a token, but a poller writes an unattended log
for hours and one careless `%s` of a request header would be a real leak
(KI-11).
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Iterable, Optional

_MASK = "***"
_forced_level = None
_MIN_SECRET_LEN = 6  # below this, masking would scrub ordinary words
_secrets = set()


def register_secret(value: Optional[str]) -> None:
    """Mark a value as never-printable. Safe to call repeatedly."""
    if value and len(value) >= _MIN_SECRET_LEN:
        _secrets.add(value)


def registered_secrets() -> Iterable[str]:
    return tuple(_secrets)


def scrub(text: str) -> str:
    """Replace every registered secret occurring in `text`."""
    for secret in _secrets:
        if secret in text:
            text = text.replace(secret, _MASK)
    return text


class _ScrubbingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return scrub(super().format(record))

    def formatException(self, ei) -> str:  # exception text can carry a URL
        return scrub(super().formatException(ei))


def set_level(level: Optional[int]) -> None:
    """Pin the log level, overriding `configure`.

    For hosts that embed the engine (and for the test suite) — otherwise the
    next `configure` call, e.g. from the CLI, would reset a deliberate choice.
    """
    global _forced_level
    _forced_level = level


def configure(verbose: bool = False, stream=None, logfile: Optional[str] = None) -> logging.Logger:
    """Configure and return the package logger.

    Logs go to stderr so stdout stays clean for machine-readable command output
    (`poller status --json`). An optional file handler gives an unattended run
    an audit trail that survives a lost terminal.
    """
    logger = logging.getLogger("poller")
    logger.setLevel(_forced_level if _forced_level is not None
                    else (logging.DEBUG if verbose else logging.INFO))
    logger.handlers = []  # idempotent: re-configuring must not double-log
    logger.propagate = False

    fmt = _ScrubbingFormatter(
        fmt="%(asctime)s %(levelname)-5s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    fmt.converter = time.gmtime  # timestamps are UTC, always (KI-13)

    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(fmt)
    logger.addHandler(handler)

    if logfile:
        file_handler = logging.FileHandler(logfile, encoding="utf-8")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("poller")
