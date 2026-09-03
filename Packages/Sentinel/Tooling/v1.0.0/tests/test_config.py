"""Config loading, and the guard that keeps host data out of the repo."""

import json
import tempfile
import unittest
from pathlib import Path

from sentinel import config
from sentinel.errors import BoundaryError, ConfigError


def write_manifest(directory: Path, payload: dict) -> Path:
    manifest = directory / "hosts.json"
    manifest.write_text(json.dumps(payload))
    return manifest


class TestBoundaryGuard(unittest.TestCase):
    """The reason this package can be published: the data never enters it."""

    def test_baselines_inside_the_repo_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Toolbelt"
            (root / "Packages").mkdir(parents=True)
            (root / "PROCESS.md").write_text("# Toolbelt")
            inside = root / "baselines"
            inside.mkdir()
            with self.assertRaises(BoundaryError) as caught:
                config.assert_outside_repo(inside, root)
            self.assertIn("may be", str(caught.exception))

    def test_nested_baselines_inside_the_repo_are_also_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Toolbelt"
            deep = root / "Packages" / "Sentinel" / "baselines"
            deep.mkdir(parents=True)
            (root / "PROCESS.md").write_text("# Toolbelt")
            with self.assertRaises(BoundaryError):
                config.assert_outside_repo(deep, root)

    def test_baselines_outside_the_repo_are_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Toolbelt"
            root.mkdir()
            (root / "PROCESS.md").write_text("# Toolbelt")
            outside = Path(tmp) / "elsewhere"
            outside.mkdir()
            config.assert_outside_repo(outside, root)  # must not raise

    def test_no_repo_detected_means_no_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            config.assert_outside_repo(Path(tmp), None)  # must not raise

    def test_load_refuses_before_it_reads_anything(self):
        """The guard runs ahead of the directory check, so pointing Sentinel at
        an in-repo path fails on the boundary rather than on a missing file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "Toolbelt"
            root.mkdir()
            (root / "PROCESS.md").write_text("# Toolbelt")
            with self.assertRaises(BoundaryError):
                config.load(str(root / "does-not-exist"), environ={}, root=root)


class TestResolution(unittest.TestCase):
    def test_argument_beats_env(self):
        got = config.resolve_baselines_dir("/tmp/explicit",
                                           {"SENTINEL_BASELINES_DIR": "/tmp/env"})
        self.assertEqual(got, Path("/tmp/explicit"))

    def test_env_beats_default(self):
        got = config.resolve_baselines_dir(None, {"SENTINEL_BASELINES_DIR": "/tmp/env"})
        self.assertEqual(got, Path("/tmp/env"))

    def test_default_is_outside_the_repo(self):
        got = config.resolve_baselines_dir(None, {})
        self.assertEqual(got, Path(config.DEFAULT_BASELINES).expanduser())


class TestLoad(unittest.TestCase):
    def test_loads_hosts(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_manifest(Path(tmp), {"hosts": [
                {"name": "a.example", "target": "root@203.0.113.1",
                 "checks": ["aide", "debsums"]},
                {"name": "local-box", "local": True, "checks": ["debsums"]},
            ]})
            cfg = config.load(tmp, environ={}, root=None)
            self.assertEqual(len(cfg.hosts), 2)
            self.assertEqual(cfg.host("a.example").checks, ("aide", "debsums"))
            self.assertTrue(cfg.host("local-box").local)

    def test_unknown_check_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_manifest(Path(tmp), {"hosts": [
                {"name": "a", "target": "t", "checks": ["aide", "clamscan"]}]})
            with self.assertRaises(ConfigError) as caught:
                config.load(tmp, environ={}, root=None)
            self.assertIn("clamscan", str(caught.exception))

    def test_remote_host_without_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_manifest(Path(tmp), {"hosts": [{"name": "a", "checks": ["aide"]}]})
            with self.assertRaises(ConfigError):
                config.load(tmp, environ={}, root=None)

    def test_missing_manifest_points_at_the_example(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ConfigError) as caught:
                config.load(tmp, environ={}, root=None)
            self.assertIn("hosts.example.json", str(caught.exception))

    def test_missing_directory_explains_the_split(self):
        with self.assertRaises(ConfigError) as caught:
            config.load("/nonexistent/baselines/dir", environ={}, root=None)
        self.assertIn("the method, not the data", str(caught.exception))

    def test_malformed_json_is_reported_as_such(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "hosts.json").write_text("{not json")
            with self.assertRaises(ConfigError) as caught:
                config.load(tmp, environ={}, root=None)
            self.assertIn("not valid JSON", str(caught.exception))

    def test_unknown_host_lookup_lists_the_known_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_manifest(Path(tmp), {"hosts": [{"name": "a", "target": "t"}]})
            cfg = config.load(tmp, environ={}, root=None)
            with self.assertRaises(ConfigError) as caught:
                cfg.host("nope")
            self.assertIn("a", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
