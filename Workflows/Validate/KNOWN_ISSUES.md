# KNOWN ISSUES — Workflows/Validate

Every issue found with this tool. Each entry cites the iteration that addresses it in
[`CHANGE_LOG.md`](CHANGE_LOG.md) (PROCESS.md §3 reciprocity).

**Append-only** (PROCESS.md §5.1). Entries are never edited or removed; a fix appends, and a
repeat occurrence is added as an occurrence row on the existing entry rather than a new entry.

Ids are `<description>_<hash8>` per `process.yaml` §5 — the slugified summary, plus the first 8
hex characters of the sha256 of the canonicalised summary.

---

## `workflows-validate-failed-track-b-confor_ccdc053f`

| Field | Value |
|---|---|
| **id** | `workflows-validate-failed-track-b-confor_ccdc053f` |
| **summary** | Workflows/Validate failed Track B conformance: four canonical documents missing, code not under Tooling/, no recorded test results under Tests/, README named no version |
| **status** | open — the iteration is applied in the working tree on the migration branch; the entry closes as `resolved` on merge, per PROCESS.md §6 step 7 |
| **resolved_by** | [`CHANGE_LOG.md#migrate-workflows-validate-to-the-proces_c65a856c`](CHANGE_LOG.md#migrate-workflows-validate-to-the-proces_c65a856c) at version `v1.0.0` |
| **occurrences** | 1 — detected 2026-08-31 by the Track B conformance check run during this migration (PROCESS.md §7 Track B, §9 "on next touch") |

**outcome (X) — what the failure resulted in.** The tool did not satisfy PROCESS.md §7 Track B and
therefore could not release a version. Concretely, as found on 2026-08-31:

- **Canonical files** — check FAILED. Only `README.md` of the five §3 documents existed. Missing:
  `IMPLEMENTATIONS.md`, `TEMPLATES.md`, `KNOWN_ISSUES.md`, `CHANGE_LOG.md` (this file was one of
  the four absent).
- **Reciprocity** — check vacuous, and unverifiable. With no `IMPLEMENTATIONS.md`/`TEMPLATES.md`
  and no `KNOWN_ISSUES.md`/`CHANGE_LOG.md`, there were no entries to cross-cite in either
  direction.
- **Code layout** — check FAILED. The code (`bin/`, `config/`, `docs/`, `lib/`, `tests/`,
  `.gitignore`) sat directly at the tool root. No `Tooling/` directory existed, so there was no
  immutable released-version directory and therefore **no in-repo rollback point** (PROCESS.md §4,
  §5 safeguard 1).
- **Test layout** — check FAILED. No `Tests/` directory existed. `tests/selftest.py` was present
  and passing, but its *results* had never been recorded anywhere a human could confirm them; the
  only claim of a result was the prose "28/28" in `README.md`.
- **Version agreement** — check FAILED. `README.md` named **no version at all** (verified: a
  case-insensitive grep for `version` and for a `vN.N` pattern over `README.md` returned nothing),
  there was no `Tooling/` directory to name one, and there was no `CHANGE_LOG.md` to hold a newest
  entry. Nothing in the tool identified which version its code was.

The consequences are the ones PROCESS.md §1 exists to prevent: no rollback point, no recorded
evidence, and staleness invisible — a reader could not tell what version the code was, whether its
tests had ever actually been run, or what forms the tool is used in.

**cause (Y) — the mechanism.** The tool predates the layout PROCESS.md §3/§4 mandates. It was
authored in the flat one-directory-per-tool shape carried over from `operand-packages` v1 and was
never migrated; PROCESS.md §9 records it as a known backlog row (`Workflows/Validate`: README ✅,
all other columns ❌) rather than a regression. Nothing about the tool's code caused this — the
failure is purely one of repository layout and documentation, and no defect in
`lib/validate_core.py`, `bin/validate` or `tests/selftest.py` is implicated.

**iteration (Z) — planned to resolve it.** Bring the tool into §3/§4 conformance without changing
its behaviour: move the implementation to `Tooling/v1.0.0/` (v1.0.0 because this tool has never
been versioned — PROCESS.md §9, §10.6), run the existing self-test from its new location and record
the verbatim output under `Tests/v1.0.0/`, create the four missing canonical documents, and state
the current version in `README.md`. Recorded in
[`CHANGE_LOG.md#migrate-workflows-validate-to-the-proces_c65a856c`](CHANGE_LOG.md#migrate-workflows-validate-to-the-proces_c65a856c).

### Residual gaps left open by this iteration

Recorded rather than silently fixed, because closing either would be a code change and this
iteration deliberately changes no code:

1. **No `run-tests.sh`.** `process.yaml`'s `test_decision` branch tests "`./run-tests.sh` exits 0";
   this tool has no such script, so that CI gate has no entrypoint to call. The suite must be
   invoked directly as `python3 tests/selftest.py`. Adding the wrapper is a candidate for the next
   iteration.
2. **Reciprocity is satisfied by derivation, not by a `templates/` directory.** The tool has no
   `templates/` directory. `TEMPLATES.md` documents the invocation forms and panel config that
   actually exist in the repo and says so explicitly; nothing was invented to fill it (PROCESS.md
   §9 "empty-but-valid").
