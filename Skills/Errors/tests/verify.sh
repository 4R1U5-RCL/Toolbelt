#!/usr/bin/env bash
# Smoke test for the shipped Skills/Errors package. Static structure checks on the three templates
# + dynamic checks on a fixture registry: signature greppability, the reliable-locator-vs-compact-
# grep fragmentation caveat (live), index<->catalog consistency (+ dangling demo), and the
# duplicate-ID guard (reproduces the live IN-38 class). Sandboxed under $SB.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PKG="$(cd "$HERE/.." && pwd)"; SB="$(mktemp -d)"; trap 'rm -rf "$SB"' EXIT
P=0; F=0
ok(){ if eval "$2"; then echo "  PASS · $1"; P=$((P+1)); else echo "  FAIL · $1"; F=$((F+1)); fi; }
HUB="$PKG/templates/ERRORS_AND_FINDINGS.md.template"
AREA="$PKG/templates/errors-area.md.template"
ENTRY="$PKG/templates/incident-entry.md.template"

# --- 1. Templates present + non-empty ---
for t in "$HUB" "$AREA" "$ENTRY"; do ok "template present: $(basename "$t")" '[ -s "$t" ]'; done

# --- 2. Hub structure ---
ok "hub: grep-first purpose block"      'grep -qi "Grep the registry" "$HUB"'
ok "hub: Index table"                   'grep -q "## Index" "$HUB"'
ok "hub: Part 1 (recurring classes)"    'grep -q "## Part 1" "$HUB"'
ok "hub: Part 3 (open items)"           'grep -q "## Part 3" "$HUB"'
ok "hub: intentionally NO Part 2"       '! grep -q "## Part 2" "$HUB"'
ok "hub: seed PAT-1/2/3 present"        'grep -q "PAT-1" "$HUB" && grep -q "PAT-2" "$HUB" && grep -q "PAT-3" "$HUB"'
ok "hub drift-fix: no hardcoded PAT range" '! grep -qE "PAT-1(…|\.\.)[0-9]" "$HUB"'
ok "hub drift-fix: compile-stamp clarified" 'grep -qi "last full rebuild" "$HUB"'

# --- 3. Area template ---
ok "area: binds to hub"                 'grep -q "ERRORS_AND_FINDINGS.md" "$AREA"'
ok "area: states entry format"          'grep -q "Signature" "$AREA" && grep -q "Guard" "$AREA" && grep -q "Source" "$AREA"'
ok "area: Open items section"           'grep -q "Open items" "$AREA"'
ok "area drift-fix: duplicate-ID guard note" 'grep -qi "grep the prefix" "$AREA"'
ok "area drift-fix: PAT-* not hardcoded range" '! grep -qE "PAT-1(…|\.\.)[0-9]" "$AREA"'

# --- 4. Incident entry: all fields, Signature leads ---
for fld in Signature Cause Fix Guard Status Source; do ok "entry has field: $fld" "grep -q '\\*\\*$fld:' \"\$ENTRY\""; done
first=$(grep -m1 '^- \*\*' "$ENTRY")
ok "entry: Signature is the FIRST field" 'echo "$first" | grep -q "Signature"'

# --- 5. Single entry style across all templates (no compact **XX-N bold-ID lines) ---
ok "style standardized: no compact **XX-N entries" '! grep -hqE "^\*\*[A-Z]{2,}-[0-9]" "$HUB" "$AREA" "$ENTRY"'

# --- 6. DYNAMIC: build a fixture registry (a filled instance of the templates) ---
REG="$SB/reg"; mkdir -p "$REG/errors"
cat > "$REG/ERRORS_AND_FINDINGS.md" <<'H'
# Demo — Errors & Findings Registry
## Index — per-area catalogs
| Area | File | Scope | IDs |
|---|---|---|---|
| Backend | [`errors/backend.md`](errors/backend.md) | api server | `BE-*` |
## Part 1 — Recurring Failure Classes
### PAT-1 — Empty HTTP-200 body → res.json() throws
## Part 3 — Open Items
H
cat > "$REG/errors/backend.md" <<'B'
# Errors & Findings — Backend
> Part of the [Errors & Findings Registry](../ERRORS_AND_FINDINGS.md). Entry format:
> ID — Title · Signature · Cause · Fix · Guard · Status · Source.

## Database
## BE-1 — Postgres refused connection at boot
- **Signature:** ECONNREFUSED 127.0.0.1:5432
- **Cause:** pool started before the DB was ready
- **Fix:** retry-with-backoff on connect
- **Status:** FIXED 2026-08-30
- **Source:** abc1234

## BE-2 — Migration lock never released
- **Signature:** advisory lock 771 held forever
- **Status:** OPEN
- **Source:** run-slug

## Retries
**BE-3 — flaky upstream retry loop** (compact style, simulates live drift)
- *Signature:* 429 storm on token refresh. Status: FIXED. Source: def5678.
B

# 6a. greppability contract: an entry is findable by its signature string
ok "greppable: signature string locates the incident" 'grep -rlF "ECONNREFUSED 127.0.0.1:5432" "$REG/errors" | grep -q backend.md'

# 6b. fragmentation caveat, LIVE: compact grep misses header entries; ID-regex finds all
compact=$(grep -c '^\*\*BE-' "$REG/errors/backend.md")
allids=$(grep -oE 'BE-[0-9]+' "$REG/errors/backend.md" | sort -u | wc -l)
ok "caveat: '^\\*\\*BE-' finds only the 1 compact entry (misses headers)" '[ "$compact" -eq 1 ]'
ok "reliable locator: BE-[0-9]+ finds all 3 IDs"                          '[ "$allids" -eq 3 ]'

# 6c. index <-> catalog consistency + dangling demo
dangling(){ local h="$1" d; for r in $(grep -oE 'errors/[a-z-]+\.md' "$h"); do [ -f "$SB/reg/$r" ] || echo "$r"; done; }
ok "index link resolves (errors/backend.md exists)" '[ -z "$(dangling "$REG/ERRORS_AND_FINDINGS.md")" ]'
printf '| Ghost | [`errors/ghost.md`](errors/ghost.md) | x | `GH-*` |\n' >> "$REG/ERRORS_AND_FINDINGS.md"
ok "dangling index row detected (errors/ghost.md missing)" 'dangling "$REG/ERRORS_AND_FINDINGS.md" | grep -q "errors/ghost.md"'
sed -i '/ghost.md/d' "$REG/ERRORS_AND_FINDINGS.md"
ok "restored: index clean again" '[ -z "$(dangling "$REG/ERRORS_AND_FINDINGS.md")" ]'

# 6d. duplicate-ID guard (the recommended add-time check) — reproduces the live IN-38 class
dupes(){ grep -oE 'BE-[0-9]+' "$1" | sort | uniq -d; }
ok "clean catalog has no duplicate IDs" '[ -z "$(dupes "$REG/errors/backend.md")" ]'
printf '\n## BE-2 — accidentally reused id\n- **Signature:** whatever\n' >> "$REG/errors/backend.md"
ok "guard: duplicate BE-2 is detected" 'dupes "$REG/errors/backend.md" | grep -qx "BE-2"'

echo; echo "== errors smoke: $P passed, $F failed =="
exit $([ $F -eq 0 ] && echo 0 || echo 1)
