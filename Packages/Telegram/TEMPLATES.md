# The catalogue

Sixteen templates in three groups. Every example below is real output from
`./bin/telegram render` — if one looks wrong, it *is* wrong, and the command
will show you the same thing.

```bash
./bin/telegram templates                 # the list
./bin/telegram templates --group input   # one group
./bin/telegram render <id> --set k=v     # exactly what would arrive
```

## How to read an entry

Every template declares:

| Field | Meaning |
|---|---|
| `id` | what you pass to `render` and `send` |
| `group` | `input`, `output`, or `interactive` |
| `kind` | the envelope's `kind`: `attention`, `complete`, `alert`, or null |
| `severity` | `info` / `warn` / `error` — drives `{emoji}` |
| `requires` | fields it cannot do without; absent one raises (TG-17) |
| `defaults` | fields it fills in when you do not |

`{emoji}` resolves from severity (🟢 info, 🟡 warn, 🔴 error) and is available to
every template. So is `{template}` and `{severity}`.

---

# input — rendering an event that arrived

For payloads produced by something else. The Poller is the first-class
producer; `generic.event` is the escape hatch so an unmapped payload still gets
through rather than being dropped.

## `poller.settled`
A watched item reached a successful terminal state.
**requires** `key`, `score` · severity `info` · kind `complete`

```
🟢 kaggle settled — 51.210

challenger-2arm slot-1
ref 55881637 · 2026-08-30T12:00
```

`score` is required deliberately. A settle with no result is the KI-04 case the
Poller holds as *pending* rather than reporting — and a source that genuinely
has no result should use `generic.event`, not a settle report with a blank
where the number goes.

## `poller.failed`
A watched item reached an error terminal state.
**requires** `key` · severity `error` · kind `alert`

```
🔴 kaggle FAILED

bank-47 did not complete (status SubmissionStatus.ERROR).
Error: kernel timeout
ref 55881640

A slot was spent — read the run log before retrying.
```

Distinct from a settle on purpose: an errored submission is news, not noise, and
a rail that reports only successes teaches you to read silence as "nothing
happened" when it means "something failed".

## `poller.stale`
An item has been pending past its SLA.
**requires** `key` · severity `warn` · kind `attention`

The distinction this carries: **the watched thing is slow, the watch is fine.**
Without it, a long silence is ambiguous between the two.

## `poller.degraded`
Consecutive fetch failures — still watching, no longer trusted.
severity `warn` · kind `attention`

## `poller.stopped`
The watch ended. severity `error` · kind `alert`

```
🔴 kaggle stopped

reason: max duration reached

NOTHING is watching now. Arm a new watch before the next thing you care about.
```

The single most important message the rail carries. After this, silence means
nobody is watching — not that nothing happened.

## `poller.supervisor_lost`
The session that launched the watch is gone. severity `warn` · kind `attention`

The watch survived; the attention did not. Reports keep arriving with nobody
reading them, and everything looks healthy while it happens.

## `generic.event`
Any source at all. **requires** `title` · severity `info`

```
🟢 Backup completed

482 MB in 41s
```

---

# output — something the studio is saying

## `report`
A finished result. **requires** `title` · severity `info` · kind `complete`

```
🟢 Deploy finished

dripden · 3 files · 41s

harness run 412
```

## `update`
Progress on work still running. **requires** `title` · kind null

```
Deploy finished

dripden · 3 files · 41s

step 3 of 5
```

Deliberately quiet — no emoji, no `kind`. An update is not an event, and
dressing it as one is how a channel becomes unreadable.

## `alert`
Something is wrong and wants eyes now. **requires** `title` · severity `error`

```
🚨 Deploy finished

dripden · 3 files · 41s

Check the run log
```

Use `{action}` for the footer: say what to do, not just what happened.

## `digest`
Many items in one message. **requires** `title`, `body` · kind `complete`

```
⚙️ Deploy finished — 4 items

dripden · 3 files · 41s

last 24h
```

Reach for this instead of N sends. A rail that fires per item trains its reader
to ignore it.

## `handoff`
A session or agent transition. **requires** `title` · kind `attention`

```
🔔 Handoff — Deploy finished

dripden · 3 files · 41s

Next: arm the poller
```

