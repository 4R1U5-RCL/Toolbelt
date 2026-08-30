#!/usr/bin/env bash
# fleet-board — the orchestrator's SAFE writer for the canonical SPRINT.md.
# The orchestrator is the SOLE writer of SPRINT.md; this gives it atomic, crash-safe primitives
# (write to temp → rename) instead of an interrupted `>>` that could corrupt the board.
#
# Usage (WT = the sprint worktree dir, e.g. .../.claude/worktrees/sprint-<slug>):
#   fleet-board addrow <WT> <ID> <WORKER> <task...>  # add a §3 delegation row (ASSIGNED) on assignment
#   fleet-board append <WT> <text...>     # append a timestamped bullet to §5 STATUS LOG (atomic)
#   fleet-board setrow <WT> <ID> <STATUS>  # flip the §3 delegation row's status cell (atomic)
#   fleet-board commit <WT> [msg]          # git add SPRINT.md + commit, as one retryable unit
#   fleet-board show   <WT>                # print §3 + §5 (quick board glance)
set -euo pipefail
cmd="${1:?append|setrow|commit|show}"; shift || true
WT="${1:?<WT> = sprint worktree dir}"; shift || true
DOC="$WT/SPRINT.md"
[ -f "$DOC" ] || { echo "no SPRINT.md at $DOC" >&2; exit 2; }
ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

_atomic() { local tmp="$DOC.tmp.$$"; cat > "$tmp"; mv "$tmp" "$DOC"; }   # temp → atomic rename

case "$cmd" in
  addrow)
    id="${1:?<ID>}"; worker="${2:?<WORKER>}"; shift 2 || true; task="${*:?<task>}"
    grep -qE "^\| $id \|" "$DOC" && { echo "row $id already exists" >&2; exit 3; }
    row="| $id | $worker | $task | ASSIGNED | — | — | $ts |"
    # insert directly under the §3 table separator (stays contiguous with the table; newest-first)
    awk -v row="$row" '
      /^## 3\./{s3=1} /^## 4\./{s3=0}
      {print}
      s3 && !ins && /^\|[-: ]+\|[-: ]+\|/ {print row; ins=1}
      END{ if(!ins) exit 4 }' "$DOC" | _atomic \
      && echo "added §3 row: $id → $worker ($task)" \
      || { echo "could not find §3 table separator" >&2; exit 4; }
    ;;
  append)
    line="- \`[$ts]\` $*"
    # insert the bullet just before the "## 6." heading so it stays inside §5; else append at EOF
    if grep -q '^## 6\.' "$DOC"; then
      awk -v L="$line" '/^## 6\./ && !done {print L; done=1} {print}' "$DOC" | _atomic
    else
      { cat "$DOC"; printf '%s\n' "$line"; } | _atomic
    fi
    echo "appended to §5: $*"
    ;;
  setrow)
    id="${1:?<ID>}"; status="${2:?<STATUS>}"
    # rewrite the 4th pipe-field (Status) of the row whose 1st field is <ID>
    awk -F'|' -v id=" $id " -v st=" $status " 'BEGIN{OFS="|"}
      $0 ~ /^\|/ && $2==id {$5=st; changed=1}
      {print}
      END{ if(!changed) exit 3 }' "$DOC" | _atomic \
      && echo "row $id → $status" || { echo "row $id not found in §3 table" >&2; exit 3; }
    ;;
  commit)
    msg="${*:-sprint: update board $ts}"
    git -C "$WT" -c user.email=orchestrator@local -c user.name=orchestrator add SPRINT.md
    git -C "$WT" -c user.email=orchestrator@local -c user.name=orchestrator commit -q -m "$msg" \
      && echo "committed: $msg" || echo "(nothing to commit)"
    ;;
  show)
    awk '/^## 3\./{p=1} /^## 4\./{p=0} p; /^## 5\./{q=1} /^## 6\./{q=0} q' "$DOC"
    ;;
  *) echo "usage: fleet-board {addrow|append|setrow|commit|show} <WT> ..." >&2; exit 2 ;;
esac
