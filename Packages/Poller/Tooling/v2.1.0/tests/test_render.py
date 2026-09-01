import unittest

from helpers import *  # noqa: F401,F403  (path bootstrap)
from poller.render import render


class RenderTests(unittest.TestCase):
    def test_interpolates_known_fields(self):
        self.assertEqual(render("score {score}", {"score": "51.2"}), "score 51.2")

    def test_missing_field_renders_empty_rather_than_raising(self):
        # A six-hour watch must not die because a template names a field this
        # particular row happens not to have.
        self.assertEqual(render("a{missing}b", {}), "ab")

    def test_none_renders_empty(self):
        self.assertEqual(render("[{score}]", {"score": None}), "[]")

    def test_malformed_template_degrades_to_facts(self):
        out = render("unbalanced {", {"key": "K1"})
        self.assertIn("K1", out)
        self.assertIn("unrendered template", out)

    def test_values_are_stringified_so_a_template_cannot_reach_into_objects(self):
        # Containment is the stringify: whatever the source produced, a template
        # can only ever traverse attributes of a plain `str`.
        class Carrier:
            token = "super-secret"

            def __str__(self):
                return "carrier"

        out = render("{obj.__class__}", {"obj": Carrier()})
        self.assertEqual(out, "<class 'str'>")
        self.assertNotIn("super-secret", render("{obj.token}", {"obj": Carrier()}))


if __name__ == "__main__":
    unittest.main()
