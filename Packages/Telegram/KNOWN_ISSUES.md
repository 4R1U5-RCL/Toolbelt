# Known issues — how Telegram messaging actually breaks here

Every entry below is a real failure, a real constraint of the live rail, or a
real discrepancy found in the existing code — not a hypothetical. Each names the
signature you would see, why it happens, what this package does about it, and
the column that matters most: **what is still your job**.

The IDs are referenced from the source, so `grep -rn TG-03 telegram/` finds the
code that exists because of an incident. Two entries — TG-11 and TG-14 — are
observations about the surrounding system rather than guards in this package;
they are marked *(no guard here)* and exist so the next person does not
rediscover them the hard way.

| ID | Failure | Prevented by | Still your job |
|---|---|---|---|
| [TG-01](#tg-01) | Markdown arrived as literal asterisks | `plain()` converts markup instead of transmitting it | Write templates in plain prose; preview with `render` |
| [TG-02](#tg-02) | A 2xx was mistaken for a delivered message | `accepted` and `delivered` are separate; `verify` proves the second | Run `telegram verify` before believing a rail works |
| [TG-03](#tg-03) | Buttons rendered fine and did nothing when pressed | 64-byte `callback_data` cap enforced by refusing, never truncating | Keep entity and id short; they are a budget |
| [TG-04](#tg-04) | Long messages were truncated at six different arbitrary limits | UTF-16-aware chunking at Telegram's real 4096 cap | Decide whether a long thing should be a digest instead |
| [TG-05](#tg-05) | Two header families for one HMAC | Both are sent; the receiver accepts either | Do not "tidy up" by dropping one |
| [TG-06](#tg-06) | The documented second auth gate does not exist | Documented honestly; HMAC is treated as the only gate | Do not rely on `X-Notify-Token` for anything |
| [TG-07](#tg-07) | An n8n Code node's edits vanished silently | Every Code node returns new items | Same rule in any node you add |
| [TG-08](#tg-08) | No bot token exists locally | Everything rides the signed webhook | Do not add a direct Bot API path "just for testing" |
| [TG-09](#tg-09) | A bot has exactly one webhook URL | Receiver ships inactive; the trade-off is stated | Decide which receiver owns the bot before activating |
| [TG-10](#tg-10) | A message signed five minutes ago is rejected | Sign at send time, never in advance | Do not queue a signed envelope for later |
| [TG-11](#tg-11) | Two scripts still target a dead workflow name | *(no guard here)* — recorded so it is not re-derived | Fix or retire them in `packages/notify` |
| [TG-12](#tg-12) | An unset chat id silently falls back to a literal | Documented; `check` reports what is configured | Set `TELEGRAM_DEFAULT_CHAT` deliberately |
| [TG-13](#tg-13) | Four runtimes, four emoji conventions, no shared rule | One catalogue, one `SEVERITY_EMOJI` | Add a template rather than a format string |
| [TG-14](#tg-14) | Vestigial email fields in the envelope | *(no guard here)* — not populated by this package | Ignore them; the email rail is Gmail now |
| [TG-15](#tg-15) | Inbound updates are attacker-controlled | Chat and action allow-lists, fail-closed | Set the allow-lists; an empty one allows everything |
| [TG-16](#tg-16) | A secret could reach a log through a careless format | Redacting formatter; query strings stripped from URLs | Never put a token in a config file — use `@env:` |
| [TG-17](#tg-17) | A blank where data should be looked like a quiet success | `requires` separates a data bug from a template bug | Declare the fields a template cannot do without |
| [TG-18](#tg-18) | An interactive feature degraded silently to plain text | `render` says which workflow a template needs | Deploy the interactive workflow before using polls |
| [TG-19](#tg-19) | Inline keyboards were silently discarded — on the live rail, always | A literal `replyMarkup` behind an IF branch, in the new workflow | Send interactive templates with `--url-env NOTIFY_INTERACTIVE_URL` |

---

<a name="tg-01"></a>
## TG-01 — Markdown arrived as literal asterisks

**What you see.** A message reading `*Kaggle settled* — score *51.210*`, with
the asterisks visible. It looks like the sender is broken.

**Why.** The delivery node in `[TEMPLATE] Notification Fan-out` is configured
`parse_mode: "None"`. Telegram is being told not to interpret markup, so markup
is transmitted verbatim. The Slack rail *does* render `*bold*`, so a format
string copied from a Slack sink looks correct right up until it arrives.

**What the package does.** `text.plain()` converts markup to the text a reader
meant — `**done**` becomes `done`, a link becomes `label (url)` — rather than
escaping it or passing it through. Every template renders through it.

**Still your job.** Write templates in plain prose, and run `telegram render`
before shipping one. The preview is exactly what arrives.

---

<a name="tg-02"></a>
## TG-02 — A 2xx was mistaken for a delivered message

**What you see.** A rail that reports success while nobody receives anything.

**Why.** The fan-out webhook responds immediately, before the Telegram node
runs. A 2xx means the workflow *accepted the call*. Delivery happens afterwards
and can fail for reasons the sender never learns: a wrong chat id, a bot removed
from a group, a revoked token.

**What the package does.** `SendResult.accepted` and `SendResult.delivered` are
separate fields, and `send` never sets the second. Only `DeliveryVerifier` may,
by reading the workflow's own execution record and confirming the delivery node
ran without error. `telegram send --verify` does both. The CLI exits **2**, not
1, for "sent but unproven" — distinct from a failure on purpose.

**Still your job.** Prove a new rail once with `--verify`. A rail nobody has
ever confirmed is a rail you are trusting on the strength of a status code.

---

<a name="tg-03"></a>
## TG-03 — Buttons rendered fine and did nothing when pressed

**What you see.** An interactive message that looks perfect. Every press does
nothing, or acts on the wrong record. Nobody notices for weeks, because there is
no error anywhere.

**Why.** Telegram caps `callback_data` at **64 UTF-8 bytes**. Over that, the
send fails or the data is truncated, and a truncated key collides with other
keys sharing its prefix. IN-30 records this happening: `dirnotif` emitted a
two-part `callback_data` while its receiver matched on a different key, and
every button press silently no-opped from go-live.

**What the package does.** `keyboard.encode` **refuses** rather than truncating,
naming the action and the byte count. Encoding and decoding live in one module
so the two halves cannot be maintained apart, and `tests/test_n8n_parity.py`
executes the n8n receiver's JavaScript against the Python decoder to prove they
still agree. The scheme itself is the studio's existing one from
`packages/n8n-templates/src/primitives.ts`, not a new invention.

**Still your job.** Treat 64 bytes as a budget. `att:kaggle:55881637` is 20; a
UUID plus a long entity name will not fit. Prefer short action codes.

---

<a name="tg-04"></a>
## TG-04 — Long messages were truncated at six different arbitrary limits

**What you see.** A report that stops mid-sentence, with no indication anything
was lost.

**Why.** Nothing in the studio chunks. Each caller picked a number and cut
there: 200 chars in `agent-kit`, 2500 in `notify`'s extractor, 200/300/400 in
three places inside `studio-cpu-watchdog` for the same field. Worse, the real
limit is **4096 UTF-16 code units**, not characters — a message of 2500 emoji is
over the cap while `len()` says it is comfortably under.

**What the package does.** `text.tg_len` measures in UTF-16 units. `chunk()`
splits at the largest boundary that fits — paragraph, then line, then word —
numbers the parts, and never splits a surrogate pair. `truncate()` always leaves
a visible marker, because silent truncation is indistinguishable from a message
that had nothing more to say.

**Still your job.** Ask whether a very long message should be a `digest`
instead. Three messages arriving at once is a worse read than one summary.

---

<a name="tg-05"></a>
## TG-05 — Two header families for one HMAC

**What you see.** A signature that verifies from one caller and not another,
with identical signing code.

**Why.** The studio grew two naming conventions for the same scheme:
`packages/notify/src/client.mjs` sends `x-notify-signature` /
`x-notify-timestamp`, while the SEO-suite builders and `hooks.ts` send
`x-n8n-signature` / `x-n8n-timestamp`. Both are HMAC-SHA256 over
`` `${ts}.${body}` ``. The live receiver reads
`headers['x-n8n-signature'] || headers['x-notify-signature']`, so it accepts
either — but a receiver built from the older builder source might not.

**What the package does.** Sends **both**, with the same value. Compatible with
every receiver in the estate, and asserted in `tests/test_seam.py`.

**Still your job.** Do not "clean this up" by dropping one family. The
redundancy is the compatibility.

---

<a name="tg-06"></a>
## TG-06 — The documented second auth gate does not exist

**What you see.** Documentation describing two gates. One of them.

**Why.** `packages/notify`'s docs describe `X-Notify-Token` as a Header Auth
gate rejecting bad calls at the edge before any node runs. The deployed
`[TEMPLATE] Notification Fan-out` webhook node has **no `authentication`
configured**. The header is accepted and ignored; the HMAC in the Code node is
the only real check.

**What the package does.** Sends the header for compatibility, and says plainly
in `seam.py` that it is not security. The HMAC is treated as the sole gate,
which is what it is.

**Still your job.** Do not reason about this rail's security on the basis of the
token header. If a second gate is wanted, add it to the workflow — this is a
`packages/notify` fix, not one this package can make.

---

<a name="tg-07"></a>
## TG-07 — An n8n Code node's edits vanished silently

**What you see.** A delivery node reading an item without the field the previous
Code node just set. No error.

**Why.** n8n freezes Code-node input items (IN-25). In-place mutation is
silently dropped.

**What the package does.** Every Code node in `n8n/` builds and **returns** new
items via `Object.assign({}, j, {...})`, never mutating the input.

**Still your job.** Same rule for any node you add. It fails silently, so
nothing will tell you.

---

<a name="tg-08"></a>
## TG-08 — No bot token exists locally

**What you see.** No way to call `api.telegram.org` from the container.

**Why.** By design. The bot token lives only in the n8n credential `[STUDIO]
Telegram Bot`; there is no `TELEGRAM_BOT_TOKEN` in `/studio/.env`. This is the
right arrangement — the credential is held by the always-on service that needs
it — but it means the Bot API is unreachable from here.

**What the package does.** Treats the signed webhook as the only path. There is
no direct-send code to fall back to and no configuration that would enable one.

**Still your job.** Do not add a direct Bot API path for convenience. It would
mean a bot token in the container, which is the thing this avoids.

---

<a name="tg-09"></a>
## TG-09 — A bot has exactly one webhook URL

**What you see.** Three receiver workflows on three paths, at most one of which
can be receiving anything.

**Why.** Telegram's `setWebhook` sets a single URL per bot. `triage-receiver`,
`dirnotif-feedback` and this package's receiver cannot all be live at once.

**What the package does.** Ships `[STUDIO] Telegram Receiver` **inactive** and
states the trade-off. It is designed to *replace* the bespoke receivers — it
decodes the same scheme and routes generically — rather than to sit alongside
them.

**Still your job.** Activating it is a decision about which receiver owns the
bot. Check what `getWebhookInfo` currently returns first. That call needs the
bot token, so it happens in n8n, not here (TG-08).

---

<a name="tg-10"></a>
## TG-10 — A message signed five minutes ago is rejected

**What you see.** A 401 from the fan-out on a message whose signature is
provably correct.

**Why.** The receiver enforces a 300-second skew window on the signed
timestamp, which is what makes a captured envelope non-replayable.

**What the package does.** Signs at send time, from an injected clock. There is
no code path that signs an envelope and holds it.

**Still your job.** Do not build a queue of pre-signed envelopes. Queue the
*payload* and sign on the way out. Also check host clock drift if signatures
start failing in bulk.

---

<a name="tg-11"></a>
## TG-11 — Two scripts still target a dead workflow name

*(no guard here — recorded so it is not re-derived)*

`packages/notify/scripts/provision-n8n.mjs` provisions a workflow named
`[STUDIO_NOTIFICATIONS] Outbound Alerts` at path `studio-notify`, and
`scripts/earned-pass.mjs` searches for that name via the n8n API. Both refer to
the **retired n8n Cloud instance**. The live receiver is `[TEMPLATE]
Notification Fan-out` (`sxqF7MO79IOYMYN4`) at path `notification-fanout` on the
self-hosted instance, built from
`clients/_n8n-templates/builders/notification-fanout.ts`.

Running the provisioner would re-create the dead workflow. The earned-pass
script cannot find the live one and so cannot prove anything about it.

**Still your job.** Fix or retire both in `packages/notify`. Out of scope here;
this package deliberately does not touch that package.

---

<a name="tg-12"></a>
## TG-12 — An unset chat id silently falls back to a literal

**What you see.** Messages arriving somewhere you did not configure.

**Why.** The workflow resolves the destination as
`b.chat_id || $env.TELEGRAM_DEFAULT_CHAT || '8859170398'`. With the env var
unset, the hard-coded literal wins and delivery *succeeds* — to whatever that id
points at.

**What the package does.** Documents it, sends an explicit `chat_id` when one is
given, and `telegram check` reports what is actually configured.

**Still your job.** Set `TELEGRAM_DEFAULT_CHAT` in the n8n environment
deliberately, and pass `--chat-id` when a message must go somewhere specific.

---

<a name="tg-13"></a>
## TG-13 — Four runtimes, four emoji conventions, no shared rule

**What you see.** 🟢 in one message, ⚙️ in another for the same class of event,
and no way to change either without editing four files in three languages.

**Why.** Message composition lives at the call site in `notify/bin/notify.mjs`
(Node), `agent-kit/src/notify.ts` (TypeScript), seventeen n8n Code nodes
(JavaScript), and `studio-cpu-watchdog` (Python). They agreed by copy-paste,
and copy-paste does not stay agreed.

**What the package does.** One catalogue, one `SEVERITY_EMOJI` map, one place to
change the house style. A message shape is a JSON file.

**Still your job.** When a new message shape is needed, add a template. Adding a
format string to a caller is how this happened.

---

<a name="tg-14"></a>
## TG-14 — Vestigial email fields in the envelope

*(no guard here — recorded so it is not mistaken for a feature)*

The fan-out's `Format` node computes `__email` with `from`, `to`, `subject`, but
the workflow has no email node — the only delivery path is Telegram. The fields
are left over from a Resend-era fan-out. Resend is deprecated; Gmail is the
email rail.

This package never populates them. If email delivery is wanted, that is a
workflow change and a decision about which rail, not an envelope field.

---

<a name="tg-15"></a>
## TG-15 — Inbound updates are attacker-controlled

**What you see.** Nothing, until something acts on an update it should not have.

**Why.** Anyone who discovers the bot can send it a message. `callback_data`
looks trustworthy because the bot generated it, but a crafted update can carry
any string at all. This is the same untrusted-ingress posture the Slack rail
already has.

**What the package does.** `inbound.decode_update` takes allow-lists for chat
ids and for actions, and **fails closed** — an update that cannot be matched
against the gate is untrusted, not admitted. A poll answer carries no chat id at
all, so a chat allow-list can never admit one, and that is reported rather than
worked around. Nothing in `inbound.py` executes anything; it returns a
description. The n8n receiver additionally checks Telegram's
`X-Telegram-Bot-Api-Secret-Token`, which is the only real gate available on that
endpoint since Telegram signs nothing.

**Still your job.** Set the allow-lists. An empty one means "allow anything",
which is only safe on a bot nobody else knows about — and you cannot know that.

---

<a name="tg-16"></a>
## TG-16 — A secret could reach a log through a careless format

**What you see.** A shared notify secret in a log file that someone pastes into
a ticket.

**Why.** No code path deliberately logs a token, but one `%s` of a request
header would do it, and the URL query string is a classic carrier.

**What the package does.** Every credential read through the resolver is
registered with the redactor, and the log formatter replaces registered values
with `***` — including inside exception text. `_safe_url` strips query strings
before logging. `telegram check` prints names and presence, never values.

**Still your job.** Never put a token in a config file. Use `@env:NAME`.

---

<a name="tg-17"></a>
## TG-17 — A blank where data should be looked like a quiet success

**What you see.** `🟢 kaggle settled —` with no score. It reads like a settle
with nothing to report.

**Why.** Rendering is deliberately total: a template referencing a field the
payload lacks renders it empty rather than raising, because a delivery failing
six hours into a watch is worse than a slightly wrong message. But that same
property makes a *missing* field invisible.

**What the package does.** A template declares `requires`. A declared field that
is absent raises by default — while you are authoring, where it is cheap — and
in `--lenient` mode renders anyway while recording the gap in `missing_fields`.
An empty string counts as missing; **zero does not**, because a score of 0 is a
real result.

**Still your job.** Declare the fields a template cannot do without. `requires`
is the only thing that distinguishes a data bug from a design choice.

---

<a name="tg-18"></a>
## TG-18 — An interactive feature degraded silently to plain text

**What you see.** A poll template that arrives as an ordinary message, with the
question but no voting widget.

**Why.** The live fan-out's Telegram node is hard-wired to `sendMessage`. It
reads `meta.reply_markup` (so buttons work) but knows nothing about
`meta.poll` — an envelope carrying one is delivered as text, successfully, with
no error.

**What the package does.** Ships `[STUDIO] Telegram Interactive`, which routes
on `meta.poll` and adds a `sendPoll` branch. `telegram render` states which
workflow a poll template needs, and the `poll` template's own description says
so.

**Still your job.** Deploy and activate `n8n/telegram-interactive.json` before
relying on polls, and point the sender at it with
`--url-env NOTIFY_INTERACTIVE_URL`. Buttons need the same treatment — see TG-19,
which is the same class of failure and was found the same way.

---

<a name="tg-19"></a>
## TG-19 — Inline keyboards were silently discarded, on the live rail, always

**What you see.** An interactive message arrives as ordinary text. No buttons.
No error anywhere: the webhook returns 200, the workflow's every node runs
green, and the execution record shows the keyboard being built correctly one
node before it vanishes.

**How it was found.** Sending the `approval` template through the live fan-out
during this package's smoke test. The delivery was confirmed by execution record
(TG-02) and looked like a pass — until the message was actually read, and the
buttons were not there. The `Format` node's output showed `__hasKb: true` with a
well-formed `__kb`; Telegram's response carried no `reply_markup` at all.

**Why.** The `Deliver` node sets:

```
replyMarkup:    "={{ $json.__hasKb ? 'inlineKeyboard' : 'none' }}"
inlineKeyboard: "={{ $json.__kb }}"
```

n8n's `inlineKeyboard` parameter is gated by `displayOptions: { show: {
replyMarkup: ['inlineKeyboard'] } }`. **`displayOptions` are evaluated against
the raw parameter value, not the resolved one.** The raw value here is the
literal string `"={{ $json.__hasKb ? … }}"`, which is not `'inlineKeyboard'`, so
the keyboard parameter is never read. The node sends the text and drops the
markup.

This is not specific to one workflow. It was true of **every** keyboard-capable
Telegram node in the estate — the fan-out's `Deliver`, and this package's first
copy of it, which inherited the pattern by imitation. Which means inline
keyboards have never actually worked on this rail. It also recasts part of
IN-30: the `dirnotif` buttons were investigated as a `callback_data` key
mismatch, and that mismatch was real, but on the current configuration those
buttons would not have rendered at all.

**What the package does.** `[STUDIO] Telegram Interactive` branches on `__hasKb`
with an **IF node** and routes to one of two Telegram nodes, each with a
**literal** `replyMarkup` — `"inlineKeyboard"` on one, `"none"` on the other.
Two nodes instead of one conditional, because the conditional is the bug.

**Still your job.** Two things. Send interactive templates with `--url-env
NOTIFY_INTERACTIVE_URL` so they reach the workflow that can carry them. And when
adding any Telegram node anywhere: **`replyMarkup` is a literal, never an
expression.** Branch instead. The failure mode gives you nothing to notice.
