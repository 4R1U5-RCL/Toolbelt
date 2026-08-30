import json
import unittest

from helpers import *  # noqa: F401,F403
from poller.envfile import EnvResolver
from poller.errors import ConfigError, FatalSourceError, TransientSourceError
from poller.http import HttpFatal, HttpResponse, HttpTransient
from poller.model import ItemState
from poller.sources import build_source
from poller.sources.http_json import HttpJsonSource, dig


class StubClient:
    """Returns a canned body (or raises a canned error) for every request."""

    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []

    def request(self, method, url, headers=None, body=None, params=None):
        self.calls.append({"method": method, "url": url, "headers": headers or {}, "params": params})
        if self.error:
            raise self.error
        return HttpResponse(status=200, body=json.dumps(self.payload).encode("utf-8"))


def resolver(**environ):
    return EnvResolver(None, environ=environ)


class DigTests(unittest.TestCase):
    def test_root_paths(self):
        for path in ("", ".", None):
            self.assertEqual(dig([1, 2], path), [1, 2])

    def test_nested_dicts_and_list_indices(self):
        data = {"a": {"b": [{"c": 7}]}}
        self.assertEqual(dig(data, "a.b.0.c"), 7)

    def test_missing_path_returns_the_default(self):
        self.assertIsNone(dig({"a": 1}, "a.b.c"))
        self.assertEqual(dig({"a": 1}, "zz", default="fallback"), "fallback")

    def test_indexing_a_scalar_does_not_explode(self):
        self.assertIsNone(dig({"a": 5}, "a.b"))


BASE = {
    "type": "http_json",
    "url": "https://api.example.com/jobs",
    "items_path": "data.jobs",
    "key_field": "id",
    "title_template": "{label}",
    "fields": {"label": "label", "result": "result.value"},
    "state": {
        "field": "status",
        "map": {"settled": ["finished"], "failed": ["error"], "pending": ["running", "queued"]},
        "default": "pending",
    },
}

PAYLOAD = {"data": {"jobs": [
    {"id": 1, "label": "one", "status": "finished", "result": {"value": "9.5"}},
    {"id": 2, "label": "two", "status": "running", "result": {}},
    {"id": 3, "label": "three", "status": "error", "result": {}},
]}}


class HttpJsonSourceTests(unittest.TestCase):
    def source(self, config=None, payload=PAYLOAD, error=None, **environ):
        client = StubClient(payload=payload, error=error)
        src = HttpJsonSource(dict(BASE, **(config or {})), resolver(**environ), client)
        return src, client

    def test_maps_rows_onto_the_four_states(self):
        src, _ = self.source()
        states = {item.key: item.state for item in src.fetch()}
        self.assertEqual(states, {"1": ItemState.SETTLED, "2": ItemState.PENDING,
                                  "3": ItemState.FAILED})

    def test_fields_and_titles_come_from_the_mapping(self):
        src, _ = self.source()
        first = src.fetch()[0]
        self.assertEqual(first.title, "one")
        self.assertEqual(first.fields["result"], "9.5")

    def test_status_matching_is_substring_and_case_insensitive_by_default(self):
        payload = {"data": {"jobs": [{"id": 9, "status": "JobStatus.FINISHED", "label": "x"}]}}
        src, _ = self.source(payload=payload)
        self.assertEqual(src.fetch()[0].state, ItemState.SETTLED)

    def test_exact_matching_can_be_demanded(self):
        payload = {"data": {"jobs": [{"id": 9, "status": "JobStatus.FINISHED", "label": "x"}]}}
        src, _ = self.source({"state": dict(BASE["state"], match="exact")}, payload=payload)
        self.assertEqual(src.fetch()[0].state, ItemState.PENDING)  # falls to the default

    def test_settled_requires_holds_a_row_that_has_no_result_yet(self):
        payload = {"data": {"jobs": [{"id": 9, "status": "finished", "label": "x", "result": {}}]}}
        src, _ = self.source({"state": dict(BASE["state"], settled_requires=["result"])},
                             payload=payload)
        self.assertEqual(src.fetch()[0].state, ItemState.PENDING)

    def test_ambiguous_status_resolves_to_failed_not_settled(self):
        payload = {"data": {"jobs": [{"id": 9, "status": "finished with error", "label": "x"}]}}
        src, _ = self.source(payload=payload)
        self.assertEqual(src.fetch()[0].state, ItemState.FAILED)

    def test_rows_without_a_key_are_skipped_not_guessed_at(self):
        payload = {"data": {"jobs": [{"label": "anonymous", "status": "finished"}]}}
        src, _ = self.source(payload=payload)
        self.assertEqual(src.fetch(), [])

    def test_filters_narrow_the_watch(self):
        src, _ = self.source({"filter": {"field": "label", "contains": "TW"}})
        self.assertEqual([i.key for i in src.fetch()], ["2"])

    def test_not_contains_filter(self):
        src, _ = self.source({"filter": [{"field": "label", "not_contains": "o"}]})
        self.assertEqual([i.key for i in src.fetch()], ["3"])

    def test_a_wrong_items_path_is_fatal_with_a_useful_message(self):
        src, _ = self.source({"items_path": "data.nope"})
        with self.assertRaises(FatalSourceError) as ctx:
            src.fetch()
        self.assertIn("items_path", str(ctx.exception))

    def test_a_non_list_items_path_is_fatal(self):
        src, _ = self.source({"items_path": "data"})
        with self.assertRaises(FatalSourceError):
            src.fetch()

    def test_http_errors_keep_their_classification(self):
        src, _ = self.source(error=HttpFatal("HTTP 401", status=401))
        with self.assertRaises(FatalSourceError):
            src.fetch()
        src, _ = self.source(error=HttpTransient("timeout"))
        with self.assertRaises(TransientSourceError):
            src.fetch()

    def test_bearer_auth_header(self):
        src, client = self.source({"auth": {"scheme": "bearer", "token": "@env:TOK"}}, TOK="abc123")
        src.fetch()
        self.assertEqual(client.calls[0]["headers"]["Authorization"], "Bearer abc123")

    def test_basic_auth_header(self):
        src, client = self.source({"auth": {"scheme": "basic", "token": "@env:TOK"}}, TOK="user:key")
        src.fetch()
        self.assertEqual(client.calls[0]["headers"]["Authorization"], "Basic dXNlcjprZXk=")

    def test_custom_header_auth(self):
        src, client = self.source(
            {"auth": {"scheme": "header", "header": "X-API-Key", "token": "@env:TOK"}}, TOK="k123456")
        src.fetch()
        self.assertEqual(client.calls[0]["headers"]["X-API-Key"], "k123456")

    def test_query_auth(self):
        src, client = self.source({"auth": {"scheme": "query", "param": "apikey", "token": "@env:TOK"}},
                                  TOK="q123456")
        src.fetch()
        self.assertEqual(client.calls[0]["params"]["apikey"], "q123456")

    def test_unknown_auth_scheme_is_a_config_error(self):
        with self.assertRaises(ConfigError):
            self.source({"auth": {"scheme": "magic"}})

    def test_url_is_required(self):
        with self.assertRaises(ConfigError):
            HttpJsonSource({"type": "http_json"}, resolver(), StubClient({}))


