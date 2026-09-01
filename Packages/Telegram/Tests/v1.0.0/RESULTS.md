# Test results — v1.0.0

Recorded verbatim per PROCESS.md §5 invariant 6. Full captured output:
[`run-tests.log`](run-tests.log).

| | |
|---|---|
| Version under test | `v1.0.0` (`Tooling/v1.0.0/`) |
| Command | `cd Packages/Telegram/Tooling/v1.0.0 && ./run-tests.sh -v` |
| Run at | 2026-09-01T04:36+00:00 (container local time) — re-run from `Tooling/v1.0.0/` while correcting this tool's migration entries |
| Runner | `python3 -m unittest discover -s tests -t tests` (Python 3.11.2, Linux 6.6.135) |
| Node available | yes — `node v22.23.1` |
| Outcome | **PASS** — `Ran 189 tests in 1.148s` / `OK`, exit code 0 |
| Skips | none — 0 tests skipped |

`run-tests.log` is the verbatim capture of that 2026-09-01 run. It is
byte-identical to the 2026-08-31 migration capture it replaces except for the
wall-clock line (`1.067s` → `1.148s`) — i.e. the earlier record was accurate and
reproduces. Nothing in this file is carried over on trust.

## What was run

The suite that ships with this version, from its new location
`Tooling/v1.0.0/tests/`, after the migration recorded in
[`CHANGE_LOG.md`](../../CHANGE_LOG.md#move-the-implementation-into-tooling-v1_6206c8de).
It is the whole suite: 10 test modules, offline, no network.

## Why the zero-skip line matters

Three tests in this suite are written to **skip loudly** rather than pass
quietly when their subject is missing (README, "What is proven, and how"):

- `test_conformance.TestAgainstClientMjs` — the envelope compared byte-for-byte
  against `/studio/packages/notify/src/client.mjs`, executed in `node`.
- `test_conformance.TestAgainstPollerSink` — the same envelope compared against
  `Packages/Poller`'s `notify_webhook` sink.
- `test_n8n_parity` — the receiver workflow's JavaScript executed against the
  same updates as the Python decoder.

All three **ran** in this recorded run (`... ok` in `run-tests.log`); none
skipped. That is the evidence that the migration did not silently disarm the
cross-implementation checks by breaking the paths they resolve — the
`Packages/Poller` path was in fact broken by the move and repaired, see the
change entry.

## Verbatim tail

```
----------------------------------------------------------------------
Ran 189 tests in 1.067s

OK
EXIT=0
```

## Track B conformance — the honest tick-list

Run against `Packages/Telegram` on 2026-09-01, against the five checks of
PROCESS.md §7 Track B. **This tool does not pass Track B.**

| Check | Verdict | Evidence |
|---|---|---|
| Canonical files | ✅ | All five of §3 exist at the tool root and are non-empty: `README.md`, `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md`, `CHANGE_LOG.md` |
| Reciprocity — `KNOWN_ISSUES.md` ↔ `CHANGE_LOG.md` | ✅ | 24 `TG-` entries carry `status: legacy` and are exempt (§9). The two non-legacy issue entries each cite a `CHANGE_LOG.md` id; both change entries cite an issue id back |
| Reciprocity — `IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` | ❌ | Neither document's entries are id-headed; they cross-reference by template name. Cannot be fixed without rewriting append-only entries. Logged as [`KNOWN_ISSUES.md#track-b-reciprocity-fails-for-the-implem_c160a132`](../../KNOWN_ISSUES.md#track-b-reciprocity-fails-for-the-implem_c160a132), status `escalated` |
| Code layout | ✅ | The tool's code sits under `Tooling/v1.0.0/` (`telegram/ bin/ templates/ n8n/ examples/ tests/ run-tests.sh`) |
| Test layout | ✅ | This directory — `Tests/v1.0.0/RESULTS.md` + `run-tests.log` — records the current version's run |
| Version agreement | ✅ | `README.md` ("Current version: `v1.0.0`"), the newest `Tooling/` directory (`v1.0.0`) and the newest `CHANGE_LOG.md` entry naming a version (`v1.0.0`) all agree |

**Overall: FAIL**, on the Reciprocity check. Five of the six rows above are
green; the check as PROCESS.md §7 writes it is one check, and it fails.

Recorded here rather than asserted anywhere else, per §5 invariant 5 — and
stated as a failure rather than softened, per invariant 6. The six ✅ in the
first `CHANGE_LOG.md` entry verify that entry's own `expected_result`, which
never included reciprocity; they are not a Track B verdict and the entry now
says so.

## Ids recomputed 2026-09-01

Every id the 2026-08-31 migration minted for this tool was recomputed with
`sha256sum` over the canonical identity string (trim → lowercase → collapse
whitespace runs to one space → strip trailing `. , ; : ! ?`).

| Id | Identity field | Reproduced? |
|---|---|---|
| `packages-telegram-failed-track-b-conform_9f851380` | issue `summary` | ✅ unchanged |
| `migrate-packages-telegram-to-the-tooling_78deb9ee` → `move-the-implementation-into-tooling-v1_6206c8de` | change `iteration` | ❌ **moved** — the old id was minted from `summary`; `process.yaml: definitions.change-id` settles change identity on `iteration` alone. Every citation was updated |
| `track-b-reciprocity-fails-for-the-implem_c160a132` | issue `summary` | new this change |
| `extend-the-process-md-9-legacy-rule-to-c_ad654f71` | change `iteration` | new this change |
