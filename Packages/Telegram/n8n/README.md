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
| **Send a native poll** | n8n's Telegram node has **no `sendPoll` operation at all** — configuring one answers `Not Found` from the Bot API. A poll must be a direct HTTP call, which needs a bot token in n8n's env (TG-18, TG-22) |
| **Receive an answer** | It is send-only. Button presses arrive as Telegram *updates* on the bot's webhook, which is a different endpoint entirely |

So this directory adds two workflows, both now deployed and **ACTIVE**:

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
  Telegram Trigger → Decode + Gate → Was A Button? ─→ Answer Callback

  A Telegram TRIGGER, not a webhook: n8n calls setWebhook itself (no bot token
  needed anywhere) and answers Telegram correctly, so there is no way to return
  a non-2xx and earn a retry storm (TG-21).
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

Set env in n8n if you have not already:

* `TELEGRAM_DEFAULT_CHAT` — TG-12, it falls back to a hard-coded literal;
* `NOTIFY_FANOUT_SECRET` — already set, the fan-out uses it;
* `TELEGRAM_BOT_TOKEN` — **only needed for native polls** (TG-22). The same
  token as the `[STUDIO] Telegram Bot` credential. Without it a poll is
  delivered as a numbered list that names the degrade, rather than failing.

**Until this is active, nothing interactive works** — not polls, and not
buttons. Callers reach it with
`./bin/telegram send <template> --url-env NOTIFY_INTERACTIVE_URL`.

### `[STUDIO] Telegram Receiver` — now owns the bot's webhook

It is a **Telegram Trigger**, so activation *is* the wiring: n8n calls
`setWebhook` itself using the stored credential. No bot token passes through
anyone's hands (TG-08), and there is no manual API call to get wrong.

**A Telegram bot has exactly one webhook URL** (TG-09), so activating this took
it from `dirnotif-feedback`. That cost nothing, and the evidence is worth
keeping: **every execution `dirnotif-feedback` and `triage-receiver` have ever
run ends at `Reject 401`.** Both are generic webhooks guarded by an HMAC check,
and Telegram does not sign its updates, so the check can never pass. The inbound
half of this rail had never worked (TG-21).

That also means this receiver does not yet carry those workflows' side effects
(their Supabase writes) — but there were no working side effects to preserve. If
you want them, port them onto this receiver rather than switching back.

Configuration, both optional:

* `TELEGRAM_ALLOWED_CHATS` — comma-separated. **Unset, it fails closed to the
  owner's chat**, because an unconfigured allow-list on a bot anyone can find is
  not a gate. Set it to widen.
* `TELEGRAM_WEBHOOK_SECRET` — only meaningful on a generic-webhook deployment,
  where `setWebhook` was given a `secret_token`. On the trigger path n8n owns the
  endpoint and there are no headers to check. The check discriminates on the
  transport, not on whether the header is present, so it cannot be bypassed by
  omitting it.

### Why a refusal is never a status code

Telegram retries any non-2xx — one press against the old receiver produced ten
executions in seventy seconds. The trigger answers Telegram itself, so this
workflow has no way to return an error at all. A refused update is recorded in
the `trusted` field and goes no further.

## Where answers go, for now

`$getWorkflowStaticData('global')`, keyed `entity:id`, pruned to the most recent
500 — the same mechanism `[OPERORCH] Runner Watcher` already relies on. It
survives restarts, which is enough for v1's "record the verdict".

It is **not** enough for a script to block on, which is why `telegram await` is
not in v1. That needs a real answer store, and there are three plausible ones
(a file, Supabase, or a callback back out to the caller). Picking one is a
decision, not a detail.
