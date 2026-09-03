"""End-to-end sweeps driven by FakeRunner, plus report rendering and the CLI.

No host, no SSH key, no network — the seam in `runner` is what makes the whole
sweep path exercisable, including the failure paths a real host rarely shows.
"""

import io
import json
import tempfile
import unittest
from pathlib import Path

from sentinel import checks, classify, cli, report
from sentinel.config import Host, SweepConfig
from sentinel.errors import TransportError
from sentinel.runner import FakeRunner, Runner

CLEAN_AIDE = "AIDE found NO differences"
TAMPERED_AIDE = ("Summary:\n  Changed entries: 1\n"
                 "File: /srv/tree/config.conf\n"
                 "  Size    : 17        | 26\n")
HASH = "d6aa449cd0b55f8763c2db5644125761ef3d8616a35746ef1af5112f82443d45"


def config_with_fingerprint(tmp: str, host_name: str, value: str | None) -> SweepConfig:
    base = Path(tmp)
    if value is not None:
        (base / host_name).mkdir(parents=True, exist_ok=True)
        (base / host_name / "aide.db.sha256").write_text(value)
    return SweepConfig(baselines_dir=base)


class TestSweepHost(unittest.TestCase):
    def test_clean_host(self):
        host = Host("h", "root@h", ("aide", "aide_db_fingerprint", "debsums"))
        runner = FakeRunner({
            "--check": (0, CLEAN_AIDE, ""),
            "sha256sum": (0, f"{HASH}  /var/lib/aide/aide.db", ""),
            "debsums -c": (0, "", ""),
        })
        with tempfile.TemporaryDirectory() as tmp:
            cfg = config_with_fingerprint(tmp, "h", HASH)
            results = checks.sweep_host(runner, host, cfg)
        self.assertEqual(classify.worst(results), classify.CLEAN)
        self.assertEqual(len(results), 3)

    def test_tampered_host_reports_a_finding(self):
        host = Host("h", "root@h", ("aide",))
        runner = FakeRunner({"--check": (4, TAMPERED_AIDE, "")})
        results = checks.sweep_host(runner, host, SweepConfig(baselines_dir=Path("/x")))
        self.assertEqual(classify.worst(results), classify.FINDING)

    def test_swapped_database_reports_a_finding(self):
        """The tamper-evidence property: the host's own db no longer matches the
        record kept off it."""
        host = Host("h", "root@h", ("aide_db_fingerprint",))
        runner = FakeRunner({"sha256sum": (0, f"{'0' * 64}  /var/lib/aide/aide.db", "")})
        with tempfile.TemporaryDirectory() as tmp:
            cfg = config_with_fingerprint(tmp, "h", HASH)
            results = checks.sweep_host(runner, host, cfg)
        self.assertEqual(results[0].verdict, classify.FINDING)

    def test_unrecorded_host_is_unbaselined(self):
        host = Host("h", "root@h", ("aide_db_fingerprint",))
        runner = FakeRunner({"sha256sum": (0, f"{HASH}  /var/lib/aide/aide.db", "")})
        with tempfile.TemporaryDirectory() as tmp:
            cfg = config_with_fingerprint(tmp, "h", None)
            results = checks.sweep_host(runner, host, cfg)
        self.assertEqual(results[0].verdict, classify.UNBASELINED)

    def test_unreachable_host_is_an_error_and_stops_that_host(self):
        """An unreachable host must never render as a clean one."""

        class Dead(Runner):
            def run(self, command, timeout=0):
                raise TransportError("ssh could not reach root@h")

        host = Host("h", "root@h", ("aide", "debsums", "rkhunter"))
        results = checks.sweep_host(Dead(), host, SweepConfig(baselines_dir=Path("/x")))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].verdict, classify.ERROR)
        self.assertNotEqual(classify.worst(results), classify.CLEAN)


