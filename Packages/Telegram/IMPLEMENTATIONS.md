# Implementation guide — wiring a caller to the seam

The seam never changes. Implementing a Telegram rail means answering three
questions and writing the answers into a JSON file.

1. **Is this rendering something that arrived, saying something, or asking
   something?** That picks the group — `input`, `output`, `interactive`.
2. **What fields does the message need, and which of them can it not do
   without?** The second list is `requires` (TG-17).
3. **If it asks something, what identifies the thing being decided?** That is
   the `<entity>:<id>` half of the callback, and it has 64 bytes to fit in
   (TG-03).

Answer those and the rest — signing, both header families, plain-text
conversion, chunking, the delivery ledger of proof, the redactor — you get
unchanged.

---

## The five commands

```bash
./bin/telegram templates                       # what exists
./bin/telegram render <id> --set k=v           # exactly what would arrive (offline)
./bin/telegram check                           # do the credentials resolve?
./bin/telegram send <id> --data event.json     # send it
./bin/telegram verify --request-id <id>        # was it actually delivered?
./bin/telegram decode 'att:kaggle:55881637'    # what did that button mean?
```

`render` is the one to reach for first and most often. It is offline, it sends
nothing, and it shows the chunking, the buttons and the encoded callbacks —
which is where every trap in `KNOWN_ISSUES.md` lives.

---

## Worked example: the Poller

The Poller produces exactly the events this package's `input` group renders, and
the two are deliberately **not coupled**. The Poller's rule is no paths into
other packages (its KI-10), so it keeps its own envelope implementation and
`tests/test_conformance.py` here holds both to the same bytes.

### The clean wiring: the Poller's `command` sink

The Poller already has a sink that shells out with the event on stdin. That is
the whole integration — no new code in either package.

```json
{
  "type": "command",
  "name": "telegram",
  "command": ["/studio/scratch/toolbelt/Toolbelt/Packages/Telegram/bin/telegram",
              "send", "poller.settled", "--data", "-", "--source", "kaggle-poller"],
  "reasons": ["settled"]
}
```

One sink per reason, because each maps to its own template:

| Poller `reason` | Template |
|---|---|
| `settled` | `poller.settled` |
| `failed` | `poller.failed` |
| `stale` | `poller.stale` |
| `degraded` | `poller.degraded` |
| `watch_ended`, `watch_failed` | `poller.stopped` |
| `supervisor_lost` | `poller.supervisor_lost` |

The Poller's event context arrives as the payload: `key`, `state`, `title`,
`body`, `reason`, `severity`, plus the source's own fields. For the Kaggle
source those are `score`, `date`, `description`, `error`, `status`, `filename`.
The template names map onto them directly.

### The alternative: keep using `notify_webhook`

The Poller's built-in `notify_webhook` sink already reaches Telegram, and it
still works. Use it when you want the Poller to stay entirely self-contained —
for instance on a host where this package is not checked out. You give up the
template catalogue and the plain-text conversion, and you compose the text in
the Poller config instead.

Both are legitimate. The conformance test is what makes having both safe.

---

## Worked example: a human gate in a script

```bash
#!/usr/bin/env bash
set -euo pipefail

RUN_ID="run-$(date +%s)"
./bin/telegram send approval \
  --set "title=Deploy dripden to production" \
  --set "body=3 files changed, harness run 412" \
  --set "id=$RUN_ID" --set "entity=deploy" \
  --source "harness" --verify
```

`--url-env NOTIFY_INTERACTIVE_URL` is not optional here. The live fan-out drops
an inline keyboard silently and delivers plain text (TG-19, TG-20), so without
that flag this reads as a notification with no way to answer it.

The press comes back: `[STUDIO] Telegram Receiver` decodes it, records the
verdict under `entity:id`, and answers the callback so the button stops
spinning.

What v1 does *not* do is **block** until that happens. A blocking `telegram
await` needs a durable answer store — three plausible ones, so it is a decision
rather than a detail — and is deliberately deferred. Until then an approval is a
notification with a recorded verdict, not a gate a script can wait on. Say that
plainly to whoever is relying on it.

---

## Worked example: replacing a hand-rolled format string

The seventeen SEO-suite n8n builders each carry their own:

```js
'📊 GSC CSV — ' + rows.length + ' rows ingested for ' + property + '. ' + ...
```

