#!/usr/bin/env bash
# PreToolUse guard for the fleet-triage subagent — enforces its READ-ONLY contract mechanically
# (not by prose). Triage may PEEK the mailbox and READ the board; it must never write the board,
# ack/consume messages, or send. Blocks the Bash call (exit 2) when the command would mutate state.
# Wired via the `hooks:` frontmatter in ~/.claude/agents/fleet-triage.md.
set -euo pipefail
cmd="$(python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("tool_input",{}).get("command",""))
except Exception: print("")' 2>/dev/null || true)"
[ -n "$cmd" ] || exit 0

# Deny: board writer at all; mailbox mutating verbs; redirect/in-place edit of SPRINT.md;
#       moving/removing inbox files; bare rm.
if printf '%s' "$cmd" | grep -Eq \
  'fleet-board|fleet-mbox([^|&;]*)?[[:space:]](read|ack|send|lock|unlock|init)|(>>?|tee|sed[[:space:]]+-i|mv|cp)[^|&;]*SPRINT\.md|/inbox/[^|&;]*(mv|rm)|(^|[[:space:];&|])rm[[:space:]]'
then
  printf 'fleet-triage is READ-ONLY — refusing: %s\nUse peek/ls/check + cat/grep/awk/find only; the orchestrator applies + acks.\n' "$cmd" >&2
  exit 2
fi
exit 0
