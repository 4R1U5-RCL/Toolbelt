"""Executor process-gate — self-test suite. Stdlib only (unittest)."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
GATE = os.path.join(HERE, "..", "bin", "process-gate")
TEMPLATES = os.path.join(HERE, "..", "templates")

spec = importlib.util.spec_from_loader(
    "gate", importlib.machinery.SourceFileLoader("gate", GATE)
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


CONFIG = """\
meta:
  version: 1.0.0

slots:
  s1_runner:        "bash tests/verify.sh"
  s2_gate_jobs:     ["process-gate"]
  s3_branch:        "main"
  s5_id_scheme:     "github"
  s6_change_record: "CHANGELOG.md"
  s8_t2_paths:
    - "migrations/*"
    - "deploy/*"
  s9_excluded:      ["clients/*"]
  s11_rollback:     "git revert"

scope:
  governs: everything else
"""


def write(tmp, name, text):
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    return p


def status_of(results, name):
    for n, s, _ in results:
        if n == name:
            return s
    raise AssertionError(f"no check named {name}")


class SlotsParser(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cfg = write(self.tmp, "process.yaml", CONFIG)

    def test_scalar(self):
        s = gate.parse_slots(self.cfg)
        self.assertEqual(s["s1_runner"], "bash tests/verify.sh")
        self.assertEqual(s["s6_change_record"], "CHANGELOG.md")

    def test_inline_list(self):
        s = gate.parse_slots(self.cfg)
        self.assertEqual(s["s2_gate_jobs"], ["process-gate"])
        self.assertEqual(s["s9_excluded"], ["clients/*"])

    def test_block_list(self):
        s = gate.parse_slots(self.cfg)
        self.assertEqual(s["s8_t2_paths"], ["migrations/*", "deploy/*"])

    def test_stops_at_next_top_level_key(self):
        s = gate.parse_slots(self.cfg)
        self.assertNotIn("governs", s)

    def test_missing_config_is_none(self):
        self.assertIsNone(gate.parse_slots(os.path.join(self.tmp, "nope.yaml")))

    def test_placeholder_detection(self):
        self.assertTrue(gate.is_placeholder("<command>"))
        self.assertFalse(gate.is_placeholder("pnpm test"))


class Checks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.slots = gate.parse_slots(write(self.tmp, "process.yaml", CONFIG))

    def run_gate(self, body, changed, runner="pass"):
        return gate.run_checks(self.slots, body, changed, runner)

    def test_clean_t1_passes_everything(self):
        r = self.run_gate("T1 — fix the thing.\n\nCloses #12", ["src/a.py", "CHANGELOG.md"])
        for name in ("tier-declared", "reciprocity", "change-record", "evidence"):
            self.assertEqual(status_of(r, name), gate.PASS, name)

    def test_undeclared_tier_fails(self):
        r = self.run_gate("fix the thing\n\nCloses #12", ["src/a.py", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "tier-declared"), gate.FAIL)

    def test_t2_path_declared_t1_fails_floor(self):
        r = self.run_gate("T1\n\nCloses #12", ["migrations/003.sql", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "tier-floor"), gate.FAIL)

    def test_t2_path_declared_t2_passes_floor(self):
        body = "T2\n\nCloses #12\n\nRollback: git revert abc123 and redeploy v1.2.0\n"
        r = self.run_gate(body, ["migrations/003.sql", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "tier-floor"), gate.PASS)
        self.assertEqual(status_of(r, "rollback"), gate.PASS)

    def test_pipeline_owned_path_fails_scope(self):
        r = self.run_gate("T1\n\nCloses #12", ["clients/acme/page.tsx", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "scope"), gate.FAIL)

    def test_missing_issue_citation_fails_reciprocity(self):
        r = self.run_gate("T1 — just a change", ["src/a.py", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "reciprocity"), gate.FAIL)

    def test_bare_hash_is_not_a_citation(self):
        r = self.run_gate("T1 — see #12 for background", ["src/a.py", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "reciprocity"), gate.FAIL)

    def test_missing_change_record_fails(self):
        r = self.run_gate("T1\n\nCloses #12", ["src/a.py"])
        self.assertEqual(status_of(r, "change-record"), gate.FAIL)

    def test_t2_without_rollback_fails(self):
        r = self.run_gate("T2\n\nCloses #12", ["migrations/003.sql", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "rollback"), gate.FAIL)

    def test_t2_with_empty_rollback_heading_fails(self):
        r = self.run_gate("T2\n\nCloses #12\n\nRollback:\n\n", ["migrations/1.sql", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "rollback"), gate.FAIL)

    def test_t0_skips_record_checks(self):
        r = self.run_gate("T0 — typo", ["README.md"])
        self.assertEqual(status_of(r, "reciprocity"), gate.SKIP)
        self.assertEqual(status_of(r, "change-record"), gate.SKIP)

    def test_unknown_runner_fails_t1_per_inv4(self):
        r = self.run_gate("T1\n\nCloses #12", ["src/a.py", "CHANGELOG.md"], runner="unknown")
        self.assertEqual(status_of(r, "evidence"), gate.FAIL)

    def test_unknown_runner_defers_on_t0(self):
        r = self.run_gate("T0 — typo", ["README.md"], runner="unknown")
        self.assertEqual(status_of(r, "evidence"), gate.DEFER)

    def test_failing_runner_fails(self):
        r = self.run_gate("T1\n\nCloses #12", ["src/a.py", "CHANGELOG.md"], runner="fail")
        self.assertEqual(status_of(r, "evidence"), gate.FAIL)

    def test_approval_always_defers(self):
        r = self.run_gate("T1\n\nCloses #12", ["src/a.py", "CHANGELOG.md"])
        self.assertEqual(status_of(r, "approval"), gate.DEFER)

    def test_unfilled_runner_defers(self):
        cfg = CONFIG.replace('"bash tests/verify.sh"', '"<command>"')
        slots = gate.parse_slots(write(self.tmp, "p2.yaml", cfg))
        r = gate.run_checks(slots, "T1\n\nCloses #12", ["src/a.py", "CHANGELOG.md"], "unknown")
        self.assertEqual(status_of(r, "evidence"), gate.DEFER)


class EndToEnd(unittest.TestCase):
    """The CLI as CI actually invokes it."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.cfg = write(self.tmp, "process.yaml", CONFIG)

    def invoke(self, body, changed, runner="pass"):
        b = write(self.tmp, "body.txt", body)
        c = write(self.tmp, "changed.txt", "\n".join(changed))
        return subprocess.run(
            [sys.executable, GATE, "--config", self.cfg, "--body-file", b,
             "--changed-file", c, "--runner-status", runner],
            capture_output=True, text=True,
        )

    def test_clean_change_exits_zero(self):
        p = self.invoke("T1 — fix\n\nCloses #12", ["src/a.py", "CHANGELOG.md"])
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("0 failure(s)", p.stdout)

    def test_violation_exits_one(self):
        p = self.invoke("T1 — fix", ["src/a.py"])
        self.assertEqual(p.returncode, 1)
        self.assertIn("FAIL", p.stdout)

    def test_unadopted_repo_defers_and_exits_zero(self):
        p = subprocess.run(
            [sys.executable, GATE, "--config", os.path.join(self.tmp, "absent.yaml")],
            capture_output=True, text=True,
        )
        self.assertEqual(p.returncode, 0)
        self.assertIn("DEFER", p.stdout)

    def test_every_check_reports_a_status(self):
        p = self.invoke("T2\n\nCloses #1\n\nRollback: git revert abc", ["migrations/1.sql", "CHANGELOG.md"])
        for name in ("tier-declared", "tier-floor", "scope", "reciprocity",
                     "change-record", "rollback", "evidence", "approval"):
            self.assertIn(name, p.stdout)


class Templates(unittest.TestCase):
    """The shipped templates must be internally consistent."""

    def test_yaml_template_slots_parse(self):
        s = gate.parse_slots(os.path.join(TEMPLATES, "executor-process.yaml.template"))
        self.assertIsNotNone(s)
        for k in ("s1_runner", "s3_branch", "s6_change_record", "s8_t2_paths",
                  "s9_excluded", "s10_adoption", "s11_rollback"):
            self.assertIn(k, s, f"template is missing slot {k}")

    def test_yaml_template_ships_unfilled(self):
        s = gate.parse_slots(os.path.join(TEMPLATES, "executor-process.yaml.template"))
        self.assertTrue(gate.is_placeholder(s["s1_runner"]))

    def test_prose_declares_yaml_normative(self):
        p = os.path.join(TEMPLATES, "EXECUTOR_PROCESS.md.template")
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("the yaml wins", text)

    def test_every_invariant_in_prose_exists_in_yaml(self):
        with open(os.path.join(TEMPLATES, "executor-process.yaml.template"), encoding="utf-8") as fh:
            y = fh.read()
        for n in range(1, 9):
            self.assertIn(f"INV-{n}:", y, f"yaml is missing INV-{n}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
