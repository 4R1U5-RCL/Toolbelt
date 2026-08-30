import os
import tempfile
import unittest

from helpers import *  # noqa: F401,F403
from poller.envfile import EnvResolver, read_env_file
from poller.errors import ConfigError
from poller.log import registered_secrets


class EnvFileTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, ".env")
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(
                "# a comment\n"
                "\n"
                "PLAIN=value1\n"
                "export EXPORTED=value2\n"
                'QUOTED="has spaces"\n'
                "SINGLE='single quoted'\n"
                "WITH_EQUALS=a=b=c\n"
                "not a valid line\n"
                "EMPTY=\n"
            )

    def test_parses_the_shapes_a_real_dotenv_contains(self):
        values = read_env_file(self.path)
        self.assertEqual(values["PLAIN"], "value1")
        self.assertEqual(values["EXPORTED"], "value2")
        self.assertEqual(values["QUOTED"], "has spaces")
        self.assertEqual(values["SINGLE"], "single quoted")
        self.assertEqual(values["WITH_EQUALS"], "a=b=c")
        self.assertEqual(values["EMPTY"], "")

    def test_missing_file_is_not_fatal(self):
        self.assertEqual(read_env_file(os.path.join(self.dir, "nope")), {})

    def test_file_wins_over_process_env(self):
        resolver = EnvResolver(self.path, environ={"PLAIN": "from-process"})
        self.assertEqual(resolver.get("PLAIN"), "value1")

    def test_falls_back_to_process_env(self):
        resolver = EnvResolver(self.path, environ={"ONLY_IN_ENV": "yes-abc"})
        self.assertEqual(resolver.get("ONLY_IN_ENV"), "yes-abc")

    def test_missing_required_value_fails_at_startup(self):
        resolver = EnvResolver(self.path, environ={})
        with self.assertRaises(ConfigError):
            resolver.get("ABSENT")
        self.assertIsNone(resolver.get("ABSENT", required=False))

    def test_resolved_values_are_registered_for_redaction(self):
        resolver = EnvResolver(self.path, environ={})
        resolver.get("QUOTED")
        self.assertIn("has spaces", registered_secrets())

    def test_env_reference_expansion(self):
        resolver = EnvResolver(self.path, environ={})
        self.assertEqual(resolver.resolve("@env:PLAIN"), "value1")
        self.assertEqual(resolver.resolve("literal"), "literal")
        self.assertEqual(resolver.resolve_mapping({"H": "@env:PLAIN"}), {"H": "value1"})


if __name__ == "__main__":
    unittest.main()
