#!/usr/bin/env bash
# fleet-doctor — health check + status view for a running /fleet sprint.
# Catches the failure modes the cross-model review flagged as worth guarding by TOOLING (not
# protocol): stale locks, §0↔§3 worker mismatch, tasks IN-REVIEW with no reviewer traffic,
# uncommitted board, inbox backlog. The human is the failsafe; this is what the human runs to look.
#
# Usage:
#   fleet-doctor <WT> [--root <FLEET_ROOT>]     # check (default). WT = sprint worktree dir.
#   fleet-doctor check  <WT> [--root <ROOT>]
#   fleet-doctor status <WT> [--root <ROOT>]    # colorized board glance
# FLEET_ROOT is derived from the worktree slug when not given. Env FLEET_LOCK_STALE_H (default 6).
set -uo pipefail

sub="check"; case "${1:-}" in check|status) sub="$1"; shift;; esac
WT="${1:?usage: fleet-doctor [check|status] <WT> [--root <FLEET_ROOT>]}"; shift || true
ROOT=""; [ "${1:-}" = "--root" ] && { ROOT="${2:?}"; }
DOC="$WT/SPRINT.md"
slug="$(basename "$WT" | sed 's/^sprint-//')"
ROOT="${ROOT:-/studio/scratch/fleet/$slug}"
STALE_H="${FLEET_LOCK_STALE_H:-6}"

if [ -t 1 ]; then R=$'\e[31m'; Y=$'\e[33m'; G=$'\e[32m'; C=$'\e[36m'; B=$'\e[1m'; Z=$'\e[0m'
else R=; Y=; G=; C=; B=; Z=; fi

warn=0; failn=0
say(){ printf '%s\n' "$*"; }
OK(){   say "  ${G}✓${Z} $*"; }
WARN(){ say "  ${Y}▲ WARN${Z} $*"; warn=$((warn+1)); }
FAIL(){ say "  ${R}✗ FAIL${Z} $*"; failn=$((failn+1)); }

_rows(){ awk '/^## 3\./{s=1;next} /^## 4\./{s=0} s && /^\| *[A-Za-z0-9]/ && $0 !~ /Task \(one line\)/' "$DOC"; }
_field(){ awk -F'|' -v n="$1" '{gsub(/^ +| +$/,"",$n); print $n}'; }   # 1-based incl leading empty
_count(){ find "$ROOT/$1/inbox" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' '; }

[ -f "$DOC" ] || { FAIL "no SPRINT.md at $DOC"; exit 2; }

if [ "$sub" = status ]; then
  say "${B}SPRINT ${slug}${Z}  ·  $DOC"
  # lock
  if [ -d "$ROOT/.lock" ]; then say "lock: ${C}$(sed -n 's/^holder: //p' "$ROOT/.lock/holder")${Z}"; else say "lock: unlocked"; fi
  say "${B}§3 delegation${Z}"
  _rows | while IFS= read -r line; do
    id=$(printf '%s' "$line" | _field 2); who=$(printf '%s' "$line" | _field 3)
    task=$(printf '%s' "$line" | _field 4); st=$(printf '%s' "$line" | _field 5)
    col=$Z; case "$st" in COMPLETE) col=$G;; BLOCKED|NEEDS-ITERATION) col=$R;; IN-REVIEW|IN-PROGRESS) col=$C;; ASSIGNED|QUEUED) col=$Y;; esac
    printf '  %-4s %-3s %b%-14s%b %s\n' "$id" "$who" "$col" "$st" "$Z" "$task"
  done
  say "${B}inboxes${Z}"
  for who in orchestrator reviewer $(ls -1 "$ROOT" 2>/dev/null | grep -vE '^(orchestrator|reviewer|\.lock)$'); do
    [ -d "$ROOT/$who/inbox" ] || continue; printf '  %-14s %s unread\n' "$who" "$(_count "$who")"
  done
  say "${B}§5 tail${Z}"; awk '/^## 5\./{s=1;next} /^## 6\./{s=0} s && /^- /' "$DOC" | tail -5 | sed 's/^/  /'
  exit 0
