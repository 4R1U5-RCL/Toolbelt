"""The catalogue: validation, total rendering, and what `requires` is for."""

import json
import os
import tempfile
import unittest

import helpers  # noqa: F401  (path setup)

from telegram.errors import KeyboardError, TemplateError
from telegram.template import Catalogue, Template, catalogue_dir

MINIMAL = {"id": "t", "title": "Hello {name}"}


def make(**overrides):
    return Template(dict(MINIMAL, **overrides))


class TestValidation(unittest.TestCase):
    def test_a_template_needs_an_id(self):
        with self.assertRaises(TemplateError):
            Template({"title": "x"})

    def test_a_template_needs_a_title(self):
        with self.assertRaises(TemplateError):
            Template({"id": "t"})

    def test_group_must_be_known(self):
        with self.assertRaises(TemplateError):
            make(group="sideways")

    def test_kind_must_be_known_or_null(self):
        with self.assertRaises(TemplateError):
            make(kind="shouting")
        self.assertIsNone(make(kind=None).kind)

    def test_severity_must_be_known(self):
        with self.assertRaises(TemplateError):
            make(severity="catastrophic")

    def test_an_interactive_template_must_have_a_return_path(self):
        # Otherwise it is an output message wearing a question mark.
        with self.assertRaises(TemplateError) as caught:
            make(group="interactive")
        self.assertIn("no return path", str(caught.exception).replace("neither buttons nor a poll",
                                                                     "no return path"))

    def test_unknown_keys_are_warned_not_ignored(self):
        with self.assertLogs("telegram", level="WARNING") as logged:
            make(tilte="typo")
        self.assertIn("unknown keys", "".join(logged.output))


class TestRendering(unittest.TestCase):
    def test_interpolates_context(self):
        self.assertEqual(make().render({"name": "Arius"}).title, "Hello Arius")

    def test_defaults_fill_gaps(self):
        template = make(defaults={"name": "there"})
        self.assertEqual(template.render().title, "Hello there")

    def test_payload_beats_defaults(self):
        template = make(defaults={"name": "there"})
        self.assertEqual(template.render({"name": "you"}).title, "Hello you")

    def test_template_structure_is_flattened_but_content_is_not(self):
        # Headings and bullets are structure and go; inline delimiters are inert
        # on this rail and are left exactly as written (TG-01, TG-23).
        self.assertEqual(make(title="## {name}").render({"name": "build"}).title, "build")
        self.assertEqual(make(title="**{name}**").render({"name": "build"}).title,
                         "**build**")

    def test_payload_content_is_never_altered_by_rendering(self):
        # Third-party field values are data. A description containing markdown
        # characters must arrive as the source sent it.
        rendered = make(title="{name}").render({"name": "build __v2__ `ok`"}).title
        self.assertEqual(rendered, "build __v2__ `ok`")

    def test_an_undeclared_missing_field_renders_blank_rather_than_raising(self):
        # Total rendering: a delivery must not fail six hours in over a field
        # nobody said was required.
        self.assertEqual(make(title="Hi {nobody}").render().title, "Hi")

    def test_severity_emoji_is_available_to_every_template(self):
        self.assertEqual(make(title="{emoji}", severity="error").render().title, "🔴")

    def test_title_body_and_footer_are_joined_with_blank_lines(self):
        template = make(title="T", body="B", footer="F")
        self.assertEqual(template.render().text, "T\n\nB\n\nF")

    def test_empty_sections_do_not_leave_gaps(self):
        template = make(title="T", body="", footer="F")
        self.assertEqual(template.render().text, "T\n\nF")


class TestRequires(unittest.TestCase):
    """The line between a template bug and a data bug."""

    def test_a_missing_required_field_raises_by_default(self):
        with self.assertRaises(TemplateError) as caught:
            make(requires=["name"]).render({})
        self.assertIn("TG-17", str(caught.exception))

    def test_lenient_mode_renders_anyway_and_records_the_gap(self):
        # A degraded notification still beats no notification when something is
        # already going wrong.
        message = make(requires=["name"]).render({}, strict=False)
        self.assertEqual(message.missing, ["name"])
        self.assertIn("missing_fields", message.meta())

    def test_an_empty_string_counts_as_missing(self):
        with self.assertRaises(TemplateError):
            make(requires=["name"]).render({"name": ""})

    def test_zero_does_not_count_as_missing(self):
        # A score of 0 is a real result, not an absent one.
        self.assertEqual(make(requires=["name"]).render({"name": 0}).title, "Hello 0")

    def test_a_default_satisfies_a_requirement(self):
        self.assertEqual(make(requires=["name"], defaults={"name": "x"}).render().missing, [])


