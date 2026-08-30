import json
import os
import tempfile
import unittest

from helpers import *  # noqa: F401,F403
from poller.errors import AlreadyRunning
from poller.lock import InstanceLock, is_process_alive


class LockTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "p.lock")

    def test_second_instance_is_refused(self):
        first = InstanceLock(self.path, "demo")
        first.acquire()
        with self.assertRaises(AlreadyRunning):
            InstanceLock(self.path, "demo").acquire()
        first.release()

    def test_lock_is_released_and_retakeable(self):
        with InstanceLock(self.path, "demo"):
            pass
        InstanceLock(self.path, "demo").acquire()  # must not raise

    def test_stale_lock_from_a_dead_pid_is_reclaimed(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump({"pid": 999999, "name": "demo", "started_at": "x"}, handle)
        InstanceLock(self.path, "demo").acquire()  # must not raise

    def test_force_takes_over_a_live_lock(self):
        first = InstanceLock(self.path, "demo")
        first.acquire()
        InstanceLock(self.path, "demo").acquire(force=True)

    def test_release_does_not_delete_someone_elses_lock(self):
        mine = InstanceLock(self.path, "demo")
        mine.acquire()
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump({"pid": 424242, "name": "demo"}, handle)
        mine.release()
        self.assertTrue(os.path.exists(self.path))

    def test_liveness_probe_needs_no_ps_binary(self):
        self.assertTrue(is_process_alive(os.getpid()))
        self.assertFalse(is_process_alive(999999))
        self.assertFalse(is_process_alive(None))
        self.assertFalse(is_process_alive(-1))


if __name__ == "__main__":
    unittest.main()


class LockRaceTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "p.lock")

    def test_creation_is_exclusive(self):
        first = InstanceLock(self.path, "demo")
        self.assertTrue(first._create_exclusive())
        self.assertFalse(InstanceLock(self.path, "demo")._create_exclusive())

    def test_the_lock_records_who_holds_it(self):
        lock = InstanceLock(self.path, "demo")
        lock.acquire()
        holder = lock.holder()
        self.assertEqual(holder["pid"], os.getpid())
        self.assertEqual(holder["name"], "demo")
        self.assertIn("cmdline", holder)
