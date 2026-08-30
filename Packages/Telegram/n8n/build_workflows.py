"""Build the two n8n workflows this package needs beyond the live fan-out.

Nothing here touches `[TEMPLATE] Notification Fan-out`. That workflow is live,
active, and other plugins depend on it; it already renders inline keyboards from
`meta.reply_markup`, so **buttons need no change to anything deployed**.

Two things it genuinely cannot do:

1. **Send a native poll.** Its Telegram node is wired to `sendMessage`.
   `[STUDIO] Telegram Interactive` adds a `sendPoll` branch alongside it.
2. **Receive an answer.** `[STUDIO] Telegram Receiver` decodes `callback_query`
   and `poll_answer` updates using the same `<action>:<entity>:<id>` scheme as
   `telegram/keyboard.py`, replacing the per-plugin bespoke receivers rather
   than becoming a fourth one.

Both are emitted with **no credential attached** where a secret would be needed,
so tokens are entered by their owner in the n8n UI rather than transiting a
script.

    python3 n8n/build_workflows.py interactive > n8n/telegram-interactive.json
    python3 n8n/build_workflows.py receiver    > n8n/telegram-receiver.json
"""

import json
import sys

TELEGRAM_CREDENTIAL = {"telegramApi": {"id": "pojHLD8xi2lxHgNp",
                                       "name": "[STUDIO] Telegram Bot"}}

# ---------------------------------------------------------------------------
# [STUDIO] Telegram Interactive — sendMessage or sendPoll, from one envelope
# ---------------------------------------------------------------------------

VERIFY_JS = r"""
// Verify the studio notify envelope. Byte-for-byte the same contract as
// telegram/seam.py and packages/notify/src/client.mjs: HMAC-SHA256 over
// `${timestamp}.${rawBody}`, five-minute skew, both header families accepted.
const crypto = require('crypto');
const readSecret = (k) => {
  let v = null;
  try { v = $env[k]; } catch (e) {}
  if (v === null || v === undefined || v === '') {
    try { v = typeof $vars !== 'undefined' ? $vars[k] : null; } catch (e) {}
  }
  return (v === null || v === undefined) ? '' : String(v);
};
const SECRET = readSecret('NOTIFY_FANOUT_SECRET');
const MAX_SKEW_MS = 300000;
const hmac = (d) => crypto.createHmac('sha256', SECRET).update(d).digest('hex');
const safeEq = (a, b) => {
  if (!a || !b) return false;
  const x = Buffer.from(String(a)), y = Buffer.from(String(b));
  return x.length === y.length && crypto.timingSafeEqual(x, y);
};
// TE-16: recover the EXACT signed bytes, or the signature cannot match.
const rawOf = (j) => (j.rawBody != null) ? j.rawBody.toString() : JSON.stringify(j.body);

const out = [];
for (const it of $input.all()) {
  const j = it.json;
  const h = j.headers || {};
  let ok = false;
  // Fail-closed: an unconfigured secret can never verify, and never throws.
  if (SECRET) {
    const sig = h['x-n8n-signature'] || h['x-notify-signature'];
    const ts = h['x-n8n-timestamp'] || h['x-notify-timestamp'];
    const n = Number(ts);
    if (sig && ts && Number.isFinite(n) && Math.abs(Date.now() - n) <= MAX_SKEW_MS) {
      ok = safeEq(hmac(ts + '.' + rawOf(j)), sig);
    }
  }
  // TG-07 (IN-25): n8n freezes Code-node input items — an in-place write is
  // silently dropped and the next node reads an item without the field.
  // Always RETURN new items.
  out.push({ json: Object.assign({}, j, { __authok: ok }) });
}
return out;
"""

