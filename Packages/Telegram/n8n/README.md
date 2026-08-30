# The n8n side

## What is already there, and why it is not touched

`[TEMPLATE] Notification Fan-out` (`sxqF7MO79IOYMYN4`) is live, active, and
several plugins depend on it. It receives the signed envelope, verifies the
HMAC, and delivers to Telegram.

It reads `meta.reply_markup.inline_keyboard` and builds the keyboard correctly —
and then **loses it**. Measured on a real send: the `Format` node emitted
`__hasKb: true` with a well-formed `__kb`, and Telegram's response carried no
`reply_markup` at all. The message arrived as plain text, successfully, with no
error at any node (TG-19).

Nothing in this directory modifies it. The fix lives in the new workflow
instead, because changing a live shared dependency is a bigger decision than
this package should make on its own.

## The two things it cannot do

| | Why |
|---|---|
| **Attach an inline keyboard** | Its `replyMarkup` is set from an expression. That parameter gates `inlineKeyboard` through `displayOptions`, which n8n evaluates against the RAW parameter — an expression never equals `'inlineKeyboard'`, so the keyboard is skipped (TG-19) |
| **Send a native poll** | Its Telegram node is hard-wired to `sendMessage`. An envelope carrying `meta.poll` is delivered as plain text, successfully, with no error (TG-18) |
| **Receive an answer** | It is send-only. Button presses arrive as Telegram *updates* on the bot's webhook, which is a different endpoint entirely |

So this directory adds two workflows, both deployed **inactive**:

```
[STUDIO] Telegram Interactive          — sendMessage OR sendPoll, from one envelope
  Webhook → Verify HMAC → Auth Gate ─┬→ Shape → Poll or Message ─┬→ Send Poll ────────┐
                                     │                           │                    │
                                     │                           └→ Has Buttons? ─┬→ Send With Buttons
                                     │                                            └→ Send Message
                                     └→ Reject 401                                        │
                                                        Sign Response ← ─────────────────┘
                                                              ↓
                                                       Respond Delivered

  Two send nodes, not one with a conditional: `replyMarkup` must be a LITERAL
  for n8n to expose the keyboard parameter at all (TG-19).

[STUDIO] Telegram Receiver             — callback_query AND poll_answer
  Telegram Webhook → Decode + Gate → Was A Button? ─┬→ Answer Callback ─┐
                                                    └───────────────────┴→ Respond 200
```

`build_workflows.py` regenerates both:

```bash
python3 n8n/build_workflows.py interactive > n8n/telegram-interactive.json
python3 n8n/build_workflows.py receiver    > n8n/telegram-receiver.json
```

## Parity is enforced, not hoped for

The receiver's `Decode + Gate` node and `telegram/inbound.py` are two
implementations of one contract in two languages. That arrangement is exactly
what produced IN-30, so it is **tested**: `tests/test_n8n_parity.py` extracts the
JavaScript from the workflow JSON, executes it in `node` against the same
updates as the Python decoder, and compares the answers — including an id
containing colons, the empty-entity single-column form, the chat allow-list, and
the poll-answer case that no chat allow-list can admit.

The same test runs the sender's `Shape` node against real
`template.Message.meta()` output, so the two ends of the envelope cannot drift
either.

If you change the encoding in one place, the suite fails. That is the point.

## Deploying

```bash
set -a; . /studio/.env; set +a
curl -s -X POST -H "X-N8N-API-KEY: $N8N_API_KEY" -H "Content-Type: application/json" \
     --data-binary @n8n/telegram-interactive.json "$N8N_BASE_URL/api/v1/workflows"
```

Both reuse the existing `[STUDIO] Telegram Bot` credential
(`pojHLD8xi2lxHgNp`), so **no credential needs creating** — unlike the Poller's
n8n tier, nothing here requires a token to be entered.

### `[STUDIO] Telegram Interactive` — safe to activate

Path `/webhook/telegram-interactive`. It is a strict superset of the fan-out for
this package's envelopes: same HMAC contract, same `NOTIFY_FANOUT_SECRET`, same
`meta.reply_markup` handling, plus the poll branch. Activating it takes nothing
away from anything else, because nothing else points at that path.

Set env in n8n if you have not already: `TELEGRAM_DEFAULT_CHAT` (TG-12 — it
falls back to a hard-coded literal), and `NOTIFY_FANOUT_SECRET` (already set,
since the fan-out uses it).

**Until this is active, nothing interactive works** — not polls, and not
buttons. Callers reach it with
`./bin/telegram send <template> --url-env NOTIFY_INTERACTIVE_URL`.

### `[STUDIO] Telegram Receiver` — read TG-09 before activating

Path `/webhook/telegram-receiver`.

**A Telegram bot has exactly one webhook URL.** Two receivers already exist —
`triage-receiver` and `dirnotif-feedback` — on different paths, so at most one
of them is currently receiving anything. Pointing the bot at this one *takes the
URL away* from whichever holds it.

That is deliberate: this receiver is meant to **replace** the bespoke ones. It
decodes the same `<action>:<entity>:<id>` scheme, and its `att` / `def` / `mute`
action codes are the same vocabulary they route on. But it does not yet perform
their side effects (their Supabase writes), so swapping the webhook over would
record the answer without doing what those workflows do with it.

Before activating:

1. Check what the bot's webhook currently points at (`getWebhookInfo` — needs
   the bot token, so run it from n8n, not from here: TG-08).
2. Decide whether this receiver replaces the incumbent or waits until it can
   carry the incumbent's side effects too.
3. Set `TELEGRAM_WEBHOOK_SECRET` in n8n and pass the same value as
   `secret_token` to `setWebhook`. **Telegram signs nothing** — that echoed
   header is the only real gate this endpoint has.
4. Set `TELEGRAM_ALLOWED_CHATS` (comma-separated). Empty means allow any chat,
   which is only safe on a bot nobody else knows about, and you cannot know
   that (TG-15).

### Why it answers 200 to a hostile update

Telegram retries any non-2xx. Answering 401 to a crafted update earns a retry
loop rather than stopping one, so the receiver always responds 200 and records
the refusal in the `trusted` field instead. The refusal is in the data, not the
status code.

## Where answers go, for now

`$getWorkflowStaticData('global')`, keyed `entity:id`, pruned to the most recent
500 — the same mechanism `[OPERORCH] Runner Watcher` already relies on. It
survives restarts, which is enough for v1's "record the verdict".

It is **not** enough for a script to block on, which is why `telegram await` is
not in v1. That needs a real answer store, and there are three plausible ones
(a file, Supabase, or a callback back out to the caller). Picking one is a
decision, not a detail.
