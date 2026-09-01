import json
import os
import tempfile
import unittest

from helpers import *  # noqa: F401,F403
from poller.config import Config, from_dict, load_config
from poller.errors import ConfigError
from poller.model import EventReason

MINIMAL = {
    "name": "demo",
    "source": {"type": "http_json", "url": "https://example.com/x"},
    "sinks": [{"type": "stdout"}],
}


class ConfigTests(unittest.TestCase):
    def test_derives_state_paths_from_the_name(self):
        config = from_dict(dict(MINIMAL, state_dir="/tmp/pollertest"))
        self.assertEqual(config.state_file, "/tmp/pollertest/demo.state.json")
        self.assertEqual(config.heartbeat_file, "/tmp/pollertest/demo.heartbeat.json")
        self.assertEqual(config.lock_file, "/tmp/pollertest/demo.lock")

    def test_explicit_paths_win(self):
        config = from_dict(dict(MINIMAL, state_file="/tmp/x.json"))
        self.assertEqual(config.state_file, "/tmp/x.json")

    def test_templates_merge_over_defaults_per_field(self):
        config = from_dict(dict(MINIMAL, templates={"settled": {"title": "custom {key}"}}))
        spec = config.template_for(EventReason.SETTLED)
        self.assertEqual(spec["title"], "custom {key}")
        self.assertIn("body", spec)  # the default body survives a title-only override

    def test_rejects_a_name_that_would_not_be_a_safe_filename(self):
        with self.assertRaises(ConfigError):
            from_dict(dict(MINIMAL, name="has spaces"))

    def test_rejects_unknown_notify_states(self):
        with self.assertRaises(ConfigError):
            from_dict(dict(MINIMAL, notify_states=["finished"]))

    def test_rejects_a_poller_with_no_sinks(self):
        with self.assertRaises(ConfigError):
            from_dict(dict(MINIMAL, sinks=[]))

    def test_rejects_sub_second_intervals(self):
        with self.assertRaises(ConfigError):
            from_dict(dict(MINIMAL, interval_seconds=0))

    def test_unknown_keys_are_dropped_not_fatal(self):
        config = from_dict(dict(MINIMAL, intervall_seconds=5))
        self.assertEqual(config.interval_seconds, 180.0)

    def test_load_config_reports_bad_json_clearly(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write("{not json")
            path = handle.name
        with self.assertRaises(ConfigError) as ctx:
            load_config(path)
        self.assertIn("not valid JSON", str(ctx.exception))
        os.unlink(path)

    def test_missing_file_reports_the_path(self):
        with self.assertRaises(ConfigError):
            load_config("/nonexistent/poller.json")

    def test_shipped_examples_all_load(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        examples = os.path.join(here, "examples")
        for name in sorted(os.listdir(examples)):
            if name.endswith(".json"):
                config = load_config(os.path.join(examples, name))
                self.assertTrue(config.name, name)
                self.assertTrue(config.sinks, name)


if __name__ == "__main__":
    unittest.main()