---

# interactive — asking the human

These carry a return path. **Both buttons and polls need
`n8n/telegram-interactive.json`** — the live fan-out silently drops an inline
keyboard (TG-19) and cannot send a poll at all (TG-18). Send them with
`--url-env NOTIFY_INTERACTIVE_URL`.

`callback_data` is `<action>:<entity>:<id>`, capped at 64 UTF-8 bytes and
**refused rather than truncated** when it does not fit (TG-03). Check what
yours encodes to with `render` before shipping.

## `approval`
The human gate. **requires** `title`, `id` · severity `warn`

```
🔐 Approval needed — Deploy dripden to production

3 files changed, harness run #412
```
```
row 1  '✅ Approve' → ok:deploy:run-412
       '❌ Reject'  → no:deploy:run-412
row 2  '⏳ Later'   → def:deploy:run-412
```

Three outcomes, not two. Without a defer, a decision someone is not ready to
make becomes a message they ignore, which is indistinguishable from a rejection
nobody sent.

## `choice`
Pick one of two named options.
**requires** `title`, `id`, `option_a`, `option_b`

```
row 1  '{option_a}' → a:choice:<id>
       '{option_b}' → b:choice:<id>
```

Beyond two or three, use `poll`. A keyboard of eight buttons is unreadable on a
phone.

## `ack`
The triage vocabulary already in use across the studio.
**requires** `title`, `id`

```
row 1  '✅ Attended' → att:<entity>:<id>
       '⏳ Deferred' → def:<entity>:<id>
       '🔕 Mute'     → mute:<entity>:<id>
```

The action codes match the existing `triage-receiver` and `dirnotif-feedback`
receivers deliberately — this is the vocabulary those already route on.

## `poll`
A native Telegram poll. **requires** `question`

```
📊 Which lane next?
   ○ Track A
   ○ Track B
   ○ Track C
```

Options come from an `options` field — a list, or a `|`-separated string so it
works from the CLI:

```bash
./bin/telegram render poll --set 'question=Which lane next?' \
                           --set 'options=Track A|Track B|Track C'
```

Telegram allows 2–10 options at 100 characters each; the template enforces both.
Fewer than two raises rather than silently dropping the widget.

**A native poll needs `TELEGRAM_BOT_TOKEN` in n8n's environment** — n8n's
Telegram node has no `sendPoll`, so the workflow calls the Bot API directly
(TG-22). Without the token the poll still arrives, as a numbered list that names
the degrade. It never silently vanishes.

**A poll answer carries no chat id.** Telegram does not send one, so a poll vote
can only ever be user-allow-listed, never chat-allow-listed (TG-15).

---

# Writing your own

Drop a JSON file in a directory and point at it:

```bash
./bin/telegram render ./my-template.json --set title=x
./bin/telegram send my.template --templates-dir ./my-templates --data event.json
```

`--templates-dir` is searched **before** the bundled catalogue, so a file with a
built-in id overrides it rather than colliding.

```json
{
  "id": "deploy.finished",
  "group": "output",
  "kind": "complete",
  "severity": "info",
  "description": "One line, shown by `telegram templates`.",
  "requires": ["client", "duration"],
  "defaults": { "url": "" },
  "title": "{emoji} {client} deployed",
  "body": "{duration}\n{url}",
  "footer": "",
  "buttons": [[
    { "text": "✅ Looks right", "action": "ok", "entity": "deploy", "id": "{client}" }
  ]]
}
```

Four rules, each bought by an entry in `KNOWN_ISSUES.md`:

1. **Plain prose, no markup.** It is transmitted, not rendered (TG-01) — and
   not stripped either, so `**bold**` shows its asterisks. Content passed in
   from a payload is never edited (TG-23).
2. **Declare `requires`.** It is the only thing separating a data bug from a
   design choice (TG-17).
3. **Keep `entity` and `id` short.** 64 bytes total, including the action and
   two colons (TG-03).
4. **Preview before sending.** `render` shows the chunking, the buttons and the
   encoded callbacks. Everything above is invisible until you look.

An unknown key is warned about, not ignored — a typo'd `titel` would otherwise
leave the template rendering without the thing you thought you configured.
