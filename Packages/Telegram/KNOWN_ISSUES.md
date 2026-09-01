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
| [TG-19](#tg-19) | Inline keyboards were silently discarded — on the live rail, always | A literal `replyMarkup`, plus TG-20 | Send interactive templates with `--url-env NOTIFY_INTERACTIVE_URL` |
| [TG-20](#tg-20) | A `fixedCollection` cannot be filled from an expression | Literal keyboard structure, expressions only at the leaves | Keep to three buttons; overflow is counted, not silent |
| [TG-21](#tg-21) | Every inbound callback was rejected 401, then retried into a storm | A Telegram Trigger, which owns its endpoint and answers correctly | Only one receiver can own the bot — decide which |
| [TG-22](#tg-22) | A poll errored `Not Found` — n8n's Telegram node has no `sendPoll` | A direct Bot API call, degrading to readable text without a token | Set `TELEGRAM_BOT_TOKEN` in n8n for real polls |
| [TG-23](#tg-23) | Stripping inert markdown silently corrupted content | `plain()` flattens structure only; inline delimiters are left alone | Write templates in plain prose — the rail cannot render markup |
| [TG-24](#tg-24) | The response signature was verified and then ignored | A present-but-wrong signature now fails the send | Nothing — but do not re-soften it without measuring first |

---

<a name="tg-01"></a>
## TG-01 — Markdown arrived as literal asterisks

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

**What you see.** A message reading `*Kaggle settled* — score *51.210*`, with
the asterisks visible. It looks like the sender is broken.

**Why.** The delivery node in `[TEMPLATE] Notification Fan-out` is configured
`parse_mode: "None"`. Telegram is being told not to interpret markup, so markup
is transmitted verbatim. The Slack rail *does* render `*bold*`, so a format
string copied from a Slack sink looks correct right up until it arrives.

**What the package does.** `text.plain()` flattens line-level *structure* —
heading hashes, blockquote markers, fence lines, rules — and turns a link into
`label (url)` so both halves survive. It deliberately does **not** touch inline
delimiters; see TG-23 for why removing them was a mistake.

**Still your job.** Write templates in plain prose, and run `telegram render`
before shipping one. The preview is exactly what arrives.

---

<a name="tg-02"></a>
## TG-02 — A 2xx was mistaken for a delivered message

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

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
and routes to Telegram nodes with a **literal** `replyMarkup` — `"inlineKeyboard"`
or `"none"`. Nodes instead of one conditional, because the conditional is the bug.

**This fix alone was not enough.** Making `replyMarkup` literal and leaving the
keyboard itself as an expression produced exactly the same silent failure — see
TG-20, which is the other half and was found by hard-coding a keyboard to see
whether anything could render at all.

**Still your job.** Send interactive templates with `--url-env
NOTIFY_INTERACTIVE_URL`. And when adding any Telegram node anywhere:
**`replyMarkup` is a literal, never an expression.** The failure mode gives you
nothing to notice.

---

<a name="tg-20"></a>
## TG-20 — A `fixedCollection` cannot be filled from an expression

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

**What you see.** Identical to TG-19, and reached immediately after fixing it: a
literal `replyMarkup: "inlineKeyboard"`, a correct keyboard object in the item,
`Send With Buttons` running green — and Telegram's response with no
`reply_markup`. Plain text again.

**How it was found.** By replacing the whole keyboard with a **hard-coded** one
and sending it. That message arrived with buttons. So the structure was fine and
the *expression* was the problem, which is a one-experiment answer to a question
that could otherwise have absorbed an afternoon.

**Why.** `inlineKeyboard` is a `fixedCollection` parameter. n8n resolves the
declared nested shape — `rows` → `row` → `buttons` → `{text, additionalFields}` —
from the node's own parameter tree. Handing it `={{ $json.__kb }}` gives it an
expression where it expects that tree, and it finds no rows to walk. As with
TG-19: no error, no warning, message delivered.

**What the package does.** The structure is literal in the node and only the
leaves are expressions:

```
"inlineKeyboard": {"rows": [{"row": {"buttons": [
    {"text": "={{ $json.__b1text }}",
     "additionalFields": {"callback_data": "={{ $json.__b1data }}"}}, …]}}]}
```

Which makes the button count **structural**. So the `Shape` node flattens the
template's keyboard into `__b1text`/`__b1data`…, sets `__btnCount`, and a Switch
routes to `Send 1 Button`, `Send 2 Buttons` or `Send 3 Buttons`. One row of up
to three, which is also as many as reads well on a phone.

**Still your job.** Keep interactive templates to three buttons. A fourth is
**counted, not silently dropped** — `__btnDropped` records it — because a button
that never appears is a decision the human was never offered. If you need more,
add a fourth node and a Switch rule, or use a poll.

---

<a name="tg-21"></a>
## TG-21 — Every inbound callback was rejected 401, then retried into a storm

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

**What you see.** Buttons that do nothing when pressed. On the n8n side, a
receiver workflow with executions — so it *looks* like traffic is arriving and
being handled.

**How it was found.** A real button press during this package's round-trip test.
The callback `ok:tgpkg:proof-3` reached n8n and ended at `Reject 401`. Checking
the history: **every execution of `dirnotif-feedback` and `triage-receiver`, for
as far back as the API returns, ends at `Reject 401`.** Neither has ever
successfully processed a callback.

**Why, twice.**

*The gate.* Both are generic Webhook nodes guarded by an HMAC verify. **Telegram
does not sign its updates** — it has no shared secret with the receiver and no
signature header. The check can never pass. The intent was there: `setWebhook`
accepts a `secret_token` echoed back as `X-Telegram-Bot-Api-Secret-Token`, and
`/studio/.env` even holds a `DIRNOTIF_TG_WEBHOOK_SECRET`. The receiver just
checks the wrong thing.

*The storm.* Telegram retries any non-2xx. One press produced **ten executions
in seventy seconds**, all 401. A receiver that refuses with an error code earns
traffic rather than stopping it.

**What the package does.** `[STUDIO] Telegram Receiver` is built on a **Telegram
Trigger**, not a generic Webhook node, which changes three things at once:

* n8n calls `setWebhook` itself on activation, so pointing the bot at it needs no
  bot token in anyone's hands (TG-08) and no manual API call;
* n8n owns the endpoint and answers Telegram correctly, so there is no path to
  returning a non-2xx and no retry storm;
* the gate that remains is a **chat allow-list that fails closed** — unset, it
  admits only the owner's chat, because an unconfigured allow-list on a bot
  anyone can find is not a gate.

That last point is a deliberate divergence from `inbound.decode_update`, which
hard-codes nothing and takes its allow-list from the caller — right for a
library, wrong for a public endpoint. `tests/test_n8n_parity.py` asserts both
behaviours so the difference stays intentional.

**Still your job.** A bot has one webhook URL (TG-09), so activating this takes
it from the incumbent. Here that cost nothing, because the incumbent had never
worked — but check the execution history before assuming the same elsewhere.

---

<a name="tg-22"></a>
## TG-22 — A poll errored `Not Found`: n8n's Telegram node has no `sendPoll`

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

**What you see.** `NodeApiError: Not Found` from the Telegram node on a poll, and
nothing delivered. The workflow looks correctly configured — resource
`message`, operation `sendPoll`, a valid question and options.

**Why.** n8n's Telegram node has no `sendPoll` operation. Its `message` resource
covers `sendMessage`, `sendPhoto`, `sendDocument`, `sendLocation` and the rest,
but not polls. Given an operation it does not implement, it composes a Bot API
URL for a method that does not exist — hence Telegram's `Not Found`, which reads
like a bad chat id and is nothing of the kind.

**How it was found.** A full re-smoke, after the docs had already claimed polls
were "built and unit-proven, not yet fired live". They were built and unit-proven
against the *package's* contract, which was correct — and the workflow node
underneath could never have worked. Unit tests cannot see this; only sending one
can.

**What the package does.** The poll is a direct HTTP call to the Bot API's
`sendPoll`, which needs a bot token in **n8n's** environment
(`TELEGRAM_BOT_TOKEN`). Since that may not be set, the branch is gated:

* token present → a real native poll;
* token absent → the message is delivered as a **numbered list that names the
  degrade**, rather than erroring.

```
Smoke 7/7 — which lane next?
  1. Track A — public climber
  2. Track B — private board
  3. Track C — throughput

(sent as text: TELEGRAM_BOT_TOKEN is not set in n8n, so a native poll cannot be
created — TG-22)
```

That is the difference between this and TG-18/19/20: a capability that is not
wired **says so on the message itself**. A silent degrade is the failure mode
this whole package exists to remove, so a deliberate one has to announce itself.

**Still your job.** For real polls, set `TELEGRAM_BOT_TOKEN` in n8n's
environment — the same token as the `[STUDIO] Telegram Bot` credential. Until
then polls are legible, not native. Note this is the one place a bot token is
needed anywhere; every other path avoids it (TG-08).

---

<a name="tg-23"></a>
## TG-23 — Stripping inert markdown silently corrupted content

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

**What you see.** A message that reads fine and is quietly wrong. A password
hint sent as `pw: __secret__` arrives as `pw: secret`. Quoted code loses its
backticks. Nothing errors, and the message looks deliberate.

**Why.** TG-01 establishes that the rail sends `parse_mode: "None"`, so markup
is transmitted rather than rendered. The first fix drew the wrong conclusion
from that: if the markers cannot render, remove them. But the same fact cuts the
other way — **because they are inert, removing them buys nothing**. There is no
rendering benefit to trade against the loss, and the loss is real: any content
that legitimately contains `*`, `_` or a backtick pair gets rewritten.

The blast radius was *delimited* content specifically. `part_number_1` and
`2*3=6` survived, because the emphasis pattern required non-word boundaries.
What did not survive was exactly the content most worth protecting: secrets,
quoted code, anything a third-party API put between delimiters.

**How it was found.** A cross-model review of the design, which pointed out that
`parse_mode` being `None` already prevents interpretation, so the conversion is
pure data loss. The claim was then verified against the real function rather
than taken on trust.

**What the package does.** `plain()` now flattens **structure only** — heading
hashes, blockquote markers, fence lines, horizontal rules, bullets, and links
(which become `label (url)`). Inline delimiters are returned exactly as they
arrived. Template authors write plain prose by convention; text flowing through
from an API is **data**, and data is not edited on its way to a human.

**Still your job.** Keep writing templates in plain prose. A template containing
`**bold**` will now show the asterisks, which is the honest outcome — the rail
genuinely cannot render it.

---

<a name="tg-24"></a>
## TG-24 — The response signature was verified and then ignored

**status.** legacy — pre-conformance entry (PROCESS.md §9): it predates this tool's first conformant version, has no `CHANGE_LOG.md` counterpart, and is exempt from the §7 Track B reciprocity check. Adding this field is the only edit made to the entry.

**What you see.** Nothing. That is the problem.

**Why.** The fan-out signs its own reply, and this package verified that
signature — then treated a mismatch as advisory, on the reasoning that n8n
re-serialises its response body, so a difference in JSON spacing would break
byte-equality without meaning anything.

**That premise was never measured, and it is false.** Checked against the live
workflow: `response_signature_ok: True`. The signature matches, every time.

Which makes the old behaviour the worst available option. A check that runs,
fails, and is ignored is not a weaker check — it is a **misleading** one. It
appears in the result object, it reads like a guarantee, and it defends nothing.

**What the package does.** A **present-but-wrong** signature now fails the send:
the result is `accepted=False` with a note naming this entry. An **absent**
signature is still fine and returns `None` — "unsigned" and "signed wrongly" are
different facts, and only the second is evidence of anything.

**Still your job.** If this ever starts failing in bulk, the receiver changed how
it serialises its reply. Measure before concluding — that is the mistake this
entry records. Do not re-soften it back to advisory without checking whether the
signature actually matches.

---

# Process conformance issues

The entries above are numbered `TG-nn` and predate `PROCESS.md`. Entries from
here on carry a process id — `<description>_<hash8>` per
`process.yaml: definitions.issue-id` — and are appended, never rewritten
(PROCESS.md §5 invariant 1). The index table at the top of this file is left as
it was for the same reason; it indexes the `TG-` series only.

---

## packages-telegram-failed-track-b-conform_9f851380

| Field | Value |
|---|---|
| **id** | `packages-telegram-failed-track-b-conform_9f851380` — recomputed 2026-09-01 with `sha256sum` over the canonical `summary` (trim, lowercase, collapse whitespace, strip trailing `.`), per `process.yaml: definitions.issue-id`. It reproduces unchanged |
| **status** | in-progress |
| **resolved_by** | not yet — **`merge_commit` is blank**, so `resolved` may not be written (`process.yaml: definitions.issue-status`). The iteration is [`CHANGE_LOG.md#move-the-implementation-into-tooling-v1_6206c8de`](CHANGE_LOG.md#move-the-implementation-into-tooling-v1_6206c8de), fix-version `v1.0.0` (no bump — the code moved, it did not change), executed on branch `smoke/fix-packages-telegram` and unmerged |
| **occurrences** | 1 — 2026-08-31, found by the Track B conformance sweep run against this tool (PROCESS.md §7 Track B / §9 "on next touch") |

**summary.** Packages/Telegram failed Track B conformance: CHANGE_LOG.md
missing, code not under Tooling/, no recorded test results under Tests/.

**outcome (X).** Measured against the five Track B checks of PROCESS.md §7, as
found on 2026-08-31:

| Check | Result as found |
|---|---|
| Canonical files | **FAIL** — four of five present (`README.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md`, all non-empty). `CHANGE_LOG.md` did not exist. This is the one document missing; it matches the §9 backlog table, which already records Telegram as the only tool carrying `TEMPLATES.md` and as having no `CHANGE_LOG.md` |
| Code layout | **FAIL** — no `Tooling/` directory existed. `telegram/`, `bin/`, `templates/`, `n8n/`, `examples/`, `tests/` and `run-tests.sh` all sat at the tool root, and test *code* sat in a lowercase `tests/` at the root rather than inside the version it tests (§4) |
| Test layout | **FAIL** — no `Tests/` directory existed. The suite passed (189 tests, verified before the move) but **no recorded result existed anywhere in the repo**: the evidence lived only in whoever last ran it |
| Version agreement | **PARTIAL** — `README.md` did state a version, `v1.0.0`, under "Status". The claim is *not* that the README named no version; it named one that nothing else corroborated, because neither a `Tooling/` directory nor a `CHANGE_LOG.md` entry existed to agree with it |
| Reciprocity | **PASS for the pair that exists, VACUOUS for the other.** `KNOWN_ISSUES.md` ↔ `CHANGE_LOG.md` could not be checked at all — there was no `CHANGE_LOG.md`, and no `TG-` entry cites a change id. `IMPLEMENTATIONS.md` → `TEMPLATES.md` is linked once, at IMPLEMENTATIONS.md line 149, and the two documents otherwise refer to each other by template name (`poller.settled`) rather than by entry id |

Consequence: under §7, "a tool failing Track B cannot release a new version" —
so the next genuine fix to this package was blocked before it could start, and
until then the tool's test status was unauditable from the repo alone.

**cause (Y).** The tool was authored before `PROCESS.md` existed (the process
document and `process.yaml` are both dated 2026-08-31; this package's live proof
runs date from executions 15034–15111 before it). Its layout is the flat
package shape that `PROCESS.md` §9 describes as the migration backlog — not
drift away from the convention, but code that predates it. Nothing in the tool
enforced the convention, so nothing failed loudly when it was not met; the gap
was only visible by reading the tool directory against §3 and §4 by hand.

**iteration (Z).** Bring the tool into conformance as its first pass through
§6: move the implementation to `Tooling/v1.0.0/` (§9 — a never-versioned tool
starts at `v1.0.0`), repair the paths the move breaks, run the suite from the
new location and record the verbatim output under `Tests/v1.0.0/`, create
`CHANGE_LOG.md` empty-but-valid with this migration as its first entry, and
correct `README.md` to state the layout and current version. Planned and
recorded in
[`CHANGE_LOG.md#move-the-implementation-into-tooling-v1_6206c8de`](CHANGE_LOG.md#move-the-implementation-into-tooling-v1_6206c8de).

**What the move actually broke.** Recorded here because it is the interesting
part and it is exactly what §5 invariant 6 exists to catch.
`tests/test_conformance.py` located `Packages/Poller` by walking three
directories up from itself. One directory deeper, that expression resolved to
`Packages/Telegram/Tooling/`, which contains no `Poller` — so the guard
`@unittest.skipUnless(os.path.isdir(POLLER_SINKS))` would have **skipped both
cross-package conformance tests while the suite still printed `OK`**. A green
189-test run would have silently stopped proving that this package and the
Poller emit the same envelope bytes. The path was fixed (five levels up, and
tolerant of the Poller's own migration into `Tooling/`), and the recorded run in
[`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) shows **zero skips**, which
is the evidence that it is fixed rather than merely quiet.

**Still open after this iteration.** Stated rather than silently carried:

- `IMPLEMENTATIONS.md` and `TEMPLATES.md` contain tool-root-relative paths
  (`./bin/telegram`, `tests/test_conformance.py`, `templates/`,
  `n8n/README.md`) that now live under `Tooling/v1.0.0/`. They were not
  rewritten: `IMPLEMENTATIONS.md` is append-only under §5 invariant 2, and
  correcting them is a documentation change, not part of this migration.
- The `IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` reciprocity required by §7 is
  cross-referenced by template name rather than by entry id, so a strict id-level
  reciprocity check still fails for that pair. That failure is now logged as its
  own entry, [`#track-b-reciprocity-fails-for-the-implem_c160a132`](#track-b-reciprocity-fails-for-the-implem_c160a132),
  rather than left as a sub-point — this tool therefore does **not** pass Track B,
  and the tick-list in `Tests/v1.0.0/RESULTS.md` records reciprocity as ❌.
- `IMPLEMENTATIONS.md` line 53 hard-codes
  `/studio/scratch/toolbelt/Toolbelt/Packages/Telegram/bin/telegram` as a Poller
  sink command. That absolute path is now wrong twice over (the checkout is at
  `/studio/scratch/tb`, and `bin/` moved), but it documents a live wiring
  outside this repo and is not this iteration's to change.

---

## track-b-reciprocity-fails-for-the-implem_c160a132

| Field | Value |
|---|---|
| **id** | `track-b-reciprocity-fails-for-the-implem_c160a132` — `sha256sum` over the canonical `summary` per `process.yaml: definitions.issue-id` |
| **status** | escalated |
| **resolved_by** | not resolved. The iteration is planned and recorded in [`CHANGE_LOG.md#extend-the-process-md-9-legacy-rule-to-c_ad654f71`](CHANGE_LOG.md#extend-the-process-md-9-legacy-rule-to-c_ad654f71); it cannot be executed inside this tool. Branch `smoke/fix-packages-telegram`, no fix-version, no merge commit |
| **occurrences** | 1 — 2026-09-01, found re-running Track B against this tool while correcting the 2026-08-31 migration entry |

**summary.** Track B reciprocity fails for the IMPLEMENTATIONS.md ↔ TEMPLATES.md
pair: their entries cross-reference by template name rather than by entry id.

**outcome (X).** `Packages/Telegram` fails the Track B **Reciprocity** check of
PROCESS.md §7, and therefore fails Track B as a whole. Concretely:

| Half of the check | Result |
|---|---|
| `KNOWN_ISSUES.md` ↔ `CHANGE_LOG.md` | **PASS.** The 24 `TG-` entries are marked `status: legacy` and exempt (§9). Both non-legacy issue entries cite a `CHANGE_LOG.md` id, and both change entries cite an issue id back |
| `IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` | **FAIL.** `IMPLEMENTATIONS.md` carries eight level-2 headings (`The five commands`, `Worked example: the Poller`, …) and `TEMPLATES.md` sixteen (`` `poller.settled` ``, …). None is a bare id, so under `process.yaml: definitions.entry` none is an addressable entry, and the two documents refer to each other by template *name*, not by id. There is exactly one id-shaped link between them (IMPLEMENTATIONS.md line 149) |

The §7 consequence is real and is not being softened here: a tool failing Track
B cannot release a new version. `v1.0.0` is not a release under this process —
it is the migration of existing code into the versioned layout — but the next
genuine iteration on this package is blocked until this is answered.

**cause (Y).** Both documents were authored before `PROCESS.md` existed, in
prose-section form, and both are **append-only** (§5 invariant 2 for
`IMPLEMENTATIONS.md`; `TEMPLATES.md` is a pre-existing document this repo's own
migration rules forbid overwriting). Making the check pass would require
rewriting twenty-four existing level-2 headings into `<description>_<hash8>` ids
— an overwrite of pre-existing entries, which invariant 2 forbids outright.
PROCESS.md §9 grandfathers pre-conformance **issue** entries and §7 exempts only
"non-legacy `KNOWN_ISSUES.md`" entries; the `IMPLEMENTATIONS.md` ↔
`TEMPLATES.md` clause carries no exemption at all. So the spec simultaneously
requires the id-level pairing and forbids the only edit that would create it.

**iteration (Z).** Extend the PROCESS.md §9 legacy rule to cover
pre-conformance IMPLEMENTATIONS.md and TEMPLATES.md entries, so the
IMPLEMENTATIONS ↔ TEMPLATES half of Track B reciprocity can be satisfied
without rewriting append-only entries. Recorded in
[`CHANGE_LOG.md#extend-the-process-md-9-legacy-rule-to-c_ad654f71`](CHANGE_LOG.md#extend-the-process-md-9-legacy-rule-to-c_ad654f71).

**Why this is `escalated` and not `planned`.** The iteration is a change to
`PROCESS.md`/`process.yaml`, which this branch does not own — the amended spec
is PR #16's. Per `process.yaml: definitions.escalate`, the work is left exactly
where it stands: issue-id `track-b-reciprocity-fails-for-the-implem_c160a132`,
change-id `extend-the-process-md-9-legacy-rule-to-c_ad654f71`, branch
`smoke/fix-packages-telegram`, round 1 of 3, and the check could not be answered
green without either breaking invariant 2 or narrowing the wording of the check
— neither of which an agent may do.

**What was deliberately not done.** Three tempting non-fixes, each rejected:

1. Rewriting the headings of `IMPLEMENTATIONS.md` / `TEMPLATES.md` into ids —
   breaks invariant 2.
2. Reading "entry" so that a non-id heading is not an entry, making the check
   vacuously true — that is narrowing the check to make it pass.
3. Appending fresh id-headed entries to both files and calling the pair
   reciprocal — the check reads *every* entry, so new entries do not repair old
   ones, and the result would be a green tick over a red check.