fi

# ---- check ----
say "${B}fleet-doctor — sprint ${slug}${Z}"

# 1. structure
[ -d "$ROOT" ] && OK "mailbox root present ($ROOT)" || FAIL "mailbox root missing: $ROOT"
for d in orchestrator reviewer; do [ -d "$ROOT/$d/inbox" ] && OK "$d inbox present" || WARN "$d inbox missing"; done

# 2. lock staleness
if [ -d "$ROOT/.lock" ]; then
  holder=$(sed -n 's/^holder: //p' "$ROOT/.lock/holder" 2>/dev/null)
  at=$(sed -n 's/^at: //p' "$ROOT/.lock/holder" 2>/dev/null | tr -d 'Z')
  if [ -n "$at" ]; then
    e=$(date -u -d "${at:0:4}-${at:4:2}-${at:6:2} ${at:9:2}:${at:11:2}:${at:13:2}" +%s 2>/dev/null || echo 0)
    age=$(( $(date -u +%s) - e )); ah=$(( age/3600 ))
    if [ "$ah" -ge "$STALE_H" ]; then WARN "lock held by '${holder}' for ${ah}h (≥${STALE_H}h) — likely STALE; if that session is dead, run: fleet-mbox unlock ${holder}"
    else OK "lock held by '${holder}' (${ah}h old)"; fi
  else OK "lock held by '${holder}'"; fi
else OK "no lock (unlocked)"; fi

# 3. §0 workers vs §3 workers
w0=$(grep -m1 '\*\*Workers:\*\*' "$DOC" | sed 's/.*\*\*Workers:\*\* *//; s/ //g')
w3=$(_rows | _field 3 | sort -u | tr '\n' ',' | sed 's/,$//')
mism=""
for w in $(printf '%s' "$w3" | tr ',' ' '); do case ",$w0," in *",$w,"*) ;; *) mism="$mism $w";; esac; done
[ -z "$mism" ] && OK "§3 workers ⊆ §0 workers (${w0:-none})" || WARN "§3 references worker(s) not in §0 Workers ($w0):$mism"

# 4. IN-REVIEW rows vs reviewer traffic
rev_total=$(( $(_count reviewer) + $(find "$ROOT/reviewer/processed" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ') ))
inrev=$(_rows | awk -F'|' '{gsub(/^ +| +$/,"",$5); gsub(/^ +| +$/,"",$2); if($5=="IN-REVIEW") print $2}' | tr '\n' ' ')
if [ -n "${inrev// /}" ] && [ "$rev_total" -eq 0 ]; then WARN "task(s) IN-REVIEW [${inrev}] but reviewer mailbox is empty — packet may not have been sent"
else OK "IN-REVIEW rows consistent with reviewer mailbox (${rev_total} packet msgs)"; fi

# 5. uncommitted board
if git -C "$WT" status --porcelain -- SPRINT.md 2>/dev/null | grep -q .; then WARN "SPRINT.md has uncommitted changes — run: fleet-board commit $WT"
else OK "board committed (clean working tree for SPRINT.md)"; fi

# 6. inbox backlog
big=""
for who in $(ls -1 "$ROOT" 2>/dev/null | grep -vE '^\.lock$'); do
  [ -d "$ROOT/$who/inbox" ] || continue; n=$(_count "$who"); [ "$n" -gt 20 ] && big="$big ${who}:${n}"
done
[ -z "$big" ] && OK "no inbox backlog >20" || WARN "large inbox backlog:$big (recipient not polling?)"

# 7. disk (info)
say "  ${C}i${Z} scratch usage: $(du -sh "$ROOT" 2>/dev/null | cut -f1) at $ROOT"

say ""
if [ "$failn" -gt 0 ]; then say "${R}${B}$failn FAIL${Z}, ${warn} warn"; exit 2
elif [ "$warn" -gt 0 ]; then say "${Y}${B}$warn warning(s)${Z}, 0 fail"; exit 1
else say "${G}${B}all checks green${Z}"; exit 0; fi
