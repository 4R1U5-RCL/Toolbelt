"""The command-execution seam.

Every check runs commands somewhere. Isolating that behind one interface is
what makes the classification logic testable without a host, an SSH key or a
network: the suite drives `FakeRunner` with recorded output, and the same
classifier reads it.

The seam returns the exit code rather than raising on non-zero, and that is
load-bearing. `aide --check` exits NON-ZERO when it succeeds at detecting a
change; a runner that raised on non-zero would turn every real finding into a
crash. See KNOWN_ISSUES.md#aide-check-exits-non-zero-when-it-succee_d4ecdc86.
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import TransportError

DEFAULT_TIMEOUT = 900


@dataclass(frozen=True)
class CommandResult:
    """What running one command produced. Never raises on a non-zero code."""

    command: str
    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class Runner:
    """Interface. A runner executes a shell command and reports what happened."""

    name = "runner"

    def run(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> CommandResult:
        raise NotImplementedError


class LocalRunner(Runner):
    """Runs commands on this machine. Used for a sweep of the local host."""

    name = "local"

    def run(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> CommandResult:
        return _spawn(["/bin/sh", "-c", command], command, timeout)


class SshRunner(Runner):
    """Runs commands on a remote host over SSH.

    BatchMode=yes so a missing key fails immediately instead of hanging on a
    password prompt — an unattended sweep must never block on stdin.
    """

    name = "ssh"

    def __init__(self, target: str, identity: str = "",
                 ssh_options: list[str] | None = None) -> None:
        self.target = target
        self.ssh_options = ssh_options or [
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=15",
        ]
        # An explicit key beats the agent. An unattended sweep cannot rely on a
        # forwarded agent being present, and falling back to whatever key ssh
        # picks makes "permission denied" look like a host problem.
        if identity:
            self.ssh_options = [*self.ssh_options, "-i", str(Path(identity).expanduser())]

    def run(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> CommandResult:
        argv = ["ssh", *self.ssh_options, self.target, command]
        result = _spawn(argv, command, timeout)
        # 255 is ssh's own "could not connect", distinct from any exit code the
        # remote command could return. Treating it as a check result would
        # silently report an unreachable host as a clean one.
        if result.exit_code == 255:
            raise TransportError(
                f"ssh could not reach {self.target}: {result.stderr.strip() or 'no detail'}"
            )
        return result


class FakeRunner(Runner):
    """A runner that replays recorded output. The suite's only runner.

    Commands are matched by substring against the keys of `responses`, longest
    key first, so a test can key on `aide --check` without reproducing the full
    command line. An unmatched command is an error rather than a default, so a
    test cannot silently pass on output it never supplied.
    """

    name = "fake"

    def __init__(self, responses: dict[str, tuple[int, str, str]]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def run(self, command: str, timeout: int = DEFAULT_TIMEOUT) -> CommandResult:
        self.calls.append(command)
        for key in sorted(self.responses, key=len, reverse=True):
            if key in command:
                code, out, err = self.responses[key]
                return CommandResult(command, code, out, err)
        raise AssertionError(f"FakeRunner has no response for: {command}")


def _spawn(argv: list[str], command: str, timeout: int) -> CommandResult:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise TransportError(f"cannot execute {shlex.join(argv[:1])}: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise TransportError(f"timed out after {timeout}s: {command}") from exc
    return CommandResult(command, proc.returncode, proc.stdout or "", proc.stderr or "")
