"""A custom source, used both to test and to demonstrate the `python` plugin path.

This is exactly the shape `IMPLEMENTATIONS.md` tells operators to write when an
API needs real logic (pagination, GraphQL, a second call per row): subclass
`Source`, implement `fetch`, and inherit dedup, retries, delivery and
survivability unchanged.
"""

from poller.model import Item, ItemState
from poller.sources.base import Source


class StaticSource(Source):
    """Returns whatever `config["items"]` lists — no network involved."""

    name = "static"

    def fetch(self):
        return [
            Item(key=str(row["key"]), state=row.get("state", ItemState.SETTLED),
                 title=row.get("title", ""), fields=row.get("fields", {}))
            for row in self.config.get("items", [])
        ]

    def describe(self):
        return "static source ({0} item(s))".format(len(self.config.get("items", [])))