class TestMeta(unittest.TestCase):
    def test_carries_the_template_identity(self):
        meta = make().render({"name": "x"}).meta()
        self.assertEqual(meta["template"], "t")
        self.assertEqual(meta["group"], "output")

    def test_keyboard_lands_where_the_fan_out_looks_for_it(self):
        # The live workflow reads meta.reply_markup.inline_keyboard. Anywhere
        # else and the message arrives with no buttons and no error.
        template = make(group="interactive",
                        buttons=[[{"text": "OK", "action": "ok", "entity": "e", "id": "{key}"}]])
        meta = template.render({"name": "x", "key": "1"}).meta()
        self.assertEqual(meta["reply_markup"]["inline_keyboard"][0][0]["callback_data"],
                         "ok:e:1")

    def test_no_keyboard_key_when_there_are_no_buttons(self):
        self.assertNotIn("reply_markup", make().render({"name": "x"}).meta())

    def test_extra_meta_is_merged(self):
        self.assertEqual(make().render({"name": "x"}).meta({"run": "412"})["run"], "412")


class TestPoll(unittest.TestCase):
    def test_options_come_from_a_context_field(self):
        template = make(group="interactive",
                        poll={"question": "{q}", "options_field": "options"})
        poll = template.render({"name": "x", "q": "Which?",
                                "options": ["A", "B", "C"]}).poll
        self.assertEqual(poll["options"], ["A", "B", "C"])
        self.assertEqual(poll["question"], "Which?")

    def test_a_pipe_separated_string_is_accepted(self):
        # So a poll can be driven from `--set options=A|B|C` on the CLI.
        template = make(group="interactive", poll={"options_field": "options"})
        self.assertEqual(
            template.render({"name": "x", "options": "A|B|C"}).poll["options"],
            ["A", "B", "C"])

    def test_fewer_than_two_options_is_an_error(self):
        template = make(group="interactive", poll={"options_field": "options"})
        with self.assertRaises(TemplateError):
            template.render({"name": "x", "options": ["only"]})

    def test_options_are_capped_at_ten(self):
        template = make(group="interactive", poll={"options_field": "options"})
        poll = template.render({"name": "x", "options": [str(i) for i in range(20)]}).poll
        self.assertEqual(len(poll["options"]), 10)


class TestCatalogue(unittest.TestCase):
    def test_the_bundled_catalogue_loads_and_is_not_empty(self):
        self.assertGreater(len(Catalogue().load().all()), 10)

    def test_every_bundled_template_is_valid(self):
        # Loading skips unusable files, so an empty catalogue would otherwise
        # look like a clean pass.
        directory = catalogue_dir()
        files = [f for f in os.listdir(directory) if f.endswith(".json")]
        self.assertEqual(len(Catalogue().load().all()), len(files))

    def test_groups_are_all_populated(self):
        catalogue = Catalogue().load()
        for group in ("input", "output", "interactive"):
            self.assertTrue(catalogue.by_group(group), "group {0} is empty".format(group))

    def test_unknown_id_names_what_is_available(self):
        with self.assertRaises(TemplateError) as caught:
            Catalogue().load().get("nope")
        self.assertIn("report", str(caught.exception))

    def test_a_file_path_works_anywhere_an_id_does(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "custom.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"id": "custom", "title": "Custom {x}"}, handle)
            self.assertEqual(Catalogue().load().get(path).id, "custom")

    def test_one_unusable_file_does_not_take_down_the_catalogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "broken.json"), "w", encoding="utf-8") as handle:
                handle.write("{not json")
            with open(os.path.join(tmp, "fine.json"), "w", encoding="utf-8") as handle:
                json.dump({"id": "fine", "title": "ok"}, handle)
            catalogue = Catalogue([tmp]).load()
            self.assertEqual([t.id for t in catalogue.all()], ["fine"])

    def test_a_local_directory_overrides_the_bundled_catalogue(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "report.json"), "w", encoding="utf-8") as handle:
                json.dump({"id": "report", "title": "MINE"}, handle)
            catalogue = Catalogue([tmp, catalogue_dir()]).load()
            self.assertEqual(catalogue.get("report").title, "MINE")


class TestBundledCatalogueBehaviour(unittest.TestCase):
    """The shipped templates render, and their buttons encode."""

    def setUp(self):
        self.catalogue = Catalogue().load()

    def test_every_interactive_template_encodes_its_buttons(self):
        payload = {"title": "t", "id": "abc", "question": "q?", "entity": "e",
                   "option_a": "A", "option_b": "B", "options": ["A", "B"]}
        for template in self.catalogue.by_group("interactive"):
            message = template.render(payload)
            self.assertTrue(message.reply_markup or message.poll,
                            "{0} produced no return path".format(template.id))

    def test_a_long_id_is_refused_rather_than_silently_truncated(self):
        with self.assertRaises(KeyboardError):
            self.catalogue.get("approval").render(
                {"title": "t", "id": "x" * 90, "entity": "deploy"})

    def test_poller_settled_requires_a_score(self):
        with self.assertRaises(TemplateError):
            self.catalogue.get("poller.settled").render({"key": "1"})


if __name__ == "__main__":
    unittest.main()
