# Change log — iterations made in response to issues

Every entry here answers an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) and
cites its id, per PROCESS.md §3 (reciprocal pair) and §6. Newest last; entries
are appended, never rewritten.

Entry ids follow `process.yaml: definitions.change-id` —
`<description>_<hash8>`. Both segments derive from the **`iteration` field
alone** (PROCESS.md §10, decision 8): the description is that field run through
`slug_rule`, and the hash is the first 8 hex characters of `sha256` over it
canonicalised — trimmed, lowercased, whitespace runs collapsed to one space,
then trailing `. , ; : ! ?` stripped (decision 14).

Every id in this file was recomputed with `sha256sum` on 2026-09-01. The first
entry's id **moved**: it was minted from the `summary` field before decision 8
settled identity on `iteration`.

---

## move-the-implementation-into-tooling-v1_6206c8de

| Field | Value |
|---|---|
| **id** | `move-the-implementation-into-tooling-v1_6206c8de` — **recomputed 2026-09-01**, replacing `migrate-packages-telegram-to-the-tooling_78deb9ee`. That id was derived from this entry's `summary`; `process.yaml: definitions.change-id` settles identity on the `iteration` field alone. Both segments now come from `iteration (Z)` below |
| **resolves** | [`KNOWN_ISSUES.md#packages-telegram-failed-track-b-conform_9f851380`](KNOWN_ISSUES.md#packages-telegram-failed-track-b-conform_9f851380) |
| **version** | `v1.0.0` — current version, **no bump**. The code did not change, it moved (PROCESS.md §9: an unversioned tool's current code becomes `Tooling/v1.0.0/`) |
| **merge_commit** | **blank.** Nothing is merged: the work sits on branch `smoke/fix-packages-telegram`. Because this field is empty the issue it resolves is `in-progress`, not `resolved` (`process.yaml: definitions.issue-status`) |

**summary.** Migrate Packages/Telegram to the Tooling/Tests versioned layout at
v1.0.0 and create CHANGE_LOG.md.

**cause (Y).** The tool predates PROCESS.md. It was authored as a flat package
directory — `telegram/`, `bin/`, `templates/`, `n8n/`, `examples/`, `tests/`,
`run-tests.sh` all at the tool root — and the convention that a tool's code sits
under `Tooling/v<version>/` and its recorded test output under
`Tests/v<version>/` did not exist when it was written. `CHANGE_LOG.md` had never
been created because no iteration had ever been logged through §6.

**outcome (X).** Packages/Telegram failed three of the five Track B checks of
PROCESS.md §7: canonical files (`CHANGE_LOG.md` absent), code layout (no
`Tooling/`), test layout (no `Tests/`). Under §7 a tool in that state cannot
release a new version, so the next real fix to this package was blocked before
it started.

**iteration (Z).** Move the implementation into `Tooling/v1.0.0/`, repair the
paths the move breaks, run the suite from its new location and record the actual
output under `Tests/v1.0.0/`, create `CHANGE_LOG.md`, and state the current
version in `README.md`.

**expected_result (V).** Checkably:

1. `Packages/Telegram/Tooling/v1.0.0/` contains the code; the five canonical
   `.md` files remain at the tool root and nothing else does.
2. `./run-tests.sh` run from `Tooling/v1.0.0/` exits 0.
3. The three cross-implementation tests **run** rather than skip — a skip would
   mean the move silently disarmed them.
4. `Tests/v1.0.0/` holds the verbatim output of that run.
5. All five canonical files exist and are non-empty.
6. `README.md`, the newest `Tooling/` directory and this entry all name
   `v1.0.0`.

**change (W).** What changed, where, and how it was verified:

- **Moved** into `Tooling/v1.0.0/`: `telegram/`, `bin/`, `templates/`, `n8n/`,
  `examples/`, `tests/`, `run-tests.sh`. Plain `mv`; no file contents altered by
  the move itself.
- **Left at the tool root**: `README.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`,
  `KNOWN_ISSUES.md`, `CHANGE_LOG.md` (§3), and `.gitignore` — the ignore rules
  (`__pycache__/`, `*.pyc`, state and lock files) apply recursively from the
  root and would stop covering the tool root if moved down.
- **Path repaired — one, and it was load-bearing.**
  `tests/test_conformance.py` resolved `Packages/Poller` by walking three
  directories up from the test file. At the new depth that expression pointed at
  `Packages/Telegram/Tooling/`, so `os.path.isdir` returned False and both
  cross-package conformance tests would have **skipped silently while the suite
  still reported OK** — exactly the failure mode the file's own docstring warns
  about. Replaced with `_poller_sinks_root()`, which walks five directories up
  to `Packages/`, and accepts either the flat `Packages/Poller/poller/` or a
  migrated `Packages/Poller/Tooling/v<version>/poller/` (newest first), so the
  test survives the Poller's own migration. Verified by the tests running:
  `test_envelope_bytes_match_the_poller_sink ... ok` in
  [`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log).
- **Paths checked and found correct at the new depth, unchanged**:
  `run-tests.sh` (`cd "$(dirname "$0")"`, relative discovery of `tests`);
  `bin/telegram` and `tests/helpers.py` (both insert `dirname(dirname(__file__))`
  on `sys.path`, which is still the package root because `telegram/` moved with
  them); `telegram/template.py` `_builtin_dir()` (same two-level walk to
  `templates/`, which also moved); `tests/test_n8n_parity.py` (two-level walk to
  `n8n/`, which also moved). Verified by running, not by inspection alone: the
  suite passes and `./bin/telegram templates` and `./bin/telegram render report`
  both produce correct output from the new location.
- **Created**: `Tests/v1.0.0/run-tests.log` (captured stdout+stderr of the
  verbose run, exit code included), `Tests/v1.0.0/RESULTS.md`, and this file.
- **Edited**: `README.md` only — the Quickstart `cd` path, the `n8n/README.md`
  link, the `grep -rn TG-03` hint, and a Layout section naming the current
  version. Wording and claims otherwise untouched.
- **Not edited**: `IMPLEMENTATIONS.md` (append-only, §5.2) and `TEMPLATES.md`
  (already present and complete). Both contain tool-root-relative paths such as
  `./bin/telegram` and `tests/test_conformance.py` that are now one directory
  further down; this is recorded as an open sub-point on the issue rather than
  fixed by rewriting an append-only document.

**Verification of V, item by item** — re-run and re-checked 2026-09-01, not
carried over from the migration run: 1 ✅ (`ls` of the tool root); 2 ✅ (exit 0);
3 ✅ (zero skips in the log, all three named tests `ok`); 4 ✅; 5 ✅; 6 ✅.

**These six ticks are not a Track B pass, and must not be read as one.** V was
the expected result of *this iteration*; it never contained a reciprocity item.
The honest Track B tick-list — five checks, of which **Reciprocity is ❌** —
is in [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md), and the failure is
logged as
[`KNOWN_ISSUES.md#track-b-reciprocity-fails-for-the-implem_c160a132`](KNOWN_ISSUES.md#track-b-reciprocity-fails-for-the-implem_c160a132).
The migration entry originally carried these six ticks with no such statement
next to them, which read as a clean conformance pass over a check that fails.

---

## extend-the-process-md-9-legacy-rule-to-c_ad654f71

| Field | Value |
|---|---|
| **id** | `extend-the-process-md-9-legacy-rule-to-c_ad654f71` — `sha256sum` over the canonical `iteration` field per `process.yaml: definitions.change-id` |
| **resolves** | [`KNOWN_ISSUES.md#track-b-reciprocity-fails-for-the-implem_c160a132`](KNOWN_ISSUES.md#track-b-reciprocity-fails-for-the-implem_c160a132) |
| **version** | none. No version was created; nothing under `Tooling/` changed |
| **merge_commit** | **blank** — planned only, and the plan is not this branch's to execute. Branch `smoke/fix-packages-telegram` |

**summary.** Plan for the IMPLEMENTATIONS.md ↔ TEMPLATES.md half of Track B
reciprocity, which this tool cannot satisfy without breaking append-only.

**cause (Y).** `IMPLEMENTATIONS.md` and `TEMPLATES.md` predate `PROCESS.md`.
Their entries are prose sections with human-readable headings, not
`<description>_<hash8>` ids, so they cannot cite one another by id. Both
documents are append-only, so the headings cannot be rewritten. PROCESS.md §9
grandfathers pre-conformance *issue* entries only, and the §7 reciprocity check
attaches "non-legacy" only to the `KNOWN_ISSUES.md` clause — leaving the
`IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` clause with a requirement and no exemption.

**outcome (X).** `Packages/Telegram` fails Track B on Reciprocity. Under §7 that
blocks the next genuine iteration on the package, and it makes the six ✅ in the
entry above misleading unless they are explicitly scoped, which they now are.

**iteration (Z).** Extend the PROCESS.md §9 legacy rule to cover
pre-conformance IMPLEMENTATIONS.md and TEMPLATES.md entries, so the
IMPLEMENTATIONS ↔ TEMPLATES half of Track B reciprocity can be satisfied
without rewriting append-only entries.

**expected_result (V).** Checkably, after the spec change lands:

1. §9 defines a legacy marking for `IMPLEMENTATIONS.md` and `TEMPLATES.md`
   entries that predate a tool's first conformant version, mirroring decision 7.
2. §7's Reciprocity row exempts those entries the way it exempts legacy issue
   entries, with the exemption written into the check rather than assumed.
3. Every `IMPLEMENTATIONS.md` and `TEMPLATES.md` entry in this tool that
   predates 2026-08-31 carries that marking, added as a field and changing
   nothing else — the same single permitted edit §9 already allows.
4. Track B run against `Packages/Telegram` then returns five ✅ **for real**,
   with the reciprocity tick backed by the exemption rather than by wording.

**change (W).** Nothing in this tool. The change is to `PROCESS.md` §7/§9 and
`process.yaml: definitions` — files this branch is forbidden to touch (they are
PR #16's). This entry exists so the failure has a recorded, reciprocal plan
instead of sitting as an untracked sub-point, and so the issue it resolves is
not the only non-legacy entry in `KNOWN_ISSUES.md` without a counterpart.

**Status of the plan: escalated, not executed.** No `Tooling/` directory was
created, no version was cut, and no test was run for it. Recorded per
`process.yaml: definitions.escalate` — the work is left where it stands for the
owner to judge.

---

## mark-packages-telegram-s-pre-conformance_4e15f56e

| Field | Value |
|---|---|
| **id** | `mark-packages-telegram-s-pre-conformance_4e15f56e` — `sha256` over the canonical `iteration` field per `process.yaml: definitions.change-id`. Written as `**iteration.**` rather than `**iteration (Z).**` so the field is machine-readable and the id reproduces under `bin/trackb-check.py` — the two entries above use the parenthesised form and are reported as "no iteration field to hash" (PROCESS.md §10 decision 23) |
| **resolves** | [`KNOWN_ISSUES.md#the-escalated-reciprocity-issue-is-stale_8a23643b`](KNOWN_ISSUES.md#the-escalated-reciprocity-issue-is-stale_8a23643b) |
| **version** | `v1.0.0` — current version, **no bump**. Documents only; nothing under `Tooling/v1.0.0/` was touched, so no released version directory was edited and no new one was opened (§5 safeguard 2) |
| **merge_commit** | **blank.** Nothing is merged: the work sits on branch `fix/legacy-telegram`. Because this field is empty the issue it resolves is `in-progress`, not `resolved` (`process.yaml: definitions.issue-status`) |

**summary.** Apply the amended PROCESS.md §9 legacy exemption to this tool's
pre-conformance IMPLEMENTATIONS.md and TEMPLATES.md entries.

**cause (Y).** `IMPLEMENTATIONS.md` and `TEMPLATES.md` predate `PROCESS.md`. Their
sections carry human-readable headings and cross-reference by template *name*, so
under `process.yaml: definitions.entry` none is an addressable entry and the pair
cannot cite one another by id. Both documents are append-only, so the headings
cannot be rewritten. That was
[`KNOWN_ISSUES.md#track-b-reciprocity-fails-for-the-implem_c160a132`](KNOWN_ISSUES.md#track-b-reciprocity-fails-for-the-implem_c160a132),
escalated because the only real fix was a change to the spec. The spec has since
been amended — §9 now grandfathers all four entry documents, and decision 16
extends the exemption to heading form — so the marking is now available and
nothing else about the documents needs to change.

**outcome (X).** `bin/trackb-check.py Packages/Telegram` failed the Reciprocity
check, as a hard FAIL, on 25 level-2 headings across the pair — 8 in
`IMPLEMENTATIONS.md`, 17 in `TEMPLATES.md`. 24 of the 25 were reported as "not a
bare id" — the exception is `## Environment`, where a single capitalised word
happens to satisfy the free-slug regex `definitions.impl-id / template-id`
allows, so it passed heading form by accident and failed only the citation half.
24 were reported as citing no counterpart id. Under §7 that blocks the next
genuine iteration on the package.

**iteration.** Mark Packages/Telegram's pre-conformance IMPLEMENTATIONS.md and TEMPLATES.md
entries `status: legacy` under the amended PROCESS.md §9, demote its prose
sections to level 3, and record the true status of the escalated issue by
appending rather than editing it.

**expected_result (V).** Checkably:

1. `python3 bin/trackb-check.py Packages/Telegram` reports no FAIL. Status and
   Id-reproduction advisories may remain (decision 23).
2. Every marking is the addition of a `status` field and nothing else — no
   heading text, no prose, no ordering changed in either document.
3. Every section demoted rather than marked records no use case and cites no
   template, so demoting it states a fact about the section rather than
   narrowing the check.
4. `c160a132` is untouched, and its corrected status is stated in an appended
   entry (decision 22).

**change (W).** What changed, where, and how it was verified:

- **`IMPLEMENTATIONS.md` — 6 sections marked `status: legacy`**: `Worked example:
  the Poller`, `Worked example: a human gate in a script`, `Worked example:
  replacing a hand-rolled format string`, `From Python`, `Environment`,
  `Choosing a destination workflow`. Each describes a way the tool is wired into a
  caller — a use case, which is what §3 says this document records — and each
  predates v1.0.0. One `**status.**` line was inserted after each heading; nothing
  else in the section was touched. The form is copied from
  `Packages/Scrape/IMPLEMENTATIONS.md`, which made this edit first.
- **`IMPLEMENTATIONS.md` — 2 sections demoted to level 3**: `The five commands`
  (the CLI surface, a reference table) and `Adding a template` (guidance on
  authoring a catalogue entry — the exact analogue of decision 18's own example,
  "Adding an entry", and of the `# Adding a template` section
  `Packages/Scrape/TEMPLATES.md` already keeps out of entry position). Neither
  names a use case or cites a template. They are prose, so they belong at level 3
  (decision 18); marking a reference table `legacy` would assert it is an entry.
- **`TEMPLATES.md` — 16 entries marked `status: legacy`**: every message-type
  section from `` `poller.settled` `` to `` `poll` ``. These *are* the templates
  this document exists to record — they are entries, not prose — and they are the
  16 §9 counts. They were marked rather than re-headed because their heading text
  is the runtime template id (`./bin/telegram render poller.settled`): it contains
  a dot, which `definitions.impl-id / template-id` forbids, so a bare-id heading
  means renaming the templates and breaking every reference to them by name in
  `README.md`, `IMPLEMENTATIONS.md` and `KNOWN_ISSUES.md`. §9 forbids exactly that
  rewrite, and the amendment exists so it is not needed.
- **`TEMPLATES.md` — 1 section demoted to level 3**: `How to read an entry`, which
  explains the document's own field table. Document guidance, not a template.
- **`KNOWN_ISSUES.md`** — appended
  [`#the-escalated-reciprocity-issue-is-stale_8a23643b`](KNOWN_ISSUES.md#the-escalated-reciprocity-issue-is-stale_8a23643b),
  which states the corrected status of `c160a132` (`in-progress`) without editing
  it. **`c160a132` and `9f851380` were not modified**, and neither was any `TG-`
  entry.
- **Not touched**: `PROCESS.md`, `process.yaml`, `bin/`, `README.md`, anything
  under `Tooling/` or `Tests/`, and every other tool. This is a documents-only
  change; the suite was neither re-run nor altered, and `Tests/v1.0.0/` still
  records the v1.0.0 run verbatim.

**Verification of V, item by item.** 1 ✅ — `python3 bin/trackb-check.py
Packages/Telegram` reports Canonical files, Code layout, Test layout,
**Reciprocity**, Status and Version agreement all PASS, with Id reproduction the
sole remaining advisory (three pre-existing entries, all of them above this one,
none of them re-writable). 2 ✅ — `git diff` on both documents shows only inserted
`**status.**` blocks and three `##` → `###` heading-level changes. 3 ✅ — stated
section by section under **change (W)**. 4 ✅ — `git diff Packages/Telegram/KNOWN_ISSUES.md`
shows pure addition at end of file.

**One honest cost of the demotions.** `IMPLEMENTATIONS.md` is append-only, so its
sections cannot be reordered. `### Adding a template` therefore now sits between
two level-2 sections and renders as a subsection of the worked example above it.
The heading level is what decision 18 constrains and level 3 is what it requires;
fixing the apparent nesting would mean moving the section, which invariant 2
forbids. Recorded rather than quietly left.

**`Tests/v1.0.0/RESULTS.md` still records Reciprocity as ❌.** That file is the
verbatim record of the v1.0.0 run and is not rewritten (§5 invariant 6). The
current Track B result for this tool is the checker output cited under
**Verification of V** above, not that tick-list.
