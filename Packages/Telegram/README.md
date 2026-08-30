# Telegram

The studio's Telegram messaging seam. One signed envelope to the hosted n8n
fan-out, and one catalogue of message templates — so a Telegram message stops
being composed by hand at every call site.

Zero dependencies: Python 3.9+ standard library only. No pip, no Node, no paths
into other repos. The same tree runs in a container, on a VPS, or under cron.

- **[TEMPLATES.md](TEMPLATES.md)** — the catalogue. What each template says,
  what it needs, and what its buttons encode to.
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** — the ways Telegram messaging has
  actually broken here, and the constraints of the live rail. Read this before
  writing a template.
- **[IMPLEMENTATIONS.md](IMPLEMENTATIONS.md)** — wiring a new caller, adding a
  template, and the Poller worked end to end.
- **[n8n/README.md](n8n/README.md)** — the two workflows this ships, why the
  live fan-out is not touched, and what activating them costs.

## Why this exists

The transport was solved once, in `packages/notify/src/client.mjs`. The
*message* never was.

Composing one is currently done at the call site in four runtimes: the Claude
Code hook (Node), the agent-kit digest (TypeScript), seventeen SEO-suite n8n
Code nodes (JavaScript), and `studio-cpu-watchdog` — which hand-rolled the
entire signed envelope in Python, because reaching a Node implementation from
where it runs was not possible. Between them: four emoji conventions, six
different truncation limits for the same kind of field, and no way to fix any of
it in one place.

So the catalogue is data. Adding a message shape means adding a file. Changing
how every settle report reads means changing one.

Every failure in `KNOWN_ISSUES.md` has a guard in code and a test, and each is
annotated with the `TG-` id it came from — `grep -rn TG-03 telegram/` finds the
code an incident bought.

## Quickstart

```bash
cd Packages/Telegram
./run-tests.sh                                   # full suite, offline, ~1s

./bin/telegram templates                         # what can I send?
./bin/telegram render report --set title="Deploy finished"     # offline preview
./bin/telegram check                             # prove the credentials resolve
./bin/telegram send report --set title="Deploy finished" --verify
```

`render` is the important one. It prints exactly what will arrive — including
where a long message would be chunked and what each button encodes to — without
sending anything. Most of the failures in `KNOWN_ISSUES.md` are invisible until
you can see that.

## How it works

```
   any caller ──▶ Template ──▶ Message ──▶ Seam ──▶ n8n workflow ──▶ Telegram
                     │            │          │
        catalogue/*.json    plain text   signed envelope
        input · output      + chunking   HMAC(ts.body)
        · interactive       + keyboard   both header families
                                              │
                            ┌─────────────────┴──────────────────┐
                            ▼                                    ▼
                  [TEMPLATE] Notification Fan-out    [STUDIO] Telegram Interactive
                  live · text ONLY (TG-19/20)        live · buttons + sendPoll
                            │                                    │
                            └──────────── delivered ─────────────┘
                                              │
                                   telegram verify  ── proves it, via the
                                                       execution record

   a button press ──▶ [STUDIO] Telegram Receiver ──▶ inbound.decode_update
                      live · Telegram Trigger        same <action>:<entity>:<id>
```

## The three template groups

| Group | Purpose | Examples |
|---|---|---|
| **input** | render an event that arrived from somewhere else | `poller.settled`, `poller.failed`, `poller.stopped`, `generic.event` |
| **output** | compose something the studio is saying | `report`, `update`, `alert`, `digest`, `handoff` |
| **interactive** | ask the human something | `approval`, `choice`, `ack`, `poll` |

The Poller is the first-class input producer — its settle, failure, staleness
and lifecycle events all have entries, and it can drive this package through its
own `command` sink with no coupling between the two.

## The three things worth knowing before you start

**A 2xx is not a delivery.** The webhook answers before the Telegram node runs.
`send` reports `accepted`; only `verify` can report `delivered`, by reading the
workflow's execution record. (TG-02)

**Markdown does not render, and is not stripped either.** The delivery node
sends `parse_mode: "None"`, so `*bold*` arrives with the asterisks — write
templates in plain prose (TG-01). Rendering flattens *structure* only; inline
delimiters are left alone, because removing inert markers bought no rendering
benefit and silently corrupted content like `pw: __secret__` (TG-23).

**`callback_data` is a 64-byte budget, and going over fails silently.** The
encoder refuses rather than truncating, because a truncated key produces a
perfectly normal-looking button that acts on the wrong record — which is exactly
what IN-30 was. (TG-03)

**Buttons and the return path both need the new workflows.** Measured during
this package's own smoke test: the live fan-out discards an inline keyboard
silently (TG-19, TG-20), and the two incumbent receivers reject **every** inbound
callback 401 because they check an HMAC Telegram never sends — then Telegram
retries each refusal into a storm (TG-21). Neither half of the interactive rail
had ever worked. Both are fixed in `n8n/`.

## What is proven, and how

`./run-tests.sh` runs 189 offline tests. Three of them are the ones that matter
most, and each **skips loudly** rather than passing quietly if it cannot run:

- **Envelope conformance against `client.mjs`** — the real file, executed in
  `node`, compared byte-for-byte including the signature. Two independent
  implementations of one contract, asserted rather than assumed.
- **Envelope conformance against the Poller's sink** — a third implementation,
  deliberately uncoupled, held to the same bytes.
- **n8n decoder parity** — the receiver workflow's JavaScript is executed
  against the same updates as the Python decoder and the answers compared. This
  is the IN-30 shape, so it is tested rather than reviewed.

## Status

v1.0.0, **proven live end to end** — every claim below confirmed from execution
records, not status codes.

| | Proof |
|---|---|
| Plain text, all three groups | executions 15034 / 15035 / 15036 |
| Buttons, template-driven | execution 15075 — three buttons, correct callbacks |
| **Round trip** workflow → human → workflow | a real press decoded to `att:loop:rt-1`, recorded, callback answered (15097 out, 15098 back) |
| 1-, 2- and 3-button branches | executions 15109 / 15108 / 15107 |
| Multi-part chunking | execution 15104 |
| Poll | execution 15111 — **degrades to text**: n8n has no `sendPoll` (TG-22) |

Both workflows are now **ACTIVE**: `[STUDIO] Telegram Interactive`
(`tpke3idOSDgGAA1X`) and `[STUDIO] Telegram Receiver` (`h2IF63cRYxQYUBFW`), the
latter now owning the bot's webhook (TG-09) — taken from an incumbent that had
never once succeeded.

Not in v1: the blocking `telegram await` loop, which needs a durable answer store
and is a decision rather than a detail. **Native polls need
`TELEGRAM_BOT_TOKEN` in n8n's environment** — without it a poll still arrives,
as a numbered list that says why (TG-22).
