"""Single-instance locking, without `ps`.

Two copies of the same poller means every report lands twice, and it happens
easily: a watch is relaunched because nobody could tell whether the first one
was still alive (KI-03). The lock makes the second launch refuse, and the heartbeat file
makes "is it alive?" answerable — those two together are the fix.

Liveness is checked with `os.kill(pid, 0)` plus a `/proc` command-line match,
because the container this most often runs in has no `ps` binary at all (KI-09).
"""

from __future__ import annotations

import errno
import json
import os
from typing import Optional

from .clock import Clock
from .errors import AlreadyRunning
from .log import get_logger


class InstanceLock:
    """A PID lock file that reclaims itself after an unclean exit."""

    def __init__(self, path: str, name: str = "poller", clock: Optional[Clock] = None):
        self.path = os.path.expanduser(path)
        self.name = name
        self.clock = clock or Clock()
        self._held = False

    def acquire(self, force: bool = False) -> None:
        """Take the lock, or raise AlreadyRunning if a live process holds it.

        Creation is exclusive (`O_CREAT | O_EXCL`), so two launches racing at
        the same instant cannot both conclude the lock was free.
        """
        os.makedirs(os.path.dirname(os.path.abspath(self.path)) or ".", exist_ok=True)
        if self._create_exclusive():
            self._held = True
            return

        holder = self.holder()
        if holder and not force and is_process_alive(holder.get("pid"), holder.get("cmdline")):
            raise AlreadyRunning(
                "poller {0!r} is already running as pid {1} (since {2}); "
                "use --force to take over".format(
                    holder.get("name", self.name), holder.get("pid"), holder.get("started_at")
                )
            )
        if holder and not force:
            get_logger().warning(
                "reclaiming stale lock from dead pid %s (last started %s)",
                holder.get("pid"), holder.get("started_at"),
            )
        self._write()  # takeover: overwrite in place
        self._held = True

    def release(self) -> None:
        """Drop the lock, but only if it is still ours."""
        if not self._held:
            return
        holder = self.holder()
        if holder and holder.get("pid") == os.getpid():
            try:
                os.unlink(self.path)
            except OSError:  # pragma: no cover - already gone is fine
                pass
        self._held = False

    def holder(self) -> Optional[dict]:
        """Read the current lock file, or None if absent/unreadable."""
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return None

    def _create_exclusive(self) -> bool:
        """Try to create the lock file atomically. False means it already exists."""
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(self._payload(), handle)
            handle.write("\n")
        return True

    def _payload(self) -> dict:
        return {
            "pid": os.getpid(),
            "name": self.name,
            "started_at": self.clock.iso(),
            "cmdline": _own_cmdline(),
        }

    def _write(self) -> None:
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self._payload(), handle)
            handle.write("\n")

    def __enter__(self) -> "InstanceLock":
        self.acquire()
        return self

    def __exit__(self, *exc_info) -> None:
        self.release()


def is_process_alive(pid: Optional[int], expect_cmdline: Optional[str] = None) -> bool:
    """True if `pid` is live and, when known, still the *same* process.

    Comparing against the command line recorded when the lock was taken guards
    against PID reuse: after a reboot some unrelated process may well own the
    recorded number, and treating that as a live poller would block every future
    launch. Where `/proc` is unavailable the signal probe stands alone.
    """
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return False
        if exc.errno == errno.EPERM:
            return True  # alive, owned by another user
        return False

    if expect_cmdline is None:
        return True  # nothing to compare against; trust the signal probe
    cmdline = _cmdline_of(pid)
    if cmdline is None:
        return True  # no /proc on this platform; trust the signal probe
    return cmdline.strip() == expect_cmdline.strip()


def _cmdline_of(pid: int) -> Optional[str]:
    try:
        with open("/proc/{0}/cmdline".format(pid), "rb") as handle:
            return handle.read().decode("utf-8", "replace").replace("\x00", " ")
    except OSError:
        return None


def _own_cmdline() -> str:
    return _cmdline_of(os.getpid()) or "poller"