ROUTE_JS = r"""
// Decide whether this envelope is a poll or a message, and shape it for the
// delivery node. Mirrors telegram/template.py's `Message.meta()`.
const readSecret = (k) => {
  let v = null;
  try { v = $env[k]; } catch (e) {}
  if (v === null || v === undefined || v === '') {
    try { v = typeof $vars !== 'undefined' ? $vars[k] : null; } catch (e) {}
  }
  return (v === null || v === undefined) ? '' : String(v);
};
const out = [];
for (const it of $input.all()) {
  const j = it.json;
  const b = j.body || j;
  const meta = b.meta || {};
  const poll = meta.poll;
  const isPoll = !!(poll && Array.isArray(poll.options) && poll.options.length >= 2);

  const item = { json: Object.assign({}, j, {
    __isPoll: isPoll,
    // TG-12: the literal is a last-resort fallback. If TELEGRAM_DEFAULT_CHAT is
    // unset, messages go THERE rather than failing — set it deliberately.
    __chatId: b.chat_id || readSecret('TELEGRAM_DEFAULT_CHAT') || '8859170398',
    __text: b.message || b.text || '(no message)',
    __question: isPoll ? String(poll.question || b.message || '').slice(0, 300) : '',
    // The Telegram node wants options as a newline-joined string.
    __options: isPoll ? poll.options.map((o) => String(o).slice(0, 100)).join('\n') : '',
    __multiple: isPoll ? !!poll.allows_multiple_answers : false,
    __anonymous: isPoll ? poll.is_anonymous !== false : true,
  }) };

  // TG-22: n8n's Telegram node has NO sendPoll operation, so a poll must go
  // straight to the Bot API over HTTP — which needs a bot token in n8n's env.
  // When that is absent the poll degrades to a readable text message rather than
  // erroring, and says so, because a silent nothing is the failure this package
  // exists to stop.
  if (isPoll) {
    item.json.__pollBody = JSON.stringify({
      chat_id: item.json.__chatId,
      question: item.json.__question,
      options: poll.options.map((o) => String(o).slice(0, 100)),
      is_anonymous: poll.is_anonymous !== false,
      allows_multiple_answers: !!poll.allows_multiple_answers,
    });
    item.json.__canPoll = !!readSecret('TELEGRAM_BOT_TOKEN');
    item.json.__text = item.json.__canPoll ? item.json.__text
      : (item.json.__question + '\n' +
         poll.options.map((o, i) => '  ' + (i + 1) + '. ' + o).join('\n') +
         '\n\n(sent as text: TELEGRAM_BOT_TOKEN is not set in n8n, so a native ' +
         'poll cannot be created — TG-22)');
  } else {
    item.json.__canPoll = false;
    item.json.__pollBody = '';
  }

  // TG-20: the keyboard is flattened into FLAT LEAF FIELDS, not a nested object.
  // n8n cannot populate a fixedCollection parameter from an expression — the
  // structure must be literal in the node, with expressions only at the leaves.
  // Passing the whole object was discarded silently, which is why buttons never
  // appeared. Hence one row of up to three buttons, and a Switch on the count.
  const rm = meta.reply_markup;
  const flat = [];
  if (rm && Array.isArray(rm.inline_keyboard)) {
    for (const row of rm.inline_keyboard) {
      for (const btn of row || []) {
        if (btn && btn.text) flat.push(btn);
      }
    }
  }
  const MAX_BUTTONS = 3;
  item.json.__btnDropped = Math.max(0, flat.length - MAX_BUTTONS);
  const shown = flat.slice(0, MAX_BUTTONS);
  item.json.__btnCount = shown.length;
  item.json.__hasKb = shown.length > 0;
  for (let i = 0; i < MAX_BUTTONS; i++) {
    item.json['__b' + (i + 1) + 'text'] = shown[i] ? String(shown[i].text) : '';
    item.json['__b' + (i + 1) + 'data'] = shown[i] ? String(shown[i].callback_data) : '';
  }
  if (it.binary) item.binary = it.binary;
  out.push(item);
}
return out;
"""

SIGN_RESPONSE_JS = r"""
// Sign the reply, so a caller can tell this workflow from anything else that
// happens to answer 200 on that path.
const crypto = require('crypto');
const readSecret = (k) => {
  let v = null;
  try { v = $env[k]; } catch (e) {}
  if (v === null || v === undefined || v === '') {
    try { v = typeof $vars !== 'undefined' ? $vars[k] : null; } catch (e) {}
  }
  return (v === null || v === undefined) ? '' : String(v);
};
const SECRET = readSecret('NOTIFY_FANOUT_SECRET');
const out = [];
for (const it of $input.all()) {
  const j = it.json;
  const b = j.body || j;
  const body = { ok: true, request_id: b.request_id || null, poll: !!j.__isPoll };
  const payload = JSON.stringify(body);
  out.push({ json: Object.assign({}, j, {
    __body: body,
    // Fail-open to UNSIGNED rather than signing with an empty key.
    __sig: SECRET ? crypto.createHmac('sha256', SECRET).update(payload).digest('hex') : '',
  }) });
}
return out;
"""

