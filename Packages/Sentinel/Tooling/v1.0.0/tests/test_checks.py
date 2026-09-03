"""What the tool actually RUNS.

This file exists because 55 tests passed while the headline check could not
execute. Every one of them fed `classify_*` its inputs directly, so the suite
proved the classifiers and proved nothing about the command strings. A test that
supplies its own inputs to a pure function cannot fail for the reason the tool is
about to fail. See
KNOWN_ISSUES.md#aide-check-was-invoked-without-config-so_7932f6e0.
"""

import tempfile
import unittest
from pathlib import Path

from sentinel import checks, classify
from sentinel.config import Host, SweepConfig
from sentinel.runner import FakeRunner


class TestCommands(unittest.TestCase):
    def test_aide_command_always_passes_a_config(self):
        """The bare `aide --check` exits 17 on Debian/Ubuntu and checks nothing."""
        cmd = checks.aide_command("/etc/aide/aide.conf")
        self.assertIn("--config /etc/aide/aide.conf", cmd)
        self.assertIn("--check", cmd)

    def test_aide_command_honours_a_custom_config(self):
        self.assertIn("--config /opt/custom/aide.conf",
                      checks.aide_command("/opt/custom/aide.conf"))

    def test_run_aide_sends_the_configured_path_to_the_runner(self):
        host = Host("h", "root@h", ("aide",), aide_config="/opt/custom/aide.conf")
        runner = FakeRunner({"aide": (0, "AIDE found NO differences", "")})
        checks.run_aide(runner, host, SweepConfig(baselines_dir=Path("/x")))
        self.assertEqual(len(runner.calls), 1)
        self.assertIn("--config /opt/custom/aide.conf", runner.calls[0])

    def test_fingerprint_command_reads_the_configured_db(self):
        host = Host("h", "root@h", ("aide_db_fingerprint",), aide_db="/opt/aide.db")
        runner = FakeRunner({"sha256sum": (0, "abc  /opt/aide.db", "")})
        with tempfile.TemporaryDirectory() as tmp:
            checks.run_aide_db_fingerprint(runner, host,
                                           SweepConfig(baselines_dir=Path(tmp)))
        self.assertIn("/opt/aide.db", runner.calls[0])

    def test_every_check_command_is_non_empty(self):
        for name in ("debsums", "rkhunter", "chkrootkit"):
            with self.subTest(check=name):
                host = Host("h", "root@h", (name,))
                runner = FakeRunner({"": (0, "", "")})
                checks.CHECKS[name](runner, host, SweepConfig(baselines_dir=Path("/x")))
                self.assertTrue(runner.calls[0].strip())


class TestAideConfigError(unittest.TestCase):
    """Exit 17 is a setup fault, and the message has to say so."""

    STDERR = ("ERROR: missing configuration (use '--config' '--before' or "
              "'--after' command line parameter)")

    def test_config_error_names_the_path(self):
        result = classify.classify_aide("h", 17, "", self.STDERR,
                                        config_path="/etc/aide/aide.conf")
        self.assertEqual(result.verdict, classify.ERROR)
        self.assertIn("/etc/aide/aide.conf", result.headline)
        self.assertIn("never checked anything", result.detail)

    def test_config_error_is_not_a_finding_about_the_host(self):
        result = classify.classify_aide("h", 15, "", self.STDERR, config_path="/x")
        self.assertEqual(result.verdict, classify.ERROR)
        self.assertNotEqual(result.verdict, classify.FINDING)

    def test_other_error_codes_keep_the_generic_message(self):
        result = classify.classify_aide("h", 18, "", "IO error", config_path="/x")
        self.assertEqual(result.verdict, classify.ERROR)
        self.assertIn("failed to run", result.headline)


if __name__ == "__main__":
    unittest.main()
