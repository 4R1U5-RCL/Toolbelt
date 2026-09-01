#!/usr/bin/env bash
# Smoke test for the shipped Skills/Scratch package. Stands up a REAL throwaway git repo,
# applies the shipped scratch.gitignore, and proves (via git check-ignore + git add) that every
# scratch surface + secret is ignored while normal source stays trackable. Sandboxed under $SB.
# Layout: PKG is the version directory (Tooling/v<version>/) that holds templates/ and tests/;
# TOOLROOT is the tool directory two levels up, where the five canonical .md files live (PROCESS.md §3/§4).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PKG="$(cd "$HERE/.." && pwd)"; TOOLROOT="$(cd "$PKG/../.." && pwd)"; SB="$(mktemp -d)"; trap 'rm -rf "$SB"' EXIT
P=0; F=0
ok(){ if eval "$2"; then echo "  PASS · $1"; P=$((P+1)); else echo "  FAIL · $1"; F=$((F+1)); fi; }
GI="$PKG/templates/scratch.gitignore"

# --- 1. The artifact exists, non-empty, covers the documented surfaces ---
ok "template present + non-empty" '[ -s "$GI" ]'
for pat in 'scratch/' '.runstate/' '.claude/worktrees/' 'clients/' 'labs/' '.env' '\*.key' '\*.pem' '_token'; do
  ok "gitignore covers: $pat" "grep -q \"$pat\" \"$GI\""
done
ok "README points at the shipped template" 'grep -q "scratch.gitignore" "$TOOLROOT/README.md"'

# --- 2. Real git repo: apply the ignore block and check reality ---
R="$SB/repo"; mkdir -p "$R"; git -C "$R" init -q
cp "$GI" "$R/.gitignore"
# create files across every surface + real source
mkdir -p "$R/scratch" "$R/.runstate" "$R/clients/acme" "$R/.claude/worktrees/wt" "$R/labs/proj" "$R/node_modules/x" "$R/src"
echo x > "$R/scratch/note.txt";        echo x > "$R/.runstate/state";       echo x > "$R/clients/acme/run-1.log"
echo x > "$R/.claude/worktrees/wt/f";  echo x > "$R/labs/proj/z";           echo x > "$R/node_modules/x/i.js"
echo SECRET > "$R/.env";               echo K > "$R/api.key";               echo P > "$R/secret.pem"
echo T > "$R/service_token";           echo s > "$R/src/app.ts";            echo r > "$R/README.md"

# should be IGNORED (git check-ignore -q returns 0 when the path IS ignored)
for p in scratch/note.txt .runstate/state clients/acme/run-1.log .claude/worktrees/wt/f labs/proj/z \
         node_modules/x/i.js .env api.key secret.pem service_token; do
  ok "IGNORED: $p" "git -C \"$R\" check-ignore -q \"$p\""
done
# should be TRACKABLE (check-ignore returns non-zero == not ignored)
for p in src/app.ts README.md .gitignore; do
  ok "TRACKABLE: $p" "! git -C \"$R\" check-ignore -q \"$p\""
done

# --- 3. git add -A must stage ONLY the source, never a secret/scratch path ---
git -C "$R" add -A
staged=$(git -C "$R" status --porcelain | awk '{print $2}')
ok "add: src/app.ts staged"        'echo "$staged" | grep -qx "src/app.ts"'
ok "add: README.md staged"         'echo "$staged" | grep -qx "README.md"'
ok "add: .env NOT staged"          '! echo "$staged" | grep -q "\.env"'
ok "add: no secret/token staged"   '! echo "$staged" | grep -Eq "\.pem|\.key|_token"'
ok "add: no scratch/clients staged" '! echo "$staged" | grep -Eq "^scratch/|^clients/|^\.runstate/|^\.claude/"'

echo; echo "== scratch smoke: $P passed, $F failed =="
exit $([ $F -eq 0 ] && echo 0 || echo 1)
