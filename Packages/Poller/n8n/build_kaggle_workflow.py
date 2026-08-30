"""Build (and optionally deploy) the n8n-resident Kaggle submission poller.

This is the always-on tier: the clock lives on the Hetzner VPS inside n8n, so a
flat laptop cannot take the watch down with it. Dedup state lives in
`$getWorkflowStaticData('global')` — the same mechanism the existing
[OPERORCH] Runner Watcher already relies on, persisted in the workflow record on
the VPS.

Classification mirrors the Python package exactly (failed -> settled -> pending,
and `complete` with a null publicScore is held as pending), so the two tiers
cannot disagree about what a settle is.

No secrets pass through this script. The HTTP nodes declare httpHeaderAuth and
leave the credential unset for the owner to attach in the n8n UI.
"""

import json

CODE = r"""
// Kaggle submission poller — classify, dedup, emit only what is new.
// Mirrors poller/sources/kaggle.py + poller/engine.py semantics.
const sd = $getWorkflowStaticData('global');
if (!sd.seen || typeof sd.seen !== 'object') sd.seen = {};

const FAILED  = ['error', 'failed', 'cancel'];
const SETTLED = ['complete', 'success'];
const PENDING = ['pending', 'running', 'queued', 'submitting'];

// The response is a bare array; some sibling endpoints wrap it.
let rows = $input.first().json;
if (rows && !Array.isArray(rows)) rows = rows.body || rows.submissions || rows.items || [];
if (!Array.isArray(rows)) rows = [];

const blank = (v) => v === null || v === undefined || v === '';

function classify(r) {
  const s = String(r.status ?? '').toLowerCase();
  // Checked failed-first on purpose: a false alarm is recoverable, a missed
  // failure is not.
  if (FAILED.some((p) => s.includes(p))) return 'failed';
  if (SETTLED.some((p) => s.includes(p))) {
    // "complete" can precede publicScore by a few seconds. Reporting then would
    // announce a settle with no score AND burn the dedup key (KI-04).
    return blank(r.publicScore) ? 'pending' : 'settled';
  }
  if (PENDING.some((p) => s.includes(p))) return 'pending';
  return 'pending';   // unknown status = keep watching, never "done"
}

const firstRun = !sd.seeded;
const out = [];
let seeded = 0;

for (const r of rows) {
  const key = String(r.ref ?? '');
  if (!key) continue;                       // cannot dedup what we cannot name
  const state = classify(r);
  if (state !== 'settled' && state !== 'failed') continue;
  const dedup = key + ':' + state;
  if (sd.seen[dedup]) continue;
  sd.seen[dedup] = new Date().toISOString();
  if (firstRun) { seeded++; continue; }     // seed: remember, do not report

  const score = blank(r.publicScore) ? '' : String(r.publicScore);
  const desc = String(r.description ?? '').replace(/\s+/g, ' ').trim();
  const when = String(r.date ?? '');
  const text = state === 'settled'
    ? `:bar_chart: *Kaggle settled: ${score}*\n*${desc}*\nscore *${score}*  ·  ref \`${key}\`  ·  ${when}\n— Chiron (n8n poller)`
    : `:x: *Kaggle submission FAILED*\n\`${desc}\` did not score (status ${r.status}).\nError: ${r.errorDescription || 'none'}\nA submission slot was spent — read the run log before resubmitting.\n— Chiron (n8n poller)`;
  const telegram = state === 'settled'
    ? `Kaggle settled: ${score}\n${desc}\nref ${key} · ${when}`
    : `Kaggle submission FAILED\n${desc}\nstatus ${r.status} · ${r.errorDescription || 'no detail'}`;

  out.push({ json: { key, state, score, description: desc, date: when,
                     status: String(r.status ?? ''), slack_text: text,
                     telegram_text: telegram } });
}

if (firstRun) {
  sd.seeded = new Date().toISOString();
  sd.seed_count = seeded;
}

// Bound the state file: keep the most recent 500 dedup keys.
const keys = Object.keys(sd.seen);
if (keys.length > 500) {
  keys.sort((a, b) => String(sd.seen[a]).localeCompare(String(sd.seen[b])));
  for (const k of keys.slice(0, keys.length - 500)) delete sd.seen[k];
}

return out;
"""

WORKFLOW = {
    "name": "[STUDIO] Kaggle Submission Poller (always-on)",
    "settings": {"executionOrder": "v1"},
    "nodes": [
        {
            "id": "trigger",
            "name": "Every 3 Minutes",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [0, 0],
            "parameters": {"rule": {"interval": [
                {"field": "cronExpression", "expression": "*/3 * * * *"}]}},
        },
        {
            "id": "fetch",
            "name": "Fetch Submissions",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [220, 0],
            "parameters": {
                "method": "GET",
                "url": "https://www.kaggle.com/api/v1/competitions/submissions/list/"
                       "ai-agent-security-multi-step-tool-attacks",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "options": {"timeout": 30000},
            },
        },
        {
            "id": "diff",
            "name": "Classify + Dedup",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [440, 0],
            "parameters": {"language": "javaScript", "jsCode": CODE},
        },
        {
            "id": "telegram",
            "name": "Telegram",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [680, -100],
            "parameters": {
                "resource": "message",
                "operation": "sendMessage",
                "chatId": "={{ ($env.TELEGRAM_DEFAULT_CHAT || '8859170398') }}",
                "text": "={{ $json.telegram_text }}",
                "additionalFields": {"appendAttribution": False},
            },
            "credentials": {"telegramApi": {"id": "pojHLD8xi2lxHgNp",
                                            "name": "[STUDIO] Telegram Bot"}},
        },
        {
            "id": "slack",
            "name": "Slack",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [680, 100],
            "parameters": {
                "method": "POST",
                "url": "https://slack.com/api/chat.postMessage",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "sendBody": True,
                "specifyBody": "json",
                "jsonBody": "={{ JSON.stringify({ channel: $env.SLACK_ARIUS_CHANNEL_ID "
                            "|| 'C0BRE9369KL', text: $json.slack_text }) }}",
                "options": {"timeout": 30000},
            },
        },
    ],
    "connections": {
        "Every 3 Minutes": {"main": [[{"node": "Fetch Submissions", "type": "main", "index": 0}]]},
        "Fetch Submissions": {"main": [[{"node": "Classify + Dedup", "type": "main", "index": 0}]]},
        "Classify + Dedup": {"main": [[
            {"node": "Telegram", "type": "main", "index": 0},
            {"node": "Slack", "type": "main", "index": 0},
        ]]},
    },
}

if __name__ == "__main__":
    print(json.dumps(WORKFLOW, indent=2))