class TestFakeRunner(unittest.TestCase):
    def test_unmatched_command_is_an_error_not_a_default(self):
        runner = FakeRunner({"--check": (0, "", "")})
        with self.assertRaises(AssertionError):
            runner.run("debsums -c")


class TestReport(unittest.TestCase):
    def results(self):
        return [
            classify.CheckResult("h", "aide", classify.CLEAN, "no watched file changed"),
            classify.CheckResult("h", "debsums", classify.FINDING, "2 files differ",
                                 evidence=["/usr/bin/ls"]),
        ]

    def test_text_report_carries_the_caveat(self):
        text = report.render_text(self.results(), "2026-09-03T00:00:00Z")
        self.assertIn("does not prove the host is clean", text)
        self.assertIn("FINDING", text)

    def test_clean_report_still_carries_the_caveat(self):
        clean = [classify.CheckResult("h", "aide", classify.CLEAN, "ok")]
        self.assertIn("does not prove the host is clean", report.render_text(clean))

    def test_json_report_is_machine_readable(self):
        payload = json.loads(report.render_json(self.results(), "2026-09-03T00:00:00Z"))
        self.assertEqual(payload["verdict"], classify.FINDING)
        self.assertEqual(len(payload["results"]), 2)

    def test_exit_codes(self):
        make = lambda v: classify.CheckResult("h", "c", v, "")
        self.assertEqual(report.exit_code_for([make(classify.CLEAN)]), 0)
        self.assertEqual(report.exit_code_for([make(classify.FINDING)]), 1)
        self.assertEqual(report.exit_code_for([make(classify.ERROR)]), 2)
        self.assertEqual(report.exit_code_for([make(classify.UNBASELINED)]), 1)

    def test_a_finding_alongside_an_error_still_exits_as_a_finding(self):
        make = lambda v: classify.CheckResult("h", "c", v, "")
        both = [make(classify.ERROR), make(classify.FINDING)]
        self.assertEqual(report.exit_code_for(both), 1)


class TestCli(unittest.TestCase):
    def manifest(self, tmp):
        (Path(tmp) / "hosts.json").write_text(json.dumps({"hosts": [
            {"name": "a.example", "target": "root@203.0.113.1",
             "checks": ["aide", "debsums"]}]}))

    def test_hosts_lists_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.manifest(tmp)
            out = io.StringIO()
            code = cli.main(["--baselines", tmp, "hosts"], stdout=out)
        self.assertEqual(code, 0)
        self.assertIn("a.example", out.getvalue())

    def test_dry_run_executes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.manifest(tmp)
            out = io.StringIO()
            code = cli.main(["--baselines", tmp, "sweep", "--dry-run"], stdout=out)
        self.assertEqual(code, 0)
        self.assertIn("aide", out.getvalue())
        self.assertIn("debsums", out.getvalue())

    def test_missing_config_exits_two_not_zero(self):
        import contextlib
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code = cli.main(["--baselines", "/nonexistent/xyz", "hosts"])
        self.assertEqual(code, 2)
        self.assertIn("the method, not the data", err.getvalue())


if __name__ == "__main__":
    unittest.main()


class TestSshIdentity(unittest.TestCase):
    """A configured key must reach the ssh command line.

    Found by running the tool against the real fleet during v1.0.0: without
    this the sweep authenticates as whatever key ssh happens to pick, and a
    'Permission denied (publickey)' reads as a host problem rather than a
    configuration one.
    """

    def test_identity_is_passed_to_ssh(self):
        from sentinel.runner import SshRunner
        runner = SshRunner("root@203.0.113.1", "~/.ssh/id_ed25519_sweep")
        self.assertIn("-i", runner.ssh_options)
        self.assertTrue(runner.ssh_options[-1].endswith("id_ed25519_sweep"))
        self.assertNotIn("~", runner.ssh_options[-1])

    def test_no_identity_leaves_options_alone(self):
        from sentinel.runner import SshRunner
        self.assertNotIn("-i", SshRunner("root@203.0.113.1").ssh_options)

    def test_batchmode_is_always_set(self):
        from sentinel.runner import SshRunner
        self.assertIn("BatchMode=yes", SshRunner("root@203.0.113.1").ssh_options)