INTERACTIVE = {
    "name": "[STUDIO] Telegram Interactive (message or poll)",
    "settings": {"executionOrder": "v1"},
    "nodes": [
        {"id": "hook", "name": "Webhook", "type": "n8n-nodes-base.webhook",
         "typeVersion": 2, "position": [0, 0],
         "parameters": {"httpMethod": "POST", "path": "telegram-interactive",
                        "responseMode": "responseNode", "options": {"rawBody": True}},
         "webhookId": "studio-telegram-interactive"},
        {"id": "verify", "name": "Verify HMAC", "type": "n8n-nodes-base.code",
         "typeVersion": 2, "position": [220, 0],
         "parameters": {"language": "javaScript", "jsCode": VERIFY_JS}},
        {"id": "gate", "name": "Auth Gate", "type": "n8n-nodes-base.if",
         "typeVersion": 2, "position": [440, 0],
         "parameters": {"conditions": {
             "options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
             "conditions": [{"id": "authok", "leftValue": "={{ $json.__authok }}",
                             "rightValue": "",
                             "operator": {"type": "boolean", "operation": "true"}}],
             "combinator": "and"}, "options": {}}},
        {"id": "route", "name": "Shape", "type": "n8n-nodes-base.code",
         "typeVersion": 2, "position": [660, -80],
         "parameters": {"language": "javaScript", "jsCode": ROUTE_JS}},
        {"id": "switch", "name": "Poll or Message", "type": "n8n-nodes-base.if",
         "typeVersion": 2, "position": [880, -80],
         "parameters": {"conditions": {
             "options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
             "conditions": [{"id": "ispoll", "leftValue": "={{ $json.__isPoll }}",
                             "rightValue": "",
                             "operator": {"type": "boolean", "operation": "true"}}],
             "combinator": "and"}, "options": {}}},
        # TG-22: there is no sendPoll on n8n's Telegram node — it answered
        # "Not Found" from the Bot API because the method does not exist. A poll
        # has to be an HTTP call, and that needs a bot token in n8n's env.
        {"id": "canpoll", "name": "Can Send Poll?", "type": "n8n-nodes-base.if",
         "typeVersion": 2, "position": [1100, -260],
         "parameters": {"conditions": {
             "options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
             "conditions": [{"id": "canpoll", "leftValue": "={{ $json.__canPoll }}",
                             "rightValue": "",
                             "operator": {"type": "boolean", "operation": "true"}}],
             "combinator": "and"}, "options": {}}},
        {"id": "sendpoll", "name": "Send Poll", "type": "n8n-nodes-base.httpRequest",
         "typeVersion": 4.2, "position": [1340, -320],
         "parameters": {
             "method": "POST",
             "url": "=https://api.telegram.org/bot{{ $env.TELEGRAM_BOT_TOKEN }}/sendPoll",
             "sendBody": True, "specifyBody": "json",
             "jsonBody": "={{ $json.__pollBody }}",
             "options": {"timeout": 30000}}},
        {"id": "haskb", "name": "Has Buttons?", "type": "n8n-nodes-base.if",
         "typeVersion": 2, "position": [1100, 60],
         "parameters": {"conditions": {
             "options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
             "conditions": [{"id": "haskb", "leftValue": "={{ $json.__hasKb }}",
                             "rightValue": "",
                             "operator": {"type": "boolean", "operation": "true"}}],
             "combinator": "and"}, "options": {}}},
        {"id": "howmany", "name": "How Many Buttons", "type": "n8n-nodes-base.switch",
         "typeVersion": 3, "position": [1340, -140],
         "parameters": {"rules": {"values": [
             {"conditions": {"options": {"caseSensitive": True,
                                         "typeValidation": "loose", "version": 2},
                             "conditions": [{"id": "one",
                                             "leftValue": "={{ $json.__btnCount }}",
                                             "rightValue": 1,
                                             "operator": {"type": "number",
                                                          "operation": "equals"}}],
                             "combinator": "and"},
              "outputKey": "1"},
             {"conditions": {"options": {"caseSensitive": True,
                                         "typeValidation": "loose", "version": 2},
                             "conditions": [{"id": "two",
                                             "leftValue": "={{ $json.__btnCount }}",
                                             "rightValue": 2,
                                             "operator": {"type": "number",
                                                          "operation": "equals"}}],
                             "combinator": "and"},
              "outputKey": "2"},
             {"conditions": {"options": {"caseSensitive": True,
                                         "typeValidation": "loose", "version": 2},
                             "conditions": [{"id": "three",
                                             "leftValue": "={{ $json.__btnCount }}",
                                             "rightValue": 3,
                                             "operator": {"type": "number",
                                                          "operation": "equals"}}],
                             "combinator": "and"},
              "outputKey": "3"}]},
             "options": {}}},
        # TG-19 + TG-20: `replyMarkup` is a LITERAL, and the `inlineKeyboard`
        # structure is LITERAL too — only the leaf values are expressions. Both
        # were needed. An expression in either place is discarded in silence, and
        # the message goes out as plain text with every node green. That is why
        # there is one node per button count instead of one node that adapts.
        {"id": "sendkb1", "name": "Send 1 Button", "type": "n8n-nodes-base.telegram",
         "typeVersion": 1.2, "position": [1560, -210],
         "parameters": {"resource": "message", "operation": "sendMessage",
                        "chatId": "={{ $json.__chatId }}",
                        "text": "={{ $json.__text }}",
                        "additionalFields": {"appendAttribution": False,
                                             "parse_mode": "None"},
                        "replyMarkup": "inlineKeyboard",
                        "inlineKeyboard": {"rows": [{"row": {"buttons": [{"text": "={{ $json.__b1text }}", "additionalFields": {"callback_data": "={{ $json.__b1data }}"}}]}}]}},
         "credentials": TELEGRAM_CREDENTIAL},
        # TG-19 + TG-20: `replyMarkup` is a LITERAL, and the `inlineKeyboard`
        # structure is LITERAL too — only the leaf values are expressions. Both
        # were needed. An expression in either place is discarded in silence, and
        # the message goes out as plain text with every node green. That is why
        # there is one node per button count instead of one node that adapts.
        {"id": "sendkb2", "name": "Send 2 Buttons", "type": "n8n-nodes-base.telegram",
         "typeVersion": 1.2, "position": [1560, -120],
         "parameters": {"resource": "message", "operation": "sendMessage",
                        "chatId": "={{ $json.__chatId }}",
                        "text": "={{ $json.__text }}",
                        "additionalFields": {"appendAttribution": False,
                                             "parse_mode": "None"},
                        "replyMarkup": "inlineKeyboard",
                        "inlineKeyboard": {"rows": [{"row": {"buttons": [{"text": "={{ $json.__b1text }}", "additionalFields": {"callback_data": "={{ $json.__b1data }}"}}, {"text": "={{ $json.__b2text }}", "additionalFields": {"callback_data": "={{ $json.__b2data }}"}}]}}]}},
         "credentials": TELEGRAM_CREDENTIAL},
        # TG-19 + TG-20: `replyMarkup` is a LITERAL, and the `inlineKeyboard`
        # structure is LITERAL too — only the leaf values are expressions. Both
        # were needed. An expression in either place is discarded in silence, and
        # the message goes out as plain text with every node green. That is why
        # there is one node per button count instead of one node that adapts.
        {"id": "sendkb3", "name": "Send 3 Buttons", "type": "n8n-nodes-base.telegram",
         "typeVersion": 1.2, "position": [1560, -30],
         "parameters": {"resource": "message", "operation": "sendMessage",
                        "chatId": "={{ $json.__chatId }}",
                        "text": "={{ $json.__text }}",
                        "additionalFields": {"appendAttribution": False,
                                             "parse_mode": "None"},
                        "replyMarkup": "inlineKeyboard",
                        "inlineKeyboard": {"rows": [{"row": {"buttons": [{"text": "={{ $json.__b1text }}", "additionalFields": {"callback_data": "={{ $json.__b1data }}"}}, {"text": "={{ $json.__b2text }}", "additionalFields": {"callback_data": "={{ $json.__b2data }}"}}, {"text": "={{ $json.__b3text }}", "additionalFields": {"callback_data": "={{ $json.__b3data }}"}}]}}]}},
         "credentials": TELEGRAM_CREDENTIAL},
        {"id": "sendmsg", "name": "Send Message", "type": "n8n-nodes-base.telegram",
         "typeVersion": 1.2, "position": [1340, 160],
         "parameters": {"resource": "message", "operation": "sendMessage",
                        "chatId": "={{ $json.__chatId }}",
                        "text": "={{ $json.__text }}",
                        "additionalFields": {"appendAttribution": False,
                                             "parse_mode": "None"},
                        "replyMarkup": "none"},
         "credentials": TELEGRAM_CREDENTIAL},
        {"id": "sign", "name": "Sign Response", "type": "n8n-nodes-base.code",
         "typeVersion": 2, "position": [1340, -80],
         "parameters": {"language": "javaScript", "jsCode": SIGN_RESPONSE_JS}},
        {"id": "respond", "name": "Respond Delivered",
         "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1,
         "position": [1560, -80],
         "parameters": {"respondWith": "json", "responseBody": "={{ $json.__body }}",
                        "options": {"responseHeaders": {"entries": [
                            {"name": "x-n8n-signature", "value": "={{ $json.__sig }}"}]}}}},
        {"id": "reject", "name": "Reject 401",
         "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1,
         "position": [660, 140],
         "parameters": {"respondWith": "json",
                        "responseBody": '={{ { "ok": false, "error": "invalid or missing signature" } }}',
                        "options": {"responseCode": 401}}},
    ],
    "connections": {
        "Webhook": {"main": [[{"node": "Verify HMAC", "type": "main", "index": 0}]]},
        "Verify HMAC": {"main": [[{"node": "Auth Gate", "type": "main", "index": 0}]]},
        "Auth Gate": {"main": [
            [{"node": "Shape", "type": "main", "index": 0}],
            [{"node": "Reject 401", "type": "main", "index": 0}]]},
        "Shape": {"main": [[{"node": "Poll or Message", "type": "main", "index": 0}]]},
        "Poll or Message": {"main": [
            [{"node": "Can Send Poll?", "type": "main", "index": 0}],
            [{"node": "Has Buttons?", "type": "main", "index": 0}]]},
        # No token: fall through to a plain message that spells the poll out,
        # rather than failing the execution and delivering nothing (TG-22).
        "Can Send Poll?": {"main": [
            [{"node": "Send Poll", "type": "main", "index": 0}],
            [{"node": "Send Message", "type": "main", "index": 0}]]},
        "Has Buttons?": {"main": [
            [{"node": "How Many Buttons", "type": "main", "index": 0}],
            [{"node": "Send Message", "type": "main", "index": 0}]]},
        "How Many Buttons": {"main": [
            [{"node": "Send 1 Button", "type": "main", "index": 0}],
            [{"node": "Send 2 Buttons", "type": "main", "index": 0}],
            [{"node": "Send 3 Buttons", "type": "main", "index": 0}]]},
        "Send Poll": {"main": [[{"node": "Sign Response", "type": "main", "index": 0}]]},
        "Send 1 Button": {"main": [[{"node": "Sign Response", "type": "main", "index": 0}]]},
        "Send 2 Buttons": {"main": [[{"node": "Sign Response", "type": "main", "index": 0}]]},
        "Send 3 Buttons": {"main": [[{"node": "Sign Response", "type": "main", "index": 0}]]},
        "Send Message": {"main": [[{"node": "Sign Response", "type": "main", "index": 0}]]},
        "Sign Response": {"main": [[{"node": "Respond Delivered", "type": "main", "index": 0}]]},
    },
}

