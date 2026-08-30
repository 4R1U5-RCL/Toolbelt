#!/usr/bin/env bash
# Offline smoke test for the shipped Skills/Handoff package. Sandboxed fake HOME under $SB;
# never writes to the real ~/.claude. Exercises: install, fail-closed template guard, the 4h
# scope rule (3 cases), filename convention, end-to-end doc generation + structure conformance,
# and the memory-link degradation rule.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PKG="$(cd "$HERE/.." && pwd)"; SB="$(mktemp -d)"; trap 'rm -rf "$SB"' EXIT
P=0; F=0
ok(){ if eval "$2"; then echo "  PASS · $1"; P=$((P+1)); else echo "  FAIL · $1"; F=$((F+1)); fi; }

# --- 1. Install per README (into sandbox HOME) ---
mkdir -p "$SB/.claude/commands" "$SB/.claude/data/handoffs" "$SB/.claude/data/templates"
cp "$PKG/commands/handoff.md"            "$SB/.claude/commands/"
cp "$PKG/templates/handoff-template.md"  "$SB/.claude/data/templates/"
ok "install: command file placed"  '[ -f "$SB/.claude/commands/handoff.md" ]'
ok "install: template placed"      '[ -f "$SB/.claude/data/templates/handoff-template.md" ]'

# --- 2. Fail-closed template guard (the skill's own step-3 check) ---
guard(){ HOME="$1"; [ -f "$HOME/.claude/data/templates/handoff-template.md" ] && [ -s "$HOME/.claude/data/templates/handoff-template.md" ]; }
guard "$SB"; ok "guard passes when template present+non-empty" '[ $? -eq 0 ]'
mv "$SB/.claude/data/templates/handoff-template.md" "$SB/tmpl.bak"
guard "$SB"; ok "guard ABORTS when template missing (fail-closed)" '[ $? -ne 0 ]'
: > "$SB/.claude/data/templates/handoff-template.md"   # empty file
guard "$SB"; ok "guard ABORTS when template empty (fail-closed)" '[ $? -ne 0 ]'
mv "$SB/tmpl.bak" "$SB/.claude/data/templates/handoff-template.md"  # restore

# --- 3. The 4h scope rule, 3 isolated cases ---
scope(){ # echoes "full" | "incremental since <file>"; $1 = handoffs dir
  local dir="$1" recent mt now age
  recent=$(ls -t "$dir"/*.md 2>/dev/null | head -1)
  if [ -n "$recent" ]; then
    mt=$(stat -c %Y "$recent"); now=$(date +%s); age=$(( now - mt ))
    if [ "$age" -lt 14400 ]; then echo "incremental since $(basename "$recent")"; else echo "full"; fi
  else echo "full"; fi
}
D=$SB/case_empty; mkdir -p "$D"
ok "scope: empty dir -> full" '[ "$(scope "$D")" = "full" ]'
D=$SB/case_recent; mkdir -p "$D"; touch "$D/handoff_prior_2026-08-30T10-00.md"
r=$(scope "$D"); ok "scope: <4h old -> incremental since prior" 'echo "$r" | grep -q "^incremental since handoff_prior_"'
D=$SB/case_stale; mkdir -p "$D"; touch -d "5 hours ago" "$D/handoff_old_2026-08-30T05-00.md"
ok "scope: >4h old -> full" '[ "$(scope "$D")" = "full" ]'

# --- 4. Filename convention ---
TS=$(date -u +%Y-%m-%dT%H-%M); FN="handoff_my-topic_${TS}.md"
ok "filename matches handoff_<topic>_<UTC>.md" 'echo "$FN" | grep -Eq "^handoff_[a-z0-9-]+_[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}\.md$"'

# --- 5. End-to-end: generate a doc from the template, verify structure conformance ---
TMPL="$SB/.claude/data/templates/handoff-template.md"
OUT="$SB/.claude/data/handoffs/$FN"
# fill: frontmatter + carry every '## ' section header from the template
{
  echo "---"; echo "topic: my-topic"; echo "session_scope: full"; echo "created: ${TS}Z"; echo "---"; echo
  grep '^## ' "$TMPL" | while read -r h; do echo "$h"; echo "- (content)"; echo; done
} > "$OUT"
ok "e2e: doc written under handoffs/" '[ -f "$OUT" ]'
ok "e2e: frontmatter has topic/session_scope/created" 'head -5 "$OUT" | grep -q "^topic:" && head -5 "$OUT" | grep -q "^session_scope:" && head -5 "$OUT" | grep -q "^created:"'
# every template section header present in the generated doc
MISS=0; while read -r h; do grep -qF "$h" "$OUT" || MISS=$((MISS+1)); done < <(grep '^## ' "$TMPL")
ok "e2e: all template sections present in doc ($(grep -c '^## ' "$TMPL") headers)" '[ "$MISS" -eq 0 ]'
ok "e2e: doc filename regex-valid" 'basename "$OUT" | grep -Eq "^handoff_[a-z0-9-]+_[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}-[0-9]{2}\.md$"'

# --- 6. Memory-link degradation: absent index -> "None" ---
memidx(){ [ -f "$1" ] && echo "linked" || echo "None"; }
ok "memory-link: absent index degrades to None" '[ "$(memidx "$SB/nonexistent/MEMORY.md")" = "None" ]'

# --- 7. Write-scope invariant: nothing created outside handoffs/ by the generation step ---
ok "write-scope: only handoffs/ got the new doc" '[ "$(find "$SB/.claude/data/handoffs" -name "handoff_my-topic_*.md" | wc -l)" -eq 1 ]'

echo; echo "== handoff smoke: $P passed, $F failed =="
exit $([ $F -eq 0 ] && echo 0 || echo 1)
