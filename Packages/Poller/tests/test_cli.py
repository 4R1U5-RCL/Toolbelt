import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from helpers import *  # noqa: F401,F403
from poller.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.report = os.path.join(self.dir, "reports.md")
        self.config_path = os.path.join(self.dir, "poller.json")
        self.write_config()

    def write_config(self, **overrides):
        config = {
            "name": "clitest",
            "state_dir": self.dir,
            "interval_seconds": 5,
            "max_duration_hours": 0,
            "source": {
                "type": "python",
                "target": "fake_source:StaticSource",
                "items": [
                    {"key": "A", "state": "settled", "title": "alpha",
                     "fields": {"score": "51.210"}},
                    {"key": "B", "state": "pending", "title": "bravo", "fields": {}},
                ],
            },
            "sinks": [{"type": "file", "path": self.report}],
        }
        config.update(overrides)
        with open(self.config_path, "w", encoding="utf-8") as handle:
            json.dump(config, handle)

    def run_cli(self, *argv):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(list(argv))
        return code, buffer.getvalue()

    def test_version(self):
        code, out = self.run_cli("version")
        self.assertEqual(code, 0)
        self.assertIn("poller", out)

    def test_check_validates_without_sending_anything(self):
        code, _ = self.run_cli("check", "-c", self.config_path)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.report))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "clitest.state.json")))

    def test_status_before_any_run(self):
        code, out = self.run_cli("status", "-c", self.config_path)
        self.assertEqual(code, 1)
        self.assertIn("NEVER_RAN", out)

    def test_test_command_is_dry_by_default(self):
        code, _ = self.run_cli("test", "-c", self.config_path)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.report))

    def test_run_once_seeds_and_writes_state(self):
        code, _ = self.run_cli("run", "-c", self.config_path, "--once")
        self.assertEqual(code, 0)
        # The watch start/stop still lands in the file audit trail; what must
        # NOT appear is the pre-existing item — seeded history is not news.
        with open(self.report, encoding="utf-8") as handle:
            self.assertNotIn("alpha", handle.read())
        with open(os.path.join(self.dir, "clitest.state.json"), encoding="utf-8") as handle:
            state = json.load(handle)
        self.assertIsNotNone(state["seeded_at"])

    def test_run_once_without_seeding_reports(self):
        code, _ = self.run_cli("run", "-c", self.config_path, "--once", "--no-seed")
        self.assertEqual(code, 0)
        with open(self.report, encoding="utf-8") as handle:
            self.assertIn("alpha", handle.read())

    def test_dry_run_reports_nothing(self):
        code, _ = self.run_cli("run", "-c", self.config_path, "--once", "--no-seed", "--dry-run")
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.report))

    def test_status_after_a_run_reports_stopped(self):
        self.run_cli("run", "-c", self.config_path, "--once")
        code, out = self.run_cli("status", "-c", self.config_path, "--json")
        self.assertEqual(code, 1)  # a finished watch is NOT a healthy watch
        self.assertEqual(json.loads(out)["verdict"], "STOPPED")

    def test_state_command_summarises_the_ledger(self):
        self.run_cli("run", "-c", self.config_path, "--once", "--no-seed")
        code, out = self.run_cli("state", "-c", self.config_path, "--json")
        self.assertEqual(code, 0)
        summary = json.loads(out)
        self.assertEqual(summary["undelivered"], [])
        # One item report plus the watch_started/watch_ended lifecycle records.
        self.assertEqual(summary["stats"]["records"], 3)

    def test_a_bad_config_path_fails_cleanly(self):
        code, _ = self.run_cli("check", "-c", "/nonexistent/x.json")
        self.assertEqual(code, 2)

    def test_no_command_prints_help(self):
        code, _ = self.run_cli()
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
