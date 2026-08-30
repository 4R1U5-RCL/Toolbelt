"""Report templating.

Templates are `str.format` strings over a flat mapping of strings — so a report
is config, not code (the single rule that keeps a poller from being edited per
run, which is how slugs got hard-coded in the first place: KI-01).

Rendering is total: a template referencing a field the source did not produce
renders it empty rather than crashing a delivery six hours into a watch.
"""

from __future__ import annotations

from typing import Mapping

from .log import get_logger


class _SafeDict(dict):
    """Missing keys render as an empty string instead of raising KeyError."""

    def __missing__(self, key: str) -> str:
        get_logger().debug("template referenced unknown field %r; rendered empty", key)
        return ""


def render(template: str, context: Mapping[str, object]) -> str:
    """Render `template` against `context`, never raising.

    Values are stringified first, so a template can only ever interpolate text —
    `{x.__class__}` has nothing to reach through to.
    """
    safe = _SafeDict({str(k): "" if v is None else str(v) for k, v in context.items()})
    try:
        return template.format_map(safe)
    except (IndexError, ValueError, AttributeError, TypeError) as exc:
        # Malformed template (stray brace, positional field). Degrade to the raw
        # template plus the context so the human still gets the facts.
        get_logger().warning("template failed to render (%s); emitting fallback", exc)
        pairs = ", ".join("{0}={1}".format(k, v) for k, v in sorted(safe.items()) if v)
        return "{0}\n[unrendered template: {1}]".format(pairs, template)
