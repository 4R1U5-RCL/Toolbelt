"""Text templating.

Templates are `str.format` strings over a flat mapping of strings — so a message
is config, not code. That is the whole point of the package: seventeen n8n
builders, a Node hook, a TypeScript digest and a Python watchdog each hand-rolled
their own format string, and none of them could be fixed in one place.

Rendering is total: a template referencing a field the payload did not carry
renders it empty rather than raising at the moment of delivery. Whether that
blank is acceptable or a bug is a separate question, answered by a template's
declared `requires` (TG-17) — this layer only guarantees it never explodes.
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
