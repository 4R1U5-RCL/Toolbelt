# Change log — Skills/Memory

One entry per iteration made in response to an entry in
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md). Fields are those `process.yaml` defines
under `change-entry`.

Entries are delimited by a level-2 heading whose text is the bare id
(`process.yaml: definitions.entry`) — no backticks, nothing else on the line.

Ids are `<description>_<hash8>` (`process.yaml: definitions.change-id`). A
change-id's identity is the **`iteration` field alone**: the description is that
field slugified, the hash is the first 8 hex characters of sha256 over it,
canonicalised as trim → lowercase → collapse whitespace runs to a single space →
strip trailing punctuation (`. , ; : ! ?`).

---

## migrated-skills-memory-to-the-tooling-v1_16012fef

| Field | Value |
|---|---|
| **id** | `migrated-skills-memory-to-the-tooling-v1_16012fef` |
| **iteration** | Migrated Skills/Memory to the Tooling/v1.0.0 and Tests/v1.0.0 layout and created the four missing canonical documents. |
| **resolves** | [`KNOWN_ISSUES.md#skills-memory-failed-track-b-conformance_6cdef98b`](KNOWN_ISSUES.md#skills-memory-failed-track-b-conformance_6cdef98b) |
| **version** | `v1.0.0` — **no bump.** The code did not change, it moved. PROCESS.md §9: a tool that has never been versioned starts at `v1.0.0`, and its current code becomes `Tooling/v1.0.0/` |
| **branch** | `smoke/fix-skills-memory` |
| **merge_commit** | *(empty — not merged)*. The change is committed on the branch above; the PR, human approval and merge are §6 steps 5–7 and have not happened |
| **date** | 2026-08-31 (migration), corrected 2026-09-01 |

The `iteration` row above is the identity string this id is derived from. It is
recorded here with its trailing full stop; canonicalisation strips trailing
punctuation, so `sha256` over
`migrated skills/memory to the tooling/v1.0.0 and tests/v1.0.0 layout and created the four missing canonical documents`
begins `16012fef` either way.

### Cause (Y)

`Skills/Memory` predates PROCESS.md §3/§4. It was authored as a flat package —
`README.md`, `templates/`, `tests/` — under the earlier `operand-packages`
convention and carried into this repo unchanged, and no §6 fix procedure had
ever run against it to bring it into conformance.

### Outcome (X)

The tool failed four of the five Track B checks: only one of the five canonical
documents existed, the code sat at the tool root instead of under `Tooling/`,
nothing under `Tests/` recorded any run, and `README.md` named no version. With
no recorded version and no rollback point, the tool could not release a new
version and its staleness was invisible.

### Iteration (Z)

Migrated Skills/Memory to the Tooling/v1.0.0 and Tests/v1.0.0 layout and created
the four missing canonical documents — a conformance-only migration at `v1.0.0`:
relocate the code and test code into `Tooling/v1.0.0/`, run and record the
existing suite under `Tests/v1.0.0/`, and author the four missing canonical
documents from what is actually in the tool.

### Expected result (V)

Checkably, after this change:

- All five canonical files exist at the tool root and are non-empty.
- `Tooling/v1.0.0/` holds `templates/` and `tests/`; nothing but the five `.md`
  files, `Tooling/` and `Tests/` remains at the tool root.
- `Tooling/v1.0.0/tests/verify.sh` runs from its new location and exits 0.
- `Tests/v1.0.0/` holds the verbatim output of that run.
- `README.md`, the newest `Tooling/` directory and this entry all name `v1.0.0`.
- Every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` id and vice versa;
  this entry and its issue cite each other.
- Every entry heading in this file and in `KNOWN_ISSUES.md` is the bare id, and
  every id reproduces from its identity field under the canonicalisation above.

### Change (W) — what changed, where, how it was verified

| What | Where | Verification |
|---|---|---|
| `templates/` and `tests/` relocated | → `Tooling/v1.0.0/templates/`, `Tooling/v1.0.0/tests/` | `find` over the tool directory; tool root now holds only the five `.md` files plus `Tooling/` and `Tests/` |
| Path repair after the move | none was required | `verify.sh` resolves its own directory from `BASH_SOURCE` and reads templates as `$PKG/templates/` where `PKG="$HERE/.."`; moving `tests/` and `templates/` together preserved that. `mem_tool.py` does no `sys.path` manipulation and takes every path as an argument |
| Test results recorded | `Tests/v1.0.0/run-tests.log`, `Tests/v1.0.0/RESULTS.md` | Captured verbatim: `== memory smoke: 18 passed, 0 failed ==`, `exit=0`. Re-run 2026-09-01 on branch `smoke/fix-skills-memory` from `Tooling/v1.0.0/` and from the tool root; identical both times |
| `TEMPLATES.md` created | tool root | Documents the two real files in `Tooling/v1.0.0/templates/`, quoted verbatim; each entry cites its `IMPLEMENTATIONS.md` id |
| `IMPLEMENTATIONS.md` created | tool root | Three implementations derived from `README.md` and the files present; each entry cites a `TEMPLATES.md` id |
| `KNOWN_ISSUES.md` created | tool root | Header plus the first entry, `skills-memory-failed-track-b-conformance_6cdef98b`, citing this change |
| `CHANGE_LOG.md` created | tool root | This file; this entry cites that issue |
| `README.md` updated | tool root | Adds a "Current version: `v1.0.0`" line; repoints the two `templates/…` rows and the `bash tests/verify.sh` self-check line at `Tooling/v1.0.0/`. No other prose changed |
| Conformance corrections (2026-09-01) | `KNOWN_ISSUES.md`, `CHANGE_LOG.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `Tests/v1.0.0/` | Entry headings reduced to the bare id; `status` moved onto the closed set (`in-progress`, not `resolved`, because `merge_commit` is empty); the change entry's identity field relabelled from the non-spec `summary` to `iteration`; branch claims corrected to `smoke/fix-skills-memory`; both ids re-derived with `sha256sum` and unchanged; the suite re-run and its real output re-recorded |

### Process notes (§6)

The iteration was executed on branch `smoke/fix-skills-memory` (§6 step 3), off
the migration commit rather than off a released version directory, because the
code did not change — it moved, and `Tooling/v1.0.0/` is itself the rollback
point this iteration creates (§4, §5 safeguard 1). Steps 5–7 — PR, human
approval, merge, and recording the merge commit — have **not** happened, which
is why `merge_commit` is empty and the issue entry reads `in-progress` rather
than `resolved`.

---

## re-set-the-memory-md-template-quotation_280a0bc0

| Field | Value |
|---|---|
| **id** | `re-set-the-memory-md-template-quotation_280a0bc0` |
| **iteration** | Re-set the MEMORY.md.template quotation in TEMPLATES.md as an indented code block so no quoted line sits at column 0 as a level-2 heading. |
| **resolves** | [`KNOWN_ISSUES.md#templates-md-quoted-memory-md-template_4602c9f9`](KNOWN_ISSUES.md#templates-md-quoted-memory-md-template_4602c9f9) |
| **version** | `v1.0.0` |
| **branch** | `fix/legacy-memory` |
| **merge_commit** | *(empty — not merged)*. Committed on the branch above; PR, human approval and merge are §6 steps 5–7 and have not happened |
| **date** | 2026-09-01 |

**No bump.** Nothing under `Tooling/v1.0.0/` was touched — no tool code, no
shipped template, no test. The change is confined to the canonical documents at
the tool root, so `v1.0.0` remains both the current version and the rollback
point (§4, §5 safeguard 1), and `Tooling/v1.0.0/tests/verify.sh` was not re-run:
it has no input that changed.

Appended, not folded into
[`migrated-skills-memory-to-the-tooling-v1_16012fef`](#migrated-skills-memory-to-the-tooling-v1_16012fef),
per §10 decision 22 — a correction to an unmerged entry is a new pair, never an
in-place edit.

### Cause (Y)

`TEMPLATES.md` reproduced `Tooling/v1.0.0/templates/MEMORY.md.template` verbatim
inside a fenced block. Four of that file's lines — `## User`, `## Feedback`,
`## Project`, `## Reference` — therefore sat flush left in a document where
`## ` is the entry delimiter (§10 decision 13). `bin/trackb-check.py` reads
entries line by line with no fence state, so it saw six entries where the tool
has two, and the four phantoms cite no `IMPLEMENTATIONS.md` id because they are
template content rather than forms. The file's preamble had asserted the fence
made them safe; the parser does not read preambles.

### Outcome (X)

Reciprocity failed with four findings — `TEMPLATES.md#User`,
`#Feedback`, `#Project` and `#Reference` each "cites no IMPLEMENTATIONS.md id" —
which is the whole of the tool's Track B failure. The other four checks passed.
Under §7 a tool failing Track B cannot release a new version, so the unmerged
`v1.0.0` migration was blocked on a defect in how one entry quotes a file.

### Iteration (Z)

Re-set the MEMORY.md.template quotation in TEMPLATES.md as an indented code
block so no quoted line sits at column 0 as a level-2 heading — a documents-only
change: indent the quoted block four spaces, say in the entry that the indent is
display-only, and correct the preamble sentence that had excused the flush-left
`##` lines.

The alternative fixes were rejected on the facts. Manufacturing four
`IMPLEMENTATIONS.md` entries for `User`/`Feedback`/`Project`/`Reference` would
invent four templates this tool does not ship (invariant 6 in spirit: a document
must record what is there). Demoting them to level 3 under §10 decision 18 would
edit the text of a shipped file inside its own quotation. Marking anything
`legacy` is unavailable: §9 grandfathers only entries predating a tool's first
conformant version, and this tool had no entries at all before 2026-08-31.

### Expected result (V)

Checkably, after this change:

- `python3 bin/trackb-check.py Skills/Memory` reports `Reciprocity` PASS, with
  `2 TEMPLATES` entries rather than 6 — `memory-md-template` and
  `memory-entry-md-template`, the two real files under
  `Tooling/v1.0.0/templates/`.
- All five checks pass and no advisory is raised.
- The quoted template text is unchanged apart from a uniform four-space indent;
  `diff` against `Tooling/v1.0.0/templates/MEMORY.md.template` shows only that
  indent.
- This entry and its issue cite each other, and both ids reproduce from their
  identity fields.

### Change (W) — what changed, where, how it was verified

| What | Where | Verification |
|---|---|---|
| Fenced quotation re-set as an indented code block | `TEMPLATES.md`, `memory-md-template` entry | `diff` of the de-indented block against `Tooling/v1.0.0/templates/MEMORY.md.template` — identical; `grep -n '^## ' TEMPLATES.md` now returns exactly the two entry headings |
| Lead-in sentence states the indent is display-only | `TEMPLATES.md`, same entry | Read: the entry no longer claims a verbatim reproduction it does not give, and names why the indent is there |
| Preamble sentence corrected | `TEMPLATES.md`, header | It previously said the other `##` lines "are template content rather than headings"; it now states the rule the file keeps — no line begins `## ` at column 0 except an entry heading |
| Issue and change entries appended | `KNOWN_ISSUES.md`, `CHANGE_LOG.md` | Both ids recomputed from their identity fields; the checker's `Id reproduction` and `Status` checks pass with no advisory |
| Track B result recorded | `Tests/v1.0.0/RESULTS.md` | New dated section holding the verbatim checker output, appended below the 2026-09-01 hand-read table it supersedes |

### Process notes (§6)

Steps 1 and 4 only: the pair above was appended and the documents-only iteration
executed on `fix/legacy-memory`. No new version directory was opened (§6 step 3)
because no code changed — §4's rollback point and the current version are the
same intact `Tooling/v1.0.0/`. Steps 5–7 have not happened, which is why
`merge_commit` is empty and the issue reads `in-progress`.

The underlying parser limitation — `entries()` treats a fenced `## ` line as a
heading — is recorded in the issue's Cause section and left open. It belongs to
`bin/trackb-check.py` and to a §10 decision, neither of which is this tool's to
change.
