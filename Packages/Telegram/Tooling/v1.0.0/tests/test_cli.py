"""The command line — especially `render`, which is the offline safety net."""

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

import helpers  # noqa: F401  (path setup)

from telegram.cli import EXIT_ERROR, EXIT_OK, main


def run(*argv):
    """Run the CLI, returning (exit code, stdout)."""
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = main(list(argv))
    return code, buffer.getvalue()


class TestTemplates(unittest.TestCase):
    def test_lists_all_three_groups(self):
        code, out = run("templates")
        self.assertEqual(code, EXIT_OK)
        for group in ("INPUT", "OUTPUT", "INTERACTIVE"):
            self.assertIn(group, out)

    def test_group_filter(self):
        code, out = run("templates", "--group", "interactive")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("approval", out)
        self.assertNotIn("poller.settled", out)

    def test_json_output_is_machine_readable(self):
        code, out = run("templates", "--json")
        self.assertEqual(code, EXIT_OK)
        ids = {row["id"] for row in json.loads(out)}
        self.assertIn("report", ids)


class TestRender(unittest.TestCase):
    """Offline preview. Nothing leaves the machine, which is the point."""

    def test_renders_a_report(self):
        code, out = run("render", "report", "--set", "title=Deploy finished")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Deploy finished", out)

    def test_shows_what_each_button_encodes_to(self):
        # The whole IN-30 class is invisible until you can see this string.
        code, out = run("render", "approval", "--set", "title=Ship it",
                        "--set", "id=run-412", "--set", "entity=deploy")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("ok:deploy:run-412", out)

    def test_reports_the_length_in_the_unit_telegram_uses(self):
        code, out = run("render", "report", "--set", "title=x")
        self.assertIn("UTF-16 units", out)

    def test_a_missing_required_field_fails(self):
        code, _ = run("render", "poller.settled", "--set", "key=1")
        self.assertEqual(code, EXIT_ERROR)

    def test_lenient_renders_anyway_and_names_the_gap(self):
        code, out = run("render", "poller.settled", "--set", "key=1", "--lenient")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("MISSING", out)
        self.assertIn("score", out)

    def test_data_file_supplies_the_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "event.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"key": "55881637", "score": "51.210", "source": "kaggle"}, handle)
            code, out = run("render", "poller.settled", "--data", path)
            self.assertEqual(code, EXIT_OK)
            self.assertIn("51.210", out)

    def test_set_overrides_the_data_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "event.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"key": "1", "score": "1.0"}, handle)
            code, out = run("render", "poller.settled", "--data", path,
                            "--set", "score=99.9")
            self.assertIn("99.9", out)

    def test_json_output_carries_the_parts_and_the_meta(self):
        code, out = run("render", "approval", "--json", "--set", "title=t",
                        "--set", "id=1", "--set", "entity=e")
        payload = json.loads(out)
        self.assertEqual(payload["template"], "approval")
        self.assertIn("reply_markup", payload["meta"])
        self.assertEqual(len(payload["parts"]), 1)

    def test_a_long_message_previews_as_several(self):
        code, out = run("render", "report", "--set", "title=t",
                        "--set", "body=" + ("word " * 2000), "--json")
        self.assertGreater(len(json.loads(out)["parts"]), 1)

    def test_unknown_template_is_an_error_that_lists_the_known_ones(self):
        code, _ = run("render", "nope")
        self.assertEqual(code, EXIT_ERROR)

    def test_malformed_set_is_rejected(self):
        code, _ = run("render", "report", "--set", "no-equals-sign")
        self.assertEqual(code, EXIT_ERROR)


class TestDecode(unittest.TestCase):
    def test_decodes_callback_data(self):
        code, out = run("decode", "att:kaggle:55881637")
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(json.loads(out)["entity"], "kaggle")

    def test_decodes_a_whole_update(self):
        update = json.dumps({"callback_query": {
            "id": "c1", "from": {"id": 1}, "message": {"chat": {"id": 2}},
            "data": "ok:e:3"}})
        code, out = run("decode", update)
        self.assertEqual(code, EXIT_OK)
        self.assertTrue(json.loads(out)["trusted"])

    def test_an_update_failing_the_gate_exits_non_zero(self):
        update = json.dumps({"callback_query": {
            "id": "c1", "from": {"id": 1}, "message": {"chat": {"id": 2}},
            "data": "ok:e:3"}})
        code, out = run("decode", update, "--allow-chat", "999")
        self.assertEqual(code, EXIT_ERROR)
        self.assertFalse(json.loads(out)["trusted"])


class TestVersion(unittest.TestCase):
    def test_prints_a_version(self):
        code, out = run("version")
        self.assertEqual(code, EXIT_OK)
        self.assertIn("telegram", out)


if __name__ == "__main__":
    unittest.main()
