#!/usr/bin/env bash
# Offline smoke test for the shipped Skills/Memory package. Sandboxed under $SB; installs the
# templates, cuts a fixture memory dir FROM them, and validates the format + the "index is recall"
# invariant. Actively demonstrates the drift failure mode (un-indexed entry) then fixes it.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PKG="$(cd "$HERE/.." && pwd)"; TOOL="$HERE/mem_tool.py"; SB="$(mktemp -d)"; trap 'rm -rf "$SB"' EXIT
P=0; F=0
ok(){ if eval "$2"; then echo "  PASS · $1"; P=$((P+1)); else echo "  FAIL · $1"; F=$((F+1)); fi; }
LINT(){ eval "$(python3 "$TOOL" lint "$1")"; }   # sets ENTRIES/INDEXED_OK/ORPHANS/... vars

# --- 1. Install templates per README ---
mkdir -p "$SB/.claude/data/templates" "$SB/memory"
cp "$PKG/templates/MEMORY.md.template"       "$SB/.claude/data/templates/"
cp "$PKG/templates/memory-entry.md.template" "$SB/.claude/data/templates/"
ok "install: MEMORY.md.template placed"       '[ -s "$SB/.claude/data/templates/MEMORY.md.template" ]'
ok "install: memory-entry.md.template placed" '[ -s "$SB/.claude/data/templates/memory-entry.md.template" ]'

# --- 2. Entry template defines the required frontmatter schema ---
ET="$SB/.claude/data/templates/memory-entry.md.template"
ok "entry template has name/description/metadata.type + type enum" \
  'grep -q "^name:" "$ET" && grep -q "^description:" "$ET" && grep -q "metadata:" "$ET" && grep -q "type:" "$ET" && grep -q "user | feedback | project | reference" "$ET"'

# --- 3. Cut a fixture memory dir FROM the shipped templates ---
python3 "$TOOL" build "$SB/memory" "$SB/.claude/data/templates"
ok "build: two entries + index created from templates" '[ "$(ls "$SB/memory"/*.md | wc -l)" -eq 3 ]'

# --- 4. Format + consistency on the clean fixture ---
LINT "$SB/memory"
ok "frontmatter valid on every entry (keys+enum+name==stem)" '[ -z "$FRONTMATTER_BAD" ] || [ "$FRONTMATTER_BAD" = "" ]'
ok "index-is-recall: every entry is indexed (no orphans)"    '[ "$INDEXED_OK" = "1" ]'
ok "no dangling index links (every row resolves to a file)"  '[ -z "$DANGLING_INDEX" ]'
ok "MEMORY.md carries no frontmatter block"                  '[ "$INDEX_HAS_FRONTMATTER" = "0" ]'
ok "index rows well-formed (- [t](f.md) — hook)"            '[ "$INDEX_ROWS_MALFORMED" = "0" ]'
ok "index under 200-line ceiling"                            '[ "$MAXLEN_OK" = "1" ]'

# --- 5. Wikilinks: resolved works; dangling allowed but reported ---
ok "wikilink resolves ([[reference_toolbelt-repo]] <-> file)" 'echo "$WL_RESOLVED" | grep -q "reference_toolbelt-repo"'
ok "wikilink resolves ([[project_toolbelt-skills]] <-> file)" 'echo "$WL_RESOLVED" | grep -q "project_toolbelt-skills"'
ok "dangling wikilink flagged, not fatal ([[project_future-thing]])" 'echo "$WL_DANGLING" | grep -q "project_future-thing"'

# --- 6. DRIFT DEMO: an un-indexed entry is the #1 caveat — prove the checker catches it ---
cat > "$SB/memory/project_orphan.md" <<'E'
---
name: project_orphan
description: an entry deliberately not added to the index
metadata:
  type: project
---
This fact exists on disk but is missing from MEMORY.md, so recall never loads it.
E
LINT "$SB/memory"
ok "drift: un-indexed entry detected as orphan"     'echo "$ORPHANS" | grep -q "project_orphan.md"'
ok "drift: INDEXED_OK flips to 0 while orphan present" '[ "$INDEXED_OK" = "0" ]'
# fix it: add the index pointer (the required same-change discipline)
printf -- '- [Orphan](project_orphan.md) — now indexed so recall can load it\n' >> "$SB/memory/MEMORY.md"
LINT "$SB/memory"
ok "drift: adding the index pointer clears the orphan" '[ "$INDEXED_OK" = "1" ] && [ -z "$ORPHANS" ]'

# --- 7. Dangling INDEX link (row pointing at a missing file) is caught ---
cp "$SB/memory/MEMORY.md" "$SB/memory/MEMORY.md.bak"
printf -- '- [Ghost](reference_missing.md) — points at a file that does not exist\n' >> "$SB/memory/MEMORY.md"
LINT "$SB/memory"
ok "dangling index row (missing file) is flagged" 'echo "$DANGLING_INDEX" | grep -q "reference_missing.md"'
mv "$SB/memory/MEMORY.md.bak" "$SB/memory/MEMORY.md"   # restore
LINT "$SB/memory"
ok "restored: index clean again" '[ -z "$DANGLING_INDEX" ] && [ "$INDEXED_OK" = "1" ]'

echo; echo "== memory smoke: $P passed, $F failed =="
exit $([ $F -eq 0 ] && echo 0 || echo 1)
