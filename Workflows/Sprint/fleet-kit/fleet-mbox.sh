#!/usr/bin/env bash
# fleet-mbox — file-based mailbox for parallel Claude Code sessions.
# Fallback transport when ListAgents/SendMessage (peer registration) is unreliable.
# One file per message (never a shared mutable file) → no locks, no torn writes, no lost appends.
# Addressing uses STABLE LOGICAL NAMES (orchestrator | reviewer | A | B | C ...), not studio-XX.
#
# Env:
#   FLEET_ROOT    mailbox root, e.g. /studio/scratch/fleet/<slug>   (required)
#   FLEET_SESSION this session's logical name, e.g. orchestrator|reviewer|A   (for send/lock/ack)
#
# Usage:
#   fleet-mbox init  <name> [<name> ...]     # create inbox/processed dirs for these names
#   fleet-mbox send  <to> [subject...]       # message body on STDIN → <to>'s inbox (atomic)
#                                            #   every message carries an auto sha256 of its body
#                                            #   (the correlation id packets/verdicts cite)
#   fleet-mbox check [who]                    # count unread in who's inbox (default FLEET_SESSION)
#   fleet-mbox ls    [who]                    # list unread filenames only
#   fleet-mbox peek  [who]                    # print unread WITHOUT acking (use before you apply)
#   fleet-mbox read  [who]                    # print unread, then MOVE them to processed/ (ack)
#   fleet-mbox ack   [who]                    # MOVE unread → processed/ WITHOUT printing
#                                            #   (peek → apply → ack = don't lose an unapplied msg)
#   fleet-mbox lock  [name]                   # acquire the single-writer/role lock (atomic; fails if held)
#   fleet-mbox unlock [name]                  # release it (only if you hold it)
#   fleet-mbox lock-status                     # who holds the lock
#   fleet-mbox hash                            # sha256 of STDIN (for citing a packet by hand)
set -euo pipefail

: "${FLEET_ROOT:?set FLEET_ROOT=/studio/scratch/fleet/<slug>}"
cmd="${1:-}"; shift || true

_inbox() { printf '%s/%s/inbox' "$FLEET_ROOT" "$1"; }
_proc()  { printf '%s/%s/processed' "$FLEET_ROOT" "$1"; }
_who()   { printf '%s' "${1:-${FLEET_SESSION:?set FLEET_SESSION or pass a name}}"; }
_sha()   { sha256sum | cut -c1-16; }   # short id is plenty for correlation at this scale

case "$cmd" in
  init)
    [ "$#" -ge 1 ] || { echo "init needs >=1 name" >&2; exit 2; }
    for n in "$@"; do mkdir -p "$(_inbox "$n")" "$(_proc "$n")"; done
    echo "initialized: $* under $FLEET_ROOT"
    ;;
  send)
    to="${1:?send <to> [subject]}"; shift || true
    subject="${*:-}"
    from="${FLEET_SESSION:-unknown}"
    dir="$(_inbox "$to")"; mkdir -p "$dir"
    ts="$(date -u +%Y%m%dT%H%M%S.%N)"
    body="$(cat)"                                   # capture once: needed for hash + write
    sha="$(printf '%s' "$body" | _sha)"
    base="${ts}__from-${from}__$$${RANDOM}"
    tmp="$dir/.tmp.${base}"; final="$dir/${base}.md"
    {
      echo "# msg: ${subject:-<no subject>}"
      echo "from: ${from}   to: ${to}   at: ${ts}Z"
      echo "sha256: ${sha}"                         # correlation id (packet ⇄ verdict)
      echo "---"
      printf '%s\n' "$body"
    } > "$tmp"
    mv "$tmp" "$final"        # atomic rename on same fs → reader never sees a partial file
    echo "sent → ${to}  sha:${sha}  (${final#$FLEET_ROOT/})"
    ;;
  check)
    who="$(_who "${1:-}")"; d="$(_inbox "$who")"
    n=$(find "$d" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')
    echo "$n unread in ${who}/inbox"
    ;;
  ls)
    who="$(_who "${1:-}")"; d="$(_inbox "$who")"
    find "$d" -maxdepth 1 -name '*.md' 2>/dev/null | sort | sed "s#^$FLEET_ROOT/##" || true
    ;;
  peek|read)
    who="$(_who "${1:-}")"; d="$(_inbox "$who")"; p="$(_proc "$who")"; mkdir -p "$p"
    files=$(find "$d" -maxdepth 1 -name '*.md' 2>/dev/null | sort || true)
    [ -n "$files" ] || { echo "(empty: ${who}/inbox)"; exit 0; }
    while IFS= read -r f; do
      echo "═══════════════════════════════ ${f##*/}"
      cat "$f"; echo
      [ "$cmd" = "read" ] && mv "$f" "$p/"
    done <<< "$files"
    [ "$cmd" = "read" ] && echo "(acked → ${who}/processed)"
    ;;
  ack)
    who="$(_who "${1:-}")"; d="$(_inbox "$who")"; p="$(_proc "$who")"; mkdir -p "$p"
    n=0; for f in "$d"/*.md; do [ -e "$f" ] || continue; mv "$f" "$p/"; n=$((n+1)); done
    echo "acked $n → ${who}/processed"
    ;;
  lock)
    name="$(_who "${1:-}")"; ld="$FLEET_ROOT/.lock"
    if mkdir "$ld" 2>/dev/null; then                # mkdir is atomic — the whole lock primitive
      printf 'holder: %s\npid: %s\nat: %sZ\n' "$name" "$$" "$(date -u +%Y%m%dT%H%M%S)" > "$ld/holder"
      echo "LOCK ACQUIRED by ${name}"
    else
      echo "LOCK HELD — refusing. Current holder:" >&2; cat "$ld/holder" 2>/dev/null >&2
      exit 1
    fi
    ;;
  unlock)
    name="$(_who "${1:-}")"; ld="$FLEET_ROOT/.lock"
    [ -d "$ld" ] || { echo "(no lock held)"; exit 0; }
    held="$(sed -n 's/^holder: //p' "$ld/holder" 2>/dev/null || true)"
    if [ "$held" = "$name" ]; then rm -rf "$ld"; echo "LOCK RELEASED by ${name}"
    else echo "refusing: lock held by '${held}', not '${name}'" >&2; exit 1; fi
    ;;
  lock-status)
    ld="$FLEET_ROOT/.lock"
    if [ -d "$ld" ]; then echo "LOCKED:"; cat "$ld/holder" 2>/dev/null; else echo "unlocked"; fi
    ;;
  hash) _sha ;;
  *)
    echo "usage: fleet-mbox {init|send|check|ls|peek|read|ack|lock|unlock|lock-status|hash} ..." >&2
    exit 2 ;;
esac