class TestOnlyFilter(unittest.TestCase):
    def manifest(self, tmp):
        (Path(tmp) / "hosts.json").write_text(json.dumps({"hosts": [
            {"name": "a", "target": "t", "checks": ["aide", "debsums"]},
            {"name": "b", "target": "t", "checks": ["debsums"]}]}))

    def test_only_narrows_the_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.manifest(tmp)
            out = io.StringIO()
            cli.main(["--baselines", tmp, "sweep", "--dry-run", "--only", "aide"], stdout=out)
        self.assertEqual(out.getvalue().strip(), "a\taide")

    def test_only_with_no_matching_host_exits_two(self):
        import contextlib
        with tempfile.TemporaryDirectory() as tmp:
            self.manifest(tmp)
            with contextlib.redirect_stderr(io.StringIO()):
                code = cli.main(["--baselines", tmp, "sweep", "--only", "rkhunter"])
        self.assertEqual(code, 2)


class TestTimeout(unittest.TestCase):
    """A slow check is not an unreachable host.

    Found when a corrected AIDE run on the larger host was still going at 920s
    against a 900s limit. Reporting that as "host unreachable" invents an
    infrastructure fault and — because a transport failure ends the host's sweep
    — hides the checks that would have disproved it.
    """

    class Slow(Runner):
        def run(self, command, timeout=0):
            from sentinel.errors import CheckTimeout
            if "aide" in command:
                raise CheckTimeout(f"timed out after {timeout}s: {command}")
            return type("R", (), {"command": command, "exit_code": 0,
                                  "stdout": "", "stderr": "", "ok": True})()

    def test_timeout_is_an_error_not_unreachable(self):
        host = Host("h", "root@h", ("aide",), timeout=900)
        results = checks.sweep_host(self.Slow(), host, SweepConfig(baselines_dir=Path("/x")))
        self.assertEqual(results[0].verdict, classify.ERROR)
        self.assertIn("timed out", results[0].headline)
        self.assertNotIn("unreachable", results[0].headline)

    def test_timeout_does_not_end_the_host_sweep(self):
        """The debsums pass that would show the box is fine must still run."""
        host = Host("h", "root@h", ("aide", "debsums"), timeout=900)
        results = checks.sweep_host(self.Slow(), host, SweepConfig(baselines_dir=Path("/x")))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[1].check, "debsums")
        self.assertEqual(results[1].verdict, classify.CLEAN)

    def test_unreachable_still_ends_the_host_sweep(self):
        class Dead(Runner):
            def run(self, command, timeout=0):
                raise TransportError("ssh could not reach root@h")
        host = Host("h", "root@h", ("aide", "debsums"), timeout=900)
        results = checks.sweep_host(Dead(), host, SweepConfig(baselines_dir=Path("/x")))
        self.assertEqual(len(results), 1)

    def test_host_timeout_reaches_the_runner(self):
        host = Host("h", "root@h", ("debsums",), timeout=1234)
        seen = {}
        class Recorder(Runner):
            def run(self, command, timeout=0):
                seen["timeout"] = timeout
                return type("R", (), {"command": command, "exit_code": 0,
                                      "stdout": "", "stderr": "", "ok": True})()
        checks.sweep_host(Recorder(), host, SweepConfig(baselines_dir=Path("/x")))
        self.assertEqual(seen["timeout"], 1234)

    def test_default_timeout_is_measured_not_the_old_guess(self):
        from sentinel.runner import DEFAULT_TIMEOUT
        self.assertEqual(DEFAULT_TIMEOUT, 3600)
        self.assertEqual(Host("h", "t", ()).timeout, 3600)