KAGGLE_ROWS = [
    {"ref": 55881637, "status": "complete", "publicScore": "51.210",
     "description": "agentsec-challenger-2arm", "date": "2026-08-30T04:17:28Z"},
    {"ref": 55881600, "status": "complete", "publicScore": None,
     "description": "agentsec-just-submitted", "date": "2026-08-30T04:10:00Z"},
    {"ref": 55880000, "status": "pending", "publicScore": None,
     "description": "agentsec-waiting", "date": "2026-08-30T03:00:00Z"},
    {"ref": 55870000, "status": "error", "publicScore": None, "errorDescription": "kernel timeout",
     "description": "agentsec-broken", "date": "2026-08-29T22:00:00Z"},
]


class KaggleSourceTests(unittest.TestCase):
    def source(self, payload, config=None):
        client = StubClient(payload=payload)
        cfg = dict({"type": "kaggle_submissions", "competition": "comp-slug"}, **(config or {}))
        return build_source(cfg, resolver(KAGGLE_API_TOKEN="tok123456"), client), client

    def test_watches_the_whole_competition_not_one_notebook(self):
        src, _ = self.source(KAGGLE_ROWS)
        self.assertIn("competitions/submissions/list/comp-slug", src.url)
        keys = [item.key for item in src.fetch()]
        self.assertEqual(keys, ["55881637", "55881600", "55880000", "55870000"])

    def test_identity_is_the_immutable_ref(self):
        src, _ = self.source(KAGGLE_ROWS)
        self.assertEqual(src.fetch()[0].key, "55881637")

    def test_a_scored_row_settles(self):
        src, _ = self.source(KAGGLE_ROWS)
        first = src.fetch()[0]
        self.assertEqual(first.state, ItemState.SETTLED)
        self.assertEqual(first.fields["score"], "51.210")

    def test_complete_without_a_score_is_still_pending(self):
        src, _ = self.source(KAGGLE_ROWS)
        self.assertEqual(src.fetch()[1].state, ItemState.PENDING)

    def test_an_error_row_is_reported_distinctly(self):
        src, _ = self.source(KAGGLE_ROWS)
        broken = src.fetch()[3]
        self.assertEqual(broken.state, ItemState.FAILED)
        self.assertEqual(broken.fields["error"], "kernel timeout")

    def test_enum_style_status_still_matches(self):
        rows = [{"ref": 1, "status": "SubmissionStatus.COMPLETE", "publicScore": "1.0",
                 "description": "d"}]
        src, _ = self.source(rows)
        self.assertEqual(src.fetch()[0].state, ItemState.SETTLED)

    def test_accepts_the_wrapped_response_shape_too(self):
        src, _ = self.source({"submissions": KAGGLE_ROWS})
        self.assertEqual(len(src.fetch()), 4)

    def test_bearer_auth_is_the_default(self):
        src, client = self.source(KAGGLE_ROWS)
        src.fetch()
        self.assertEqual(client.calls[0]["headers"]["Authorization"], "Bearer tok123456")

    def test_operator_config_overrides_the_preset(self):
        src, _ = self.source(KAGGLE_ROWS, {"filter": {"field": "description", "contains": "2arm"}})
        self.assertEqual([i.key for i in src.fetch()], ["55881637"])

    def test_competition_is_required(self):
        with self.assertRaises(ConfigError):
            build_source({"type": "kaggle_submissions"}, resolver(), StubClient([]))


class RegistryTests(unittest.TestCase):
    def test_unknown_type_lists_the_known_ones(self):
        with self.assertRaises(ConfigError) as ctx:
            build_source({"type": "carrier-pigeon"}, resolver())
        self.assertIn("http_json", str(ctx.exception))

    def test_missing_type_is_rejected(self):
        with self.assertRaises(ConfigError):
            build_source({}, resolver())

    def test_python_target_must_be_module_colon_class(self):
        with self.assertRaises(ConfigError):
            build_source({"type": "python", "target": "not_a_target"}, resolver())

    def test_python_target_must_subclass_source(self):
        with self.assertRaises(ConfigError):
            build_source({"type": "python", "target": "json:JSONDecoder"}, resolver())


if __name__ == "__main__":
    unittest.main()
