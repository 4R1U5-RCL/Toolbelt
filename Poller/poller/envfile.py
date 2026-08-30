"""Reading credentials out of a `.env` file without sourcing it.

Sourcing a shared `.env` into the poller's own environment pollutes the process
with dozens of unrelated keys and makes an accidental `env` dump catastrophic.
Instead this module parses the file, hands back only the names the config asked
for, and registers each one with the redactor.

Format handled: `KEY=value`, `export KEY=value`, `KEY="value"`, `KEY='value'`,
blank lines, and `#` comments. Values are taken verbatim after the first `=`.
"""

from __future__ import annotations

import os
import re
from typing import Dict, Mapping, Optional

from .errors import ConfigError
from .log import get_logger, register_secret

_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")


def read_env_file(path: Optional[str]) -> Dict[str, str]:
    """Parse a dotenv file into a dict. A missing path yields `{}`.

    Never raises on a malformed line — a poller must not refuse to start
    because an unrelated line of a shared `.env` is odd.
    """
    if not path:
        return {}
    expanded = os.path.expanduser(path)
    if not os.path.isfile(expanded):
        get_logger().warning("env file not found, falling back to process env: %s", expanded)
        return {}

    values: Dict[str, str] = {}
    with open(expanded, "r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            if not raw.strip() or raw.lstrip().startswith("#"):
                continue
            match = _LINE.match(raw)
            if not match:
                continue
            key, value = match.group(1), match.group(2)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key] = value
    return values


class EnvResolver:
    """Resolves `@env:NAME` references against the dotenv file, then os.environ.

    Precedence is file-then-process on purpose: `/studio/.env` is the single
    source of truth for this system, and a stale exported shell variable
    silently overriding it has burned us before.
    """

    REF_PREFIX = "@env:"

    def __init__(self, env_file: Optional[str] = None, environ: Optional[Mapping[str, str]] = None):
        self.env_file = env_file
        self._file_values = read_env_file(env_file)
        self._environ = os.environ if environ is None else environ

    def get(self, name: str, required: bool = True) -> Optional[str]:
        """Return the value of `name`, registering it as a secret.

        Raises ConfigError when required and absent — at startup, where it is
        cheap to fix, rather than six hours in at the moment of delivery.
        """
        value = self._file_values.get(name) or self._environ.get(name)
        if not value:
            if required:
                raise ConfigError(
                    "required environment value {0!r} not found in {1} or the process "
                    "environment".format(name, self.env_file or "<no env file>")
                )
            return None
        register_secret(value)
        return value

    def resolve(self, value, required: bool = True):
        """Expand a single config value: `@env:NAME` -> the secret, else verbatim."""
        if isinstance(value, str) and value.startswith(self.REF_PREFIX):
            return self.get(value[len(self.REF_PREFIX):].strip(), required=required)
        return value

    def resolve_mapping(self, mapping: Optional[Mapping[str, str]]) -> Dict[str, str]:
        """Expand every `@env:NAME` in a flat mapping (e.g. request headers)."""
        if not mapping:
            return {}
        return {key: str(self.resolve(val)) for key, val in mapping.items()}

    def present(self, name: str) -> bool:
        """True if `name` has a non-empty value. Never returns the value itself."""
        return bool(self._file_values.get(name) or self._environ.get(name))