# ---------------------------------------------------------------------------
# [STUDIO] Telegram Receiver — one generic decoder for every interactive send
#
# Built on a **Telegram Trigger**, not a generic Webhook node. That choice is
# load-bearing twice over:
#
#   * n8n calls `setWebhook` itself on activation, using the stored bot
#     credential — so pointing the bot here needs no bot token in anyone's hands
#     (TG-08), and no manual API call.
#   * Telegram signs nothing. The incumbent receivers (`triage-receiver`,
#     `dirnotif-feedback`) are generic webhooks guarded by an HMAC check, which
#     an update can never satisfy — so they reject 100% of what they receive and
#     Telegram retries each one into a storm (TG-21). The trigger owns its own
#     endpoint and answers correctly.
#
# TG-09 still applies: a bot has exactly ONE webhook URL, so activating this
# takes it from whatever holds it now. That is the intent — those receivers have
# never once succeeded — but it is a decision, not a side effect.
# ---------------------------------------------------------------------------

DECODE_JS = r"""
// Decode a Telegram update. Deliberately the mirror of telegram/inbound.py and
// telegram/keyboard.py: `<action>:<entity>:<id>`, everything after the second
// colon is the id. IN-30 is what happens when these two drift apart.
const readSecret = (k) => {
  let v = null;
  try { v = $env[k]; } catch (e) {}
  if (v === null || v === undefined || v === '') {
    try { v = typeof $vars !== 'undefined' ? $vars[k] : null; } catch (e) {}
  }
  return (v === null || v === undefined) ? '' : String(v);
};

// Only meaningful on a generic-webhook deployment, where setWebhook was given a
// secret_token that Telegram echoes back in this header. On the Telegram Trigger
// n8n owns the endpoint and there are no headers to check, so this is skipped —
// the chat allow-list below is the gate that actually runs.
const EXPECTED = readSecret('TELEGRAM_WEBHOOK_SECRET');
// Comma-separated chat ids. TG-21: this defaults to the owner's chat rather than
// to "allow any". An unset allow-list on a reachable bot is an open door, and
// this endpoint's other gate (the webhook secret) is also skipped when unset —
// so failing open on both would mean no gate at all. Set the env var to widen it.
const ALLOWED = (readSecret('TELEGRAM_ALLOWED_CHATS') || '8859170398')
  .split(',').map((s) => s.trim()).filter(Boolean);

const sd = $getWorkflowStaticData('global');
if (!sd.answers || typeof sd.answers !== 'object') sd.answers = {};

const out = [];
for (const it of $input.all()) {
  const j = it.json;
  const h = j.headers || {};
  const u = j.body || j;

  let trusted = true;
  let note = '';

  // Discriminate on the TRANSPORT, not on whether the header happens to be
  // present. The Telegram Trigger hands over a bare update with no headers at
  // all; a generic webhook always has them. Skipping merely because the header
  // is missing would let anyone bypass the gate by omitting it.
  const viaTrigger = !j.headers;
  const presented = h['x-telegram-bot-api-secret-token'] || '';
  if (EXPECTED && !viaTrigger && presented !== EXPECTED) {
    trusted = false; note = 'webhook secret mismatch';
  }

  let kind = 'unknown', action = '', entity = '', id = '', chatId = '', userId = '';
  let username = '', queryId = '', options = [], text = '';

  if (u.callback_query) {
    const q = u.callback_query;
    const parts = String(q.data || '').split(':');
    while (parts.length < 3) parts.push('');
    kind = 'callback';
    action = parts[0];
    entity = parts[1];
    id = parts.slice(2).join(':');
    queryId = String(q.id || '');
    chatId = String(((q.message || {}).chat || {}).id || '');
    userId = String((q.from || {}).id || '');
    username = String((q.from || {}).username || '');
    if (!action) { trusted = false; note = note || 'callback_data carried no action'; }
  } else if (u.poll_answer) {
    kind = 'poll_answer';
    id = String(u.poll_answer.poll_id || '');
    userId = String((u.poll_answer.user || {}).id || '');
    username = String((u.poll_answer.user || {}).username || '');
    options = u.poll_answer.option_ids || [];
    // Telegram sends no chat id on a poll answer, so a chat allow-list cannot
    // admit it. Say so rather than admitting it by accident.
    if (ALLOWED.length) { trusted = false; note = note || 'poll answers carry no chat id'; }
  } else if (u.message) {
    kind = 'message';
    chatId = String((u.message.chat || {}).id || '');
    userId = String((u.message.from || {}).id || '');
    text = String(u.message.text || '');
  } else {
    trusted = false;
    note = note || 'no callback_query, poll_answer or message';
  }

  if (trusted && ALLOWED.length && chatId && ALLOWED.indexOf(chatId) === -1) {
    trusted = false;
    note = 'chat ' + chatId + ' is not on the allow-list';
  }

  if (trusted && kind !== 'unknown') {
    // Durable enough for a v1: the answer survives restarts in the workflow
    // record. A real answer store is the next version's job.
    sd.answers[(entity || '-') + ':' + (id || '-')] = {
      action: action, kind: kind, options: options,
      user: userId, at: new Date().toISOString(),
    };
    const keys = Object.keys(sd.answers);
    if (keys.length > 500) for (const k of keys.slice(0, keys.length - 500)) delete sd.answers[k];
  }

  out.push({ json: {
    kind: kind, action: action, entity: entity, id: id,
    chat_id: chatId, user_id: userId, username: username,
    callback_query_id: queryId, options: options, text: text,
    trusted: trusted, note: note,
    __toast: trusted ? ('Recorded: ' + (action || kind)) : 'Not permitted',
    __hasQuery: !!queryId,
  } });
}
return out;
"""

