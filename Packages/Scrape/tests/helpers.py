"""Shared test doubles. Imported by every test file via ``from helpers import *``.

Everything here is offline and deterministic: no network, no secrets, no fixtures
to install. The HTTP transport is faked at two levels — ``FakeHttp`` stands in for
``HttpClient`` (returns/raises queued outcomes for ``post_json``), and
``FakeBackend`` stands in for ``FirecrawlClient`` (returns/raises queued ``data``
dicts for ``scrape``) — so a test can exercise the client layer or the engine
layer in isolation.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.disable(logging.CRITICAL)  # keep test output clean

from scrape.http import HttpResponse  # noqa: E402


def ok_data(markdown="# Heading\n\nA body paragraph.\n", title="Example", status=200, links=None):
    """A well-formed Firecrawl ``data`` object."""
    return {
        "markdown": markdown,
        "metadata": {"title": title, "statusCode": status},
        "links": list(links or []),
    }


def json_response(payload, status=200):
    import json

    return HttpResponse(status=status, body=json.dumps(payload), headers={})


class FakeHttp:
    """Stands in for ``HttpClient``. ``post_json`` drains a queue of outcomes."""

    def __init__(self, *outcomes):
        self._q = list(outcomes)
        self.calls = []  # list of (url, payload, headers)

    def post_json(self, url, payload, headers=None):
        self.calls.append((url, payload, headers or {}))
        item = self._q.pop(0) if self._q else HttpResponse(200, "{}", {})
        if isinstance(item, Exception):
            raise item
        return item


class FakeBackend:
    """Stands in for ``FirecrawlClient``. ``scrape`` drains a queue of results."""

    def __init__(self, *results):
        self._q = list(results)
        self.urls = []

    def scrape(self, url):
        self.urls.append(url)
        item = self._q.pop(0) if self._q else ok_data()
        if isinstance(item, Exception):
            raise item
        return item
