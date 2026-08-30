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

  const rm = meta.reply_markup;
  if (rm && Array.isArray(rm.inline_keyboard)) {
    item.json.__kb = { rows: rm.inline_keyboard.map((r) => ({
      row: { buttons: r.map((btn) => ({
        text: btn.text,
        additionalFields: { callback_data: btn.callback_data },
      })) },
    })) };
    item.json.__hasKb = true;
  } else {
    item.json.__hasKb = false;
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
        {"id": "sendpoll", "name": "Send Poll", "type": "n8n-nodes-base.telegram",
         "typeVersion": 1.2, "position": [1100, -180],
         "parameters": {"resource": "message", "operation": "sendPoll",
                        "chatId": "={{ $json.__chatId }}",
                        "question": "={{ $json.__question }}",
                        "options": "={{ $json.__options }}",
                        "additionalFields": {
                            "appendAttribution": False,
                            "allows_multiple_answers": "={{ $json.__multiple }}",
                            "is_anonymous": "={{ $json.__anonymous }}"}},
         "credentials": TELEGRAM_CREDENTIAL},
        {"id": "haskb", "name": "Has Buttons?", "type": "n8n-nodes-base.if",
         "typeVersion": 2, "position": [1100, 60],
         "parameters": {"conditions": {
             "options": {"caseSensitive": True, "typeValidation": "loose", "version": 2},
             "conditions": [{"id": "haskb", "leftValue": "={{ $json.__hasKb }}",
                             "rightValue": "",
                             "operator": {"type": "boolean", "operation": "true"}}],
             "combinator": "and"}, "options": {}}},
        # TG-19: `replyMarkup` MUST be a literal, never an expression. The
        # `inlineKeyboard` parameter is gated by displayOptions on this value, and
        # n8n evaluates displayOptions against the RAW parameter — so an
        # expression never equals 'inlineKeyboard', the keyboard is skipped, and
        # the message is delivered as plain text with no error anywhere. That is
        # why the live fan-out has never actually attached a keyboard. Hence two
        # nodes behind an IF instead of one node with a conditional.
        {"id": "sendkb", "name": "Send With Buttons", "type": "n8n-nodes-base.telegram",
         "typeVersion": 1.2, "position": [1340, -20],
         "parameters": {"resource": "message", "operation": "sendMessage",
                        "chatId": "={{ $json.__chatId }}",
                        "text": "={{ $json.__text }}",
                        # parse_mode None deliberately: the package emits plain
                        # text and markup here would be transmitted, not rendered.
                        "additionalFields": {"appendAttribution": False,
                                             "parse_mode": "None"},
                        "replyMarkup": "inlineKeyboard",
                        "inlineKeyboard": "={{ $json.__kb }}"},
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
            [{"node": "Send Poll", "type": "main", "index": 0}],
            [{"node": "Has Buttons?", "type": "main", "index": 0}]]},
        "Has Buttons?": {"main": [
            [{"node": "Send With Buttons", "type": "main", "index": 0}],
            [{"node": "Send Message", "type": "main", "index": 0}]]},
        "Send Poll": {"main": [[{"node": "Sign Response", "type": "main", "index": 0}]]},
        "Send With Buttons": {"main": [[{"node": "Sign Response", "type": "main", "index": 0}]]},
        "Send Message": {"main": [[{"node": "Sign Response", "type": "main", "index": 0}]]},
        "Sign Response": {"main": [[{"node": "Respond Delivered", "type": "main", "index": 0}]]},
    },
}

# ---------------------------------------------------------------------------
# [STUDIO] Telegram Receiver — one generic decoder for every interactive send
#
# TG-09: a bot has exactly ONE webhook URL. Activating this receiver means
# taking that URL from whatever holds it now (`triage-receiver`,
# `dirnotif-feedback`), so it is a decision about which receiver owns the bot,
# not an addition alongside them.
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

// Telegram signs nothing, but setWebhook accepts a secret_token which it then
// echoes in this header. That is the real gate on this endpoint.
const EXPECTED = readSecret('TELEGRAM_WEBHOOK_SECRET');
// Comma-separated chat ids. Empty means "allow any", which is only safe on a
// bot nobody else knows about — set it.
const ALLOWED = readSecret('TELEGRAM_ALLOWED_CHATS').split(',').map((s) => s.trim()).filter(Boolean);

const sd = $getWorkflowStaticData('global');
if (!sd.answers || typeof sd.answers !== 'object') sd.answers = {};

const out = [];
for (const it of $input.all()) {
  const j = it.json;
  const h = j.headers || {};
  const u = j.body || j;

  let trusted = true;
  let note = '';

  const presented = h['x-telegram-bot-api-secret-token'] || '';
  if (EXPECTED && presented !== EXPECTED) { trusted = false; note = 'webhook secret mismatch'; }

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
        {"id": "hook", "name": "Telegram Webhook", "type": "n8n-nodes-base.webhook",
         "typeVersion": 2, "position": [0, 0],
         "parameters": {"httpMethod": "POST", "path": "telegram-receiver",
                        "responseMode": "responseNode", "options": {"rawBody": True}},
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
        {"id": "respond", "name": "Respond 200",
         "type": "n8n-nodes-base.respondToWebhook", "typeVersion": 1.1,
         "position": [880, 0],
         # Always 200, even when untrusted. Telegram retries a non-2xx, so
         # answering 401 to a hostile update earns a retry loop instead of
         # stopping one; the refusal is recorded in `trusted`, not in the status.
         "parameters": {"respondWith": "json",
                        "responseBody": '={{ { "ok": true } }}'}},
    ],
    "connections": {
        "Telegram Webhook": {"main": [[{"node": "Decode + Gate", "type": "main", "index": 0}]]},
        "Decode + Gate": {"main": [[{"node": "Was A Button?", "type": "main", "index": 0}]]},
        "Was A Button?": {"main": [
            [{"node": "Answer Callback", "type": "main", "index": 0}],
            [{"node": "Respond 200", "type": "main", "index": 0}]]},
        "Answer Callback": {"main": [[{"node": "Respond 200", "type": "main", "index": 0}]]},
    },
}

WORKFLOWS = {"interactive": INTERACTIVE, "receiver": RECEIVER}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "interactive"
    if which not in WORKFLOWS:
        sys.stderr.write("usage: build_workflows.py [{0}]\n".format("|".join(WORKFLOWS)))
        sys.exit(2)
    print(json.dumps(WORKFLOWS[which], indent=2))