As a template:

```json
{
  "id": "seo.gsc-csv",
  "group": "output",
  "kind": "complete",
  "severity": "info",
  "description": "GSC CSV ingestion summary.",
  "requires": ["property", "rows"],
  "defaults": { "ctr_findings": "0", "cannibalization_findings": "0" },
  "title": "📊 GSC CSV — {rows} rows ingested for {property}",
  "body": "{ctr_findings} CTR opportunity findings\n{cannibalization_findings} cannibalization findings"
}
```

The gain is not brevity. It is that the next change to how these read happens
once, in a file, previewable offline — instead of seventeen times across three
languages, unverifiable until each one next fires.

---

## Adding a template

1. Write the JSON (see [TEMPLATES.md](TEMPLATES.md#writing-your-own)).
2. `./bin/telegram render ./my.json --set …` until it reads right.
3. Drop it in `templates/`, or keep it beside your caller and pass
   `--templates-dir`. A local directory is searched **first**, so you can
   override a bundled template rather than colliding with it.
4. Add a case to `tests/test_template.py` if it does anything unusual.

---

## From Python

```python
from telegram import Catalogue, Seam
from telegram.envfile import EnvResolver

message = Catalogue().load().get("report").render({"title": "Deploy finished"})
result = Seam(EnvResolver("/studio/.env"), source="harness").send(
    message=message.text, kind=message.template.kind, meta=message.meta())

if not result.accepted:
    log.warning("telegram rail down: %s", result.note)   # never raises
```

`send` never raises. A notification is not the work, and a caller reporting that
a deploy failed must not itself fail because the notifier is down. The outcome
is in the return value, and failures are loud in the log — never silent
successes.

To prove delivery rather than acceptance:

```python
from telegram import DeliveryVerifier

verdict = DeliveryVerifier(resolver).confirm(
    request_id=result.request_id, wait_seconds=20)
if not verdict.ok:
    log.warning("not confirmed delivered: %s", verdict.note)
```

`Verdict.UNAVAILABLE` means *cannot tell* — no n8n API credentials — and is
deliberately distinct from `FAILED`. An unverifiable send is never assumed good.

---

## Environment

Read from `/studio/.env` by default (`--env-file` to change it). Names only; the
package never prints a value, and `telegram check` reports presence.

| Name | For | Required |
|---|---|---|
| `NOTIFY_WEBHOOK_URL` | the fan-out endpoint | yes |
| `NOTIFY_TOKEN` | the token header, and the HMAC key when no secret is set | yes |
| `NOTIFY_SECRET` | the HMAC key, if it differs from the token | no |
| `N8N_BASE_URL`, `N8N_API_KEY` | delivery verification | only for `verify` |

Two things live in the **n8n** environment, not here: `TELEGRAM_DEFAULT_CHAT`
(the destination, which falls back to a hard-coded literal if unset — TG-12) and
`NOTIFY_FANOUT_SECRET` (the receiver's half of the HMAC; it must equal whichever
of `NOTIFY_SECRET`/`NOTIFY_TOKEN` you sign with).

There is no `TELEGRAM_BOT_TOKEN` anywhere in the container, deliberately — which
is why everything rides the webhook and not the Bot API (TG-08).

---

## Choosing a destination workflow

| You need | Point at | `--url-env` | State |
|---|---|---|---|
| Plain text | `[TEMPLATE] Notification Fan-out` | *(default)* | live — proven |
| Buttons | `[STUDIO] Telegram Interactive` | `NOTIFY_INTERACTIVE_URL` | live — proven |
| A native poll | `[STUDIO] Telegram Interactive` | `NOTIFY_INTERACTIVE_URL` | live — needs `TELEGRAM_BOT_TOKEN` in n8n, else degrades to text (TG-22) |
| To receive a press or a vote | `[STUDIO] Telegram Receiver` | — | live — proven |

**Buttons are not free on the default rail.** The live fan-out cannot attach an
inline keyboard at all — it builds one correctly and then discards it, silently
(TG-19, TG-20). Everything interactive goes through
`[STUDIO] Telegram Interactive`.

See [n8n/README.md](n8n/README.md) for what activating each costs — particularly
TG-09, since a bot has exactly one webhook URL and two other receivers already
exist.
