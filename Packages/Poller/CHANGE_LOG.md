# Change log — every iteration made in response to a known issue

Reciprocal to [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md): every entry here names the
issue it resolves, and that issue names this entry back (PROCESS.md §3). Ids use
the `<description>_<hash8>` scheme from `process.yaml` →
`definitions.change-id`.

Newest last. Entries are appended, never rewritten.

**Note on history.** This file was created on 2026-08-31 as part of the entry
below, which is therefore the first entry in it. The tool's twenty-two `KI-`
entries in `KNOWN_ISSUES.md` predate this file and have **no** reciprocal change
entries; that history was not reconstructed, because the iterations that closed
those issues were not recorded at the time and inventing them would be
fabrication. Their guards are traceable through the code instead
(`grep -rn KI-07 Tooling/v2.1.0/poller/`).

---

<a name="migrated-packages-poller-code-to-tooling_39621062"></a>
## migrated-packages-poller-code-to-tooling_39621062

| Field | Value |
|---|---|
| **id** | `migrated-packages-poller-code-to-tooling_39621062` |
| **summary** | Migrated Packages/Poller code to Tooling/v2.1.0 and created the missing canonical documents |
| **resolves** | [`KNOWN_ISSUES.md#packages-poller-failed-track-b-conforman_8f776048`](KNOWN_ISSUES.md#packages-poller-failed-track-b-conforman_8f776048) |
| **version** | `v2.1.0` — current version, **no bump**. The code moved; it did not change. A bump would claim a release that never happened and would orphan the rollback point |
| **merge_commit** | not yet merged — this iteration is on a branch, awaiting the PR and human gate (PROCESS.md §6 steps 5–6). Recorded here on merge (§6 step 7) |

**Id derivation.** `hash8` = first 8 hex chars of
`sha256("migrated packages/poller code to tooling/v2.1.0 and created the missing canonical documents")`
(summary, trimmed, lowercased, whitespace collapsed) = `39621062`. `description`
= that summary slugified and truncated to 40 characters.

**Cause (Y).** The tool predates PROCESS.md and was never migrated out of the
flat pre-convention layout; version identity lived in `poller/__init__.py` and
in a PR title rather than in the documents.

**Outcome (X).** Track B failed on four of five checks — canonical files
(`TEMPLATES.md`, `CHANGE_LOG.md` missing), reciprocity (nothing to cite), code
layout (no `Tooling/`), test layout (no `Tests/`) — and on version agreement
(README names no version). Under §7 the tool cannot release a new version until
this is fixed.

**Iteration (Z).** A conformance-only migration of the existing `v2.1.0` code:
relocate, verify, and document. Explicitly **not** a behavioural change — no
file under `poller/`, `tests/`, `examples/`, `n8n/` or `bin/` had its contents
edited, only its path.

**Expected result (V).** Checkably:

1. `Packages/Poller/Tooling/v2.1.0/` holds the whole implementation tree, and
   the five canonical `.md` files remain at the tool root.
2. `./run-tests.sh` run **from the new location** exits `0` with the same test
   count as before the move (187), proving no import, discovery root or shim
   path was broken.
3. `Packages/Poller/Tests/v2.1.0/` holds the verbatim output of that run.
4. All five canonical documents exist and are non-empty, with
   `IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` and `KNOWN_ISSUES.md` ↔ `CHANGE_LOG.md`
   citing each other.
5. `README.md` names `v2.1.0`, agreeing with the newest `Tooling/` directory,
   this entry, and `poller/__init__.py`.

**Change (W).** What changed, where, and how it is verified:

| What | Where | Verified by |
|---|---|---|
| `bin/`, `examples/`, `n8n/`, `poller/`, `tests/`, `run-tests.sh` moved unmodified | tool root → `Tooling/v2.1.0/` | `find` listing; the tool root now holds only the five `.md` files, `.gitignore`, `Tooling/`, `Tests/` |
| Path repairs after the move | **none were needed** | `run-tests.sh` does `cd "$(dirname "$0")"`, `bin/poller` and `tests/helpers.py` derive their `sys.path` root from `__file__`, and `tests/test_config.py` locates `examples/` the same way — all relative to files that moved together |
| Suite re-run from the new location | `Tooling/v2.1.0/` | `Tests/v2.1.0/run-tests.log`: `Ran 187 tests ... OK`, `exit_code=0`, 2026-08-31T15:20:38Z |
| Entry-point smoke check | `Tooling/v2.1.0/bin/poller` | `./bin/poller --version` → `poller 2.1.0`; `./bin/poller status --config examples/generic-http.json` → `NEVER_RAN` (both recorded in `Tests/v2.1.0/RESULTS.md`) |
| `TEMPLATES.md` created | tool root | Catalogues the six application forms that actually exist (5 example configs + the n8n workflow builder) and states plainly that no `templates/` directory exists |
| `CHANGE_LOG.md` created | tool root | This file |
| `KNOWN_ISSUES.md` appended | tool root | New `# Process issues` section; the existing `KI-` table and entries untouched (§5.1) |
| `IMPLEMENTATIONS.md` appended | tool root | New "Template index" section: the six `TEMPLATES.md` citations plus the path shift; existing text untouched (§5.2) |
| `README.md` edited | tool root | Version line added; `cd`/layout paths updated to `Tooling/v2.1.0/`. Minimal edit — no prose rewritten |
| `.gitignore` | left at the tool root | Deliberate: it is repo hygiene covering everything below the tool, not implementation code, and from the root it still covers `Tooling/` |

**Honest limits of this iteration.**

- The `Tests/v2.1.0/` results corroborate that the *move* broke nothing. They do
  **not** corroborate a behavioural fix, because there was none — PROCESS.md §7
  Track A's "a green suite must exercise the logged failure" is satisfied here in
  the only way it can be for a layout issue: the logged failure was the layout,
  and the layout is what the run exercises.
- No git operation was performed by this iteration (no branch, no commit, no
  PR). PROCESS.md §6 steps 3, 5 and 6 remain outstanding and are the merging
  party's to complete; `merge_commit` above stays blank until then.
- The issue entry's status remains `open` for the same reason.