RECEIVER = {
    "name": "[STUDIO] Telegram Receiver (callbacks + poll answers)",
    "settings": {"executionOrder": "v1"},
    "nodes": [
        {"id": "hook", "name": "Telegram Trigger",
         "type": "n8n-nodes-base.telegramTrigger", "typeVersion": 1.2,
         "position": [0, 0],
         "parameters": {"updates": ["callback_query", "poll_answer", "message"],
                        "additionalFields": {}},
         "credentials": TELEGRAM_CREDENTIAL,
         "webhookId": "studio-telegram-receiver"},
        {"id": "decode", "name": "Decode + Gate", "type": "n8n-nodes-base.code",
         "typeVersion": 2, "position": [220, 0],
         "parameters": {"language": "javaScript", "jsCode": DECODE_JS}},
        {"id": "hasquery", "name": "Was A Button?", "type": "n8n-nodes-base.if",
         "typeVersion": 2, "position": [440, 0],
         "parameters": {"conditions": {
             "options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
             "conditions": [{"id": "hasq", "leftValue": "={{ $json.__hasQuery }}",
                             "rightValue": "",
                             "operator": {"type": "boolean", "operation": "true"}}],
             "combinator": "and"}, "options": {}}},
        {"id": "answer", "name": "Answer Callback", "type": "n8n-nodes-base.telegram",
         "typeVersion": 1.2, "position": [660, -80],
         "parameters": {"resource": "callback", "operation": "answerQuery",
                        "queryId": "={{ $json.callback_query_id }}",
                        "additionalFields": {"text": "={{ $json.__toast }}"}},
         "credentials": TELEGRAM_CREDENTIAL},
    ],
    "connections": {
        "Telegram Trigger": {"main": [[{"node": "Decode + Gate", "type": "main", "index": 0}]]},
        "Decode + Gate": {"main": [[{"node": "Was A Button?", "type": "main", "index": 0}]]},
        # The trigger answers Telegram itself, so there is no respond node and no
        # way to accidentally return a non-2xx and earn a retry storm (TG-21).
        # A refusal is recorded in `trusted`, never in the status code.
        "Was A Button?": {"main": [
            [{"node": "Answer Callback", "type": "main", "index": 0}], []]},
    },
}

WORKFLOWS = {"interactive": INTERACTIVE, "receiver": RECEIVER}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "interactive"
    if which not in WORKFLOWS:
        sys.stderr.write("usage: build_workflows.py [{0}]\n".format("|".join(WORKFLOWS)))
        sys.exit(2)
    print(json.dumps(WORKFLOWS[which], indent=2))
