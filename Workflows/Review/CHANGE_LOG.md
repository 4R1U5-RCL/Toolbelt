# Change log — Workflows/Review

Every iteration made in response to an entry in [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)
(PROCESS.md §3). Ids are computed per `process.yaml` `definitions.change-id`.

| id | Resolves | Version |
|---|---|---|
| [`migrate-workflows-review-to-the-track-b_abb4adaf`](#migrate-workflows-review-to-the-track-b_abb4adaf) | [`workflows-review-fails-track-b-conforman_0b0b4b59`](KNOWN_ISSUES.md#workflows-review-fails-track-b-conforman_0b0b4b59) | v1.0.0 |

---

<a name="migrate-workflows-review-to-the-track-b_abb4adaf"></a>
## `migrate-workflows-review-to-the-track-b_abb4adaf`

| Field | Value |
|---|---|
| **id** | `migrate-workflows-review-to-the-track-b_abb4adaf` |
| **summary** | Migrate Workflows/Review to the Track B document layout at v1.0.0 and record that the tool has no implementation to move |
| **resolves** | [`KNOWN_ISSUES.md#workflows-review-fails-track-b-conforman_0b0b4b59`](KNOWN_ISSUES.md#workflows-review-fails-track-b-conforman_0b0b4b59) |
| **version** | **v1.0.0** — no bump. No code changed, and none moved, because none exists. Per PROCESS.md §9 an unversioned tool starts at v1.0.0; this iteration establishes that version rather than succeeding one |
| **merge_commit** | not yet recorded — this iteration ran before merge, and performed no git operations of its own |
| **date** | 2026-08-31 |

**cause (Y).** `Workflows/Review` was left as a placeholder directory and never
taken through PROCESS.md §9's conformance step — and, separately and more
fundamentally, the review workflow itself has never been written. See the two
causes distinguished in the issue entry.

**outcome (X).** All five Track B checks failed. The tool was a single 42-byte
`README.md` reading "This folder contains the review workflow." and nothing else:
four canonical documents absent, no `Tooling/`, no `Tests/`, no version named
anywhere — a directory that claims a workflow and supplies none, with no issue
log or change log to make that visible.

**iteration (Z).** Create the §3 document set and the §4 version directories at
v1.0.0, with every new document stating plainly that no implementation, use case,
template or test exists. Do **not** invent a workflow, a template, or a test
result to make a check pass.

**expected_result (V).** Checkably, after this iteration:

1. All five canonical files exist at the tool root and are non-empty.
2. `KNOWN_ISSUES.md` and `CHANGE_LOG.md` each carry one entry citing the other's
   id; `IMPLEMENTATIONS.md` and `TEMPLATES.md` carry zero entries, so their
   reciprocity check passes vacuously and both say so explicitly.
3. `Tooling/v1.0.0/` and `Tests/v1.0.0/` exist, and each states in-place that it
   holds no code / no test output and why.
4. `README.md`, the newest `Tooling/` directory and this, the newest
   `CHANGE_LOG.md` entry, all name **v1.0.0**.
5. No statement in any new document asserts anything about the review workflow's
   purpose, steps or usage — because the repo contains no such information.

Deliberately **not** expected: a passing test suite, or Code-layout and
Test-layout checks passing in substance. Both are impossible without the tool
existing, and the issue entry records them as still open.

**change (W).** What changed, where, and how it was verified:

1. **Layout.** Nothing moved. `find . -mindepth 1` returned `./README.md` alone
   before the migration — there was no `bin/`, `lib/`, `commands/`, `examples/`,
   `templates/`, `n8n/`, `tests/` or `run-tests.sh` to relocate into
   `Tooling/v1.0.0/`. The directory was created and carries
   `Tooling/v1.0.0/NOTE.md`, which records that it is empty of code and why.
2. **Paths.** No path repair was needed or possible: there is no script, no
   `sys.path` manipulation, no import, and no `bin/` entrypoint in this tool.
3. **Recorded results.** No test was run — there is no `run-tests.sh` and no
   `tests/` directory, so there is nothing to execute.
   [`Tests/v1.0.0/RESULTS.md`](Tests/v1.0.0/RESULTS.md) states exactly that,
   with the verbatim shell output showing the absence, per PROCESS.md §5.6:
   an unrun test is recorded as unrun, never as a pass.
4. **Documents.** `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md` and
   `CHANGE_LOG.md` created; `README.md` extended to name v1.0.0 and to describe
   the tool's actual state. The pre-existing sentence "This folder contains the
   review workflow." is preserved verbatim.

**Verification.** Checked by listing the tool directory after the change and
re-reading each file: the five canonical files exist and are non-empty; this
entry and the issue entry cite each other by id; `README.md`,
`Tooling/v1.0.0/` and this entry all name v1.0.0.

**Note on git.** This iteration ran under an orchestrator that owns all git
operations. No branch was created, nothing was committed, and no PR was opened
from here; PROCESS.md §6 steps 3, 5, 6 and 7 — branch, PR, human approval, merge
— are the orchestrator's to perform, and `merge_commit` above stays unrecorded
until they do.
