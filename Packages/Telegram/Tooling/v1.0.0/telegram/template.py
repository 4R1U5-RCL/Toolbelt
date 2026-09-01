"""Templates: a message is a JSON file, not an edited function.

The problem this exists for is concrete. Today a Telegram message is composed at
the call site in four different runtimes — a Node hook, a TypeScript digest,
seventeen n8n Code nodes, and a Python watchdog — each with its own format
string, its own emoji, and its own truncation limit. None of them can be fixed
in one place, and the conventions have quietly diverged (TG-13).

So the catalogue is data. Adding a message shape means adding a file; changing
how every settle report reads means changing one.

## Groups

Templates fall into three groups, which is the distinction the catalogue is
organised around:

* **input** — rendering an event that arrived from somewhere else. The Poller is
  the first-class producer: its settle, failure, staleness and lifecycle events
  all have entries.
* **output** — composing something the studio is saying itself: a report, an
  update, an alert, a digest, a handoff.
* **interactive** — asking the human something, and therefore carrying buttons
  and a return path.

## Required fields

A template declares the context fields it cannot do without. Rendering is total
(a missing field renders empty rather than raising), which is right at delivery
time but wrong at authoring time — a blank where a score should be looks like a
quiet success. `requires` is what separates the two: a declared field that is
absent is reported as an error, an undeclared one is simply blank (TG-17).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Mapping, Optional

from .errors import TemplateError
from .keyboard import from_spec
from .log import get_logger
from .render import render
from .text import chunk, plain

GROUPS = ("input", "output", "interactive")
#: The `kind` the notify envelope carries. Consumers route on it.
KINDS = ("attention", "complete", "alert")
SEVERITIES = ("info", "warn", "error")

#: The house style, finally in one place. Sourced from the conventions already
#: in use across `packages/agent-kit/src/notify.ts` and the notify hook, which
#: agreed by copy-paste rather than by contract until now (TG-13).
SEVERITY_EMOJI = {"info": "🟢", "warn": "🟡", "error": "🔴"}

_KNOWN_KEYS = {
    "id", "group", "description", "kind", "severity", "requires", "defaults",
    "title", "body", "buttons", "footer", "poll",
}


def catalogue_dir() -> str:
    """The bundled catalogue, resolved relative to this file.

    Not a working-directory-relative path: the CLI is routinely invoked from
    another tree, and a catalogue that silently resolves to nothing would make
    every template id look unknown.
    """
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")


class Template:
    """One message shape: what it says, what it needs, and what it asks."""

    def __init__(self, data: Mapping[str, Any], origin: str = "<memory>"):
        self.origin = origin
        self.raw = dict(data)

        self.id = str(data.get("id") or "").strip()
        if not self.id:
            raise TemplateError("{0}: template has no `id`".format(origin))

        self.group = str(data.get("group") or "output")
        if self.group not in GROUPS:
            raise TemplateError("{0}: group must be one of {1}, got {2!r}".format(
                origin, ", ".join(GROUPS), self.group))

        self.kind = data.get("kind")
        if self.kind is not None and self.kind not in KINDS:
            raise TemplateError("{0}: kind must be one of {1} or null, got {2!r}".format(
                origin, ", ".join(KINDS), self.kind))

        self.severity = str(data.get("severity") or "info")
        if self.severity not in SEVERITIES:
            raise TemplateError("{0}: severity must be one of {1}, got {2!r}".format(
                origin, ", ".join(SEVERITIES), self.severity))

        self.title = data.get("title")
        if not self.title:
            raise TemplateError("{0}: template has no `title`".format(origin))

        self.description = str(data.get("description") or "")
        self.body = data.get("body") or ""
        self.footer = data.get("footer") or ""
        self.requires: List[str] = list(data.get("requires") or [])
        self.defaults: Dict[str, Any] = dict(data.get("defaults") or {})
        self.buttons = data.get("buttons")
        self.poll = data.get("poll")

        if self.group == "interactive" and not (self.buttons or self.poll):
            raise TemplateError(
                "{0}: template {1!r} is in the `interactive` group but declares neither "
                "buttons nor a poll — an interactive message with no return path is just "
                "an output message that looks like a question".format(origin, self.id))

        # A typo'd key would otherwise be silently ignored, and the template
        # would render without the thing its author thought they had configured.
        unknown = set(self.raw) - _KNOWN_KEYS
        if unknown:
            get_logger().warning("%s: template %r has unknown keys: %s",
                                 origin, self.id, ", ".join(sorted(unknown)))

    # -- rendering -------------------------------------------------------------

    def context(self, data: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """Merge defaults, the payload, and the derived fields templates may use."""
        ctx: Dict[str, Any] = dict(self.defaults)
        ctx.update(dict(data or {}))
        ctx.setdefault("severity", self.severity)
        ctx.setdefault("emoji", SEVERITY_EMOJI.get(str(ctx.get("severity")), "🔔"))
        ctx.setdefault("template", self.id)
        return ctx

    def missing(self, context: Mapping[str, Any]) -> List[str]:
        """Declared fields the payload did not supply, in declaration order."""
        return [f for f in self.requires
                if context.get(f) in (None, "") and f not in self.defaults]

    def render(self, data: Optional[Mapping[str, Any]] = None,
               strict: bool = True) -> "Message":
        """Build a `Message` from this template and a payload.

        With `strict`, a missing required field raises — which is what you want
        while authoring, and in a test. Without it, the message is built anyway
        with blanks, because a degraded notification still beats no notification
        when something is already going wrong.
        """
        ctx = self.context(data)
        gaps = self.missing(ctx)
        if gaps:
            note = ("template {0!r} requires {1}, absent from the payload"
                    .format(self.id, ", ".join(repr(g) for g in gaps)))
            if strict:
                raise TemplateError(note + " (TG-17)")
            get_logger().warning("%s — rendering blank (TG-17)", note)

        title = plain(render(str(self.title), ctx))
        body = plain(render(str(self.body), ctx)) if self.body else ""
        footer = plain(render(str(self.footer), ctx)) if self.footer else ""

        text = "\n\n".join(p for p in (title, body, footer) if p)
        return Message(
            template=self, text=text, title=title, body=body,
            context=ctx, missing=gaps,
            reply_markup=from_spec(self.buttons, ctx),
            poll=self._render_poll(ctx),
        )

    def _render_poll(self, ctx: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
        """Build a native Telegram poll spec, if this template declares one.

        Options may be listed statically or drawn from a context field, because
        a poll's choices are usually the thing that varies. Telegram requires
        between 2 and 10 options and caps each at 100 characters; a caller that
        supplies one option has asked a question with no question in it, so that
        is an error rather than a silently-dropped widget.
        """
        if not self.poll:
            return None
        spec = dict(self.poll)
        options: List[str] = []

        field = spec.get("options_field")
        if field:
            supplied = ctx.get(field)
            if isinstance(supplied, (list, tuple)):
                options.extend(str(o) for o in supplied)
            elif isinstance(supplied, str) and supplied:
                options.extend(p.strip() for p in supplied.split("|") if p.strip())
        options.extend(render(str(o), ctx) for o in (spec.get("options") or []))

        options = [o[:100] for o in options if o][:10]
        if len(options) < 2:
            raise TemplateError(
                "template {0!r}: a Telegram poll needs 2-10 options, got {1}. Supply them "
                "in the payload field {2!r} (a list, or a '|'-separated string)".format(
                    self.id, len(options), field or "options"))

        return {
            "question": plain(render(str(spec.get("question") or self.title), ctx))[:300],
            "options": options,
            "is_anonymous": bool(spec.get("is_anonymous", False)),
            "allows_multiple_answers": bool(spec.get("multiple", False)),
        }


class Message:
    """A rendered message: the text that will arrive, and the envelope's extras."""

    def __init__(self, template: Template, text: str, title: str, body: str,
                 context: Mapping[str, Any], missing: List[str],
                 reply_markup: Optional[Dict[str, Any]] = None,
                 poll: Optional[Dict[str, Any]] = None):
        self.template = template
        self.text = text
        self.title = title
        self.body = body
        self.context = dict(context)
        self.missing = list(missing)
        self.reply_markup = reply_markup
        self.poll = poll

    def parts(self) -> List[str]:
        """The text split into individually deliverable messages (TG-04)."""
        return chunk(self.text)

    def meta(self, extra: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        """The envelope `meta`, including the keyboard the fan-out looks for.

        The live workflow reads `meta.reply_markup.inline_keyboard`, so a
        keyboard placed anywhere else is silently dropped and the message
        arrives with no buttons and no error.
        """
        meta: Dict[str, Any] = {
            "template": self.template.id,
            "group": self.template.group,
            "severity": self.template.severity,
        }
        if self.reply_markup:
            meta["reply_markup"] = self.reply_markup
        if self.poll:
            # The live fan-out cannot send a poll — its Telegram node is wired to
            # sendMessage. `n8n/telegram-interactive.json` is the workflow that
            # reads this; against the fan-out the message still arrives as text.
            meta["poll"] = self.poll
        if self.missing:
            meta["missing_fields"] = ",".join(self.missing)
        meta.update(dict(extra or {}))
        return meta


class Catalogue:
    """Every template available to this process, keyed by id."""

    def __init__(self, directories: Optional[List[str]] = None):
        self.directories = [d for d in (directories or [catalogue_dir()]) if d]
        self._templates: Dict[str, Template] = {}
        self._loaded = False

    def load(self) -> "Catalogue":
        """Read every `*.json` in every catalogue directory.

        A malformed file is reported and skipped rather than taking the whole
        catalogue down — one bad template should not stop the other twenty from
        being usable.
        """
        for directory in self.directories:
            if not os.path.isdir(directory):
                get_logger().debug("catalogue directory absent: %s", directory)
                continue
            for name in sorted(os.listdir(directory)):
                if not name.endswith(".json"):
                    continue
                path = os.path.join(directory, name)
                try:
                    template = load_file(path)
                except (TemplateError, ValueError, OSError) as exc:
                    get_logger().error("skipping unusable template %s: %s", path, exc)
                    continue
                if template.id in self._templates:
                    # FIRST directory wins, so a caller's own directory (which
                    # the CLI puts ahead of the bundled one) overrides a shipped
                    # template rather than being silently overwritten by it.
                    get_logger().debug(
                        "template id %r already defined by %s; ignoring %s",
                        template.id, self._templates[template.id].origin, path)
                    continue
                self._templates[template.id] = template
        self._loaded = True
        return self

    def get(self, template_id: str) -> Template:
        if not self._loaded:
            self.load()
        # A path is accepted anywhere an id is, so a caller can try a template
        # out without first installing it into the catalogue.
        if template_id not in self._templates and os.path.isfile(template_id):
            return load_file(template_id)
        try:
            return self._templates[template_id]
        except KeyError:
            raise TemplateError(
                "unknown template {0!r}. Known: {1}".format(
                    template_id, ", ".join(sorted(self._templates)) or "(none loaded)"))

    def all(self) -> List[Template]:
        if not self._loaded:
            self.load()
        return [self._templates[k] for k in sorted(self._templates)]

    def by_group(self, group: str) -> List[Template]:
        return [t for t in self.all() if t.group == group]


def load_file(path: str) -> Template:
    """Load one template from disk."""
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise TemplateError("{0}: expected a JSON object".format(path))
    return Template(data, origin=path)
