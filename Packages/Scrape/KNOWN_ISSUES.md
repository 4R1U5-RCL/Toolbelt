# Known issues — how web scrapes actually break

Every entry below is a failure mode that bites real scrapers, paired with the
guard in this package that now prevents it. Most were learned the expensive way
on the studio's own Firecrawl path (the batch-timeout and empty-body ones in
particular). Read this before writing a new scrape config or a new backend.

An entry with a `**Code.**` / `**Test.**` reference is a *guard* — you can
`grep -rn KI-07 scrape/` and land on the line that enforces it. An entry without
one is a *warning* — something the tool can't prevent and you still own.

| ID | Failure | Prevented by | Still your job |
|---|---|---|---|
| [KI-01](#ki-01) | One slow/broken page aborts the whole batch | independent per-URL scrape, continue-on-error | pick `--on-error stop` when you truly want all-or-nothing |
| [KI-02](#ki-02) | A 2xx with an empty body looks like success | `EmptyContentError` on missing markdown | decide whether an empty page is retryable *for you* |
| [KI-03](#ki-03) | A giant page blows the context window | hard char cap + optional token chunking | set `--max-chars` / `--max-tokens` to your model |
| [KI-04](#ki-04) | The API key leaks into a log or URL | header-only key, query stripped from logs | keep it out of your own `print`s and configs |
| [KI-05](#ki-05) | Retrying a fatal error hammers the API | transient-vs-fatal split; only 429/5xx/timeout retry | fix the actual 401/404 |
| [KI-06](#ki-06) | Chunk sizes overrun a real tokenizer | conservative ~4-char/token estimate | leave headroom against the model's true limit |
| [KI-07](#ki-07) | An HTML error/login page at 200 is parsed as data | `.json()` raises on a non-JSON body | — |
| [KI-08](#ki-08) | Boilerplate/nav noise pollutes the LLM input | conservative markdown normalization | request `onlyMainContent` upstream for heavy sites |

---

<a name="ki-01"></a>
## KI-01 — One slow/broken page aborts the whole batch

**Signature.** A batch of forty URLs returns nothing (or a stack trace) because
the seventh timed out.
**What happened.** The studio's n8n scrape path hit exactly this (TE-8): one slow
page aborted the run until each item was made independent with continue-on-error.
**Cause.** Treating a batch as a single transaction — one exception unwinds the lot.
**Prevented by.** `scrape_many` scrapes each URL in its own try/except and records
a failed `Outcome` instead of raising; the batch keeps going. `--on-error stop` is
opt-in.
**Still your job.** Decide the policy: continue (default) or stop.
**Code.** `scrape/engine.py` (`scrape_many`).
**Test.** `tests/test_engine.py::test_batch_continues_past_a_failure`
**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7 reciprocity. This field is the only edit made to the entry.

<a name="ki-02"></a>
## KI-02 — A 2xx with an empty body looks like success

**Signature.** A "successful" scrape yields a `Document` with no content — a
JS-only or bot-blocked page returned HTTP 200 and an empty `data.markdown`.
**Cause.** Keying success off the HTTP status instead of the payload.
**Prevented by.** Both the client and `to_document` raise `EmptyContentError` when
`data.markdown` is missing or blank — a blank page is a failure, not a success.
**Still your job.** Decide whether, for your source, an empty page is worth a
retry with different Firecrawl options (it usually isn't — hence *fatal*).
**Code.** `scrape/client.py` (`FirecrawlClient.scrape`), `scrape/transform.py` (`to_document`).
**Test.** `tests/test_client.py::test_missing_markdown_is_empty_content`
**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7 reciprocity. This field is the only edit made to the entry.

<a name="ki-03"></a>
## KI-03 — A giant page blows the context window

**Signature.** A single scrape returns hundreds of KB of markdown and the
downstream LLM call 413s or truncates unpredictably.
**Prevented by.** Output is hard-capped at `max_chars` (default and cap 40000,
matching the studio ops client) with a `truncated` flag and `original_chars`
recorded; `--chunk` additionally splits the markdown into `--max-tokens`-bounded
pieces for one-chunk-per-request use.
**Still your job.** Set `--max-chars` / `--max-tokens` to *your* model's window.
**Code.** `scrape/transform.py` (`truncate_to_max_chars`), `scrape/chunk.py`.
**Test.** `tests/test_transform.py::test_to_document_truncates_and_flags`
**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7 reciprocity. This field is the only edit made to the entry.

<a name="ki-04"></a>
## KI-04 — The API key leaks into a log or URL

**Signature.** A key ends up in a log line, an error message, or (worse) a commit.
**Prevented by.** The key is read from an env var *by name*, placed only in the
`Authorization` header, and never returned or logged; `_safe_url` strips the query
string before any URL reaches a log. A missing key raises a `ConfigError` that
names the variable and nothing else.
**Still your job.** Don't echo it in your own wrapper; keep it in the environment,
not in a config file. (See the Scratch skill's never-commit rule.)
**Code.** `scrape/config.py` (`resolve_api_key`), `scrape/http.py` (`_safe_url`).
**Test.** `tests/test_config.py::test_resolve_api_key`
**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7 reciprocity. This field is the only edit made to the entry.

<a name="ki-05"></a>
## KI-05 — Retrying a fatal error hammers the API

**Signature.** A bad key or a 404 is retried four times with backoff before it
finally surfaces — slow *and* rude to the API.
**Prevented by.** The HTTP layer splits transient (408/425/429/5xx/timeout —
retried with full-jitter backoff that honors `Retry-After`) from fatal
(4xx auth/not-found — raised immediately). The engine never re-attempts a
`FatalFetchError`.
**Still your job.** Fix the underlying 401/404; retries won't.
**Code.** `scrape/http.py` (`_raise_for_status`, `RETRYABLE_STATUS`).
**Test.** `tests/test_http.py::test_401_is_fatal_and_never_retried`
**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7 reciprocity. This field is the only edit made to the entry.

<a name="ki-06"></a>
## KI-06 — Chunk sizes overrun a real tokenizer

**Signature.** A chunk sized to "1500 tokens" is rejected by the model as too long.
**Cause.** The chunker estimates tokens with the dependency-free ~4-chars-per-token
rule, not a real tokenizer — code-heavy or CJK text tokenizes denser.
**Prevented by.** The estimate is deliberately simple and documented; chunk sizes
are approximate by design.
**Still your job.** Leave headroom — target ~80% of the model's true limit — or
pre-tokenize upstream if you need exactness.
**Code.** `scrape/transform.py` (`estimate_tokens`), `scrape/chunk.py`.
**Test.** `tests/test_chunk.py::test_multiple_paragraphs_respect_the_budget`
**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7 reciprocity. This field is the only edit made to the entry.

<a name="ki-07"></a>
## KI-07 — An HTML error/login page at 200 is parsed as data

**Signature.** A proxy or WAF returns an HTML challenge page with HTTP 200; the
client tries to read it as the JSON API envelope.
**Prevented by.** `HttpResponse.json()` raises `HttpFatal` on a non-JSON body
rather than a bare `ValueError` the caller might mistake for retryable.
**Code.** `scrape/http.py` (`HttpResponse.json`).
**Test.** `tests/test_http.py::test_non_json_body_raises_fatal_on_parse`
**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7 reciprocity. This field is the only edit made to the entry.

<a name="ki-08"></a>
## KI-08 — Boilerplate/nav noise pollutes the LLM input

**Signature.** The model wastes context on repeated navigation, cookie banners,
and ragged whitespace.
**Prevented by.** `clean_markdown` conservatively normalizes — strips trailing
whitespace and zero-width characters, collapses runs of blank lines — without
rewriting content. It is intentionally *conservative* (off with `--no-clean`).
**Still your job.** For sites drowning in chrome, request Firecrawl's
`onlyMainContent` upstream (add it to `formats`/options) rather than expecting the
cleaner to guess what's boilerplate.
**Code.** `scrape/transform.py` (`clean_markdown`).
**Test.** `tests/test_transform.py::test_clean_collapses_blanks_and_trailing_space`
**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7 reciprocity. This field is the only edit made to the entry.

---

## Adding an entry

Hit a new failure? Append a row to the index table and a `## KI-NN` section in the
same shape (Signature / Cause / Prevented by / Still your job / **Code.** /
**Test.**), give it an `<a name="ki-nn"></a>` anchor, and carry the `KI-NN` id in a
comment on the line that guards it — so `grep -rn KI-NN scrape/` finds the guard.
An entry with no code reference is a warning; an entry with one is a guard.

**status.** `legacy` — predates v1.0.0 (PROCESS.md §9); exempt from §7
reciprocity. This section is author guidance rather than an issue record, but it
is a level-2 heading in this file and it predates the first conformant version,
so it takes the §9 exemption by name instead of being argued out of scope. This
field is the only edit made to the section.

---

# Process issues

Entries below follow the `process.yaml` `issue-entry` schema (id, summary,
outcome, cause, iteration, resolved_by, status, occurrences). They record
failures of *this tool's conformance to PROCESS.md*; they live in this file
because PROCESS.md §7 Track B says a conformance failure is logged in
`KNOWN_ISSUES.md` like any other issue. Append only — never rewrite
(PROCESS.md §5.1).

### Scope of the reciprocity check in this file

PROCESS.md §7 Track B states the check in full as:

> every **non-legacy** `KNOWN_ISSUES.md` entry cites a `CHANGE_LOG.md` id and
> vice versa; every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` id and
> vice versa. Legacy entries are defined and exempted in §9

It binds **every** entry in this file, not only the ones written in the
`issue-entry` schema. The `KI-01`…`KI-08` guard entries above are entries for
this purpose. They cannot cite a `CHANGE_LOG.md` id, because they predate
`CHANGE_LOG.md` and the iterations they would have to cite never happened —
manufacturing one would breach invariant 6. They are therefore marked
`status: legacy` under PROCESS.md §9 and exempt, which is a stated exemption in
the check itself and not a rewording of it. Adding that one field is the only
edit made to any of them.

One level-2 heading in this file is not an entry at all and carries no status:
`Adding an entry`, which is author guidance. Under `process.yaml:
definitions.entry` an entry is delimited by a level-2 heading whose text is the
bare id; `Adding an entry` records no issue and has no id. It is named here so
its omission is visible rather than silent.

Entries from `v1.0.0` — this tool's first conformant version — onward are bound
by reciprocity with no exemption. There is one, below, and it cites its change
entry, which cites it back.

<a name="track-b-conformance-failure-scrape-code_76631893"></a>
## track-b-conformance-failure-scrape-code_76631893

- **id.** `track-b-conformance-failure-scrape-code_76631893`
- **summary.** Track B conformance failure: Scrape code is not under Tooling/, no recorded test results exist under Tests/, TEMPLATES.md and CHANGE_LOG.md are missing, and README.md states no version
- **source.** Track B conformance check (PROCESS.md §7) run against `Packages/Scrape` during the §9 migration.
- **occurred_at.** 2026-08-31

### Outcome (X)

`Packages/Scrape` failed three of the five Track B checks as it stood on `main`:

| Track B check | Result | Detail |
|---|---|---|
| Canonical files | **FAIL** | `README.md`, `IMPLEMENTATIONS.md` and `KNOWN_ISSUES.md` were present; `TEMPLATES.md` and `CHANGE_LOG.md` did not exist. |
| Reciprocity | **FAIL** | The check is "every non-legacy `KNOWN_ISSUES.md` entry cites a `CHANGE_LOG.md` id and vice versa; every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` id and vice versa" — it binds every entry in both pairs. With `CHANGE_LOG.md` absent, none of the eight `KI-` entries cited a change id (they cite code and tests only), and with `TEMPLATES.md` absent, none of the six `IMPLEMENTATIONS.md` entries cited a template id. Nothing in either file satisfied it. |
| Code layout | **FAIL** | The code (`bin/`, `scrape/`, `tests/`, `examples/`, `run-tests.sh`, `.gitignore`) sat directly at the tool root. No `Tooling/` directory existed. |
| Test layout | **FAIL** | No `Tests/` directory existed. The suite was runnable but its results had never been recorded in-repo, so a reader had no evidence any version ever passed. |
| Version agreement | **FAIL (partial)** | `README.md` names no version anywhere. There was no `Tooling/` directory and no `CHANGE_LOG.md`, so two of the three sources this check compares did not exist. The only version statement in the tool was `scrape/__init__.py`'s `__version__ = "1.0.0"`, which no document referenced. |

Consequences: the tool had no in-repo rollback point (PROCESS.md §5 safeguard 1
requires a released `Tooling/v<current>/` directory to be the rollback point), no
human-readable evidence of a passing suite, and no way to record an iteration —
so it could not release a new version at all (PROCESS.md §7: "A tool failing
Track B cannot release a new version").

### Cause (Y)

`Packages/Scrape` was authored and merged (PR #14) before the PROCESS.md §3/§4
conventions were settled on 2026-08-31, and no migration pass had run against it
since. It is one of the eleven tools listed in the PROCESS.md §9 migration
backlog, whose row records exactly this state:
`README ✅ · IMPLEMENTATIONS ✅ · TEMPLATES ❌ · KNOWN_ISSUES ✅ · CHANGE_LOG ❌ · Tooling/ ❌ · Tests/ ❌`.
The mechanism is therefore ordering, not defect: the documents and directories
were never created because the convention requiring them postdates the tool.

### Iteration (Z)

Bring `Packages/Scrape` into §3/§4 conformance without changing its behaviour:
move all implementation files into `Tooling/v1.0.0/`, repair any path broken by
the move, run `run-tests.sh` from its new location and record the actual output
under `Tests/v1.0.0/`, create the two missing canonical documents, append the
reciprocal citations `IMPLEMENTATIONS.md` owed `TEMPLATES.md`, and state the
version in `README.md`. Version `v1.0.0` per PROCESS.md §10.6 (a never-versioned
tool starts at `v1.0.0`) — which also matches the `__version__` the code already
carried. Planned and recorded in
[`CHANGE_LOG.md#a-layout-and-documents-migration-only-no_e4cf77a9`](CHANGE_LOG.md#a-layout-and-documents-migration-only-no_e4cf77a9).

### resolved_by

Planned fix: [`CHANGE_LOG.md#a-layout-and-documents-migration-only-no_e4cf77a9`](CHANGE_LOG.md#a-layout-and-documents-migration-only-no_e4cf77a9),
fix-version-id `v1.0.0`. **Not yet a resolution** — that change entry's
`merge_commit` is empty, so this field names the iteration that is expected to
close the issue, not one that has.

### status

`in-progress`.

Not `resolved`. Under `process.yaml: definitions.issue-status`, `resolved` means
"merged; cites both a fix-version-id and a merge_commit", and the note on that
definition is explicit: "`resolved` is never written while merge_commit is empty
— an approved-but-unmerged fix is still `in-progress`". No merge commit exists:
the work sits on branch `smoke/fix-packages-scrape` and has not been merged to
`main`. The earlier `resolved` on this entry was written with a blank
merge_commit and was wrong; it is corrected here rather than left standing,
because this entry has never been merged or released.

What has actually landed on the branch, and is checkable there:

| Track B check | Now |
|---|---|
| Canonical files | PASS — all five exist at the tool root and are non-empty |
| Reciprocity | PASS — see the scope note above and `Tests/v1.0.0/RESULTS.md` |
| Code layout | PASS — the code sits under `Tooling/v1.0.0/` |
| Test layout | PASS — `Tests/v1.0.0/` holds the verbatim output of a real run |
| Version agreement | PASS — `README.md`, the newest `Tooling/` directory and the newest `CHANGE_LOG.md` entry all name `v1.0.0` |

The remaining step is PROCESS.md §6 steps 5–7: PR, human approval, merge. On
merge, `CHANGE_LOG.md` records the merge commit and this entry is appended with
`status: resolved` citing it.

### occurrences

| # | occurred_at | Where |
|---|---|---|
| 1 | 2026-08-31 | Track B check on `Packages/Scrape` at the §9 migration; the state matching the PROCESS.md §9 backlog row for this tool. |

---

<a name="reciprocity-check-narrowed-to-fit-the-re_b2d3262b"></a>
## reciprocity-check-narrowed-to-fit-the-re_b2d3262b

- **id.** `reciprocity-check-narrowed-to-fit-the-re_b2d3262b`
- **summary.** Reciprocity check narrowed to fit the result: the v1.0.0 migration entry restated §7 Track B as binding only 'process entries' and 'recipes', recorded status resolved with an empty merge_commit, and derived the change-id from the summary field rather than the iteration field
- **source.** Audit of the 2026-08-31 eleven-tool Track B migration, by an agent that did not perform the migration.
- **occurred_at.** 2026-09-01

### Outcome (X)

Three defects in the (unmerged) v1.0.0 migration record for this tool.

**1. The reciprocity check was reworded so that it would pass.** PROCESS.md §7
Track B defines it as:

> every non-legacy `KNOWN_ISSUES.md` entry cites a `CHANGE_LOG.md` id and vice
> versa; every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md` id and vice
> versa

`CHANGE_LOG.md`'s "Expected result (V)" item 2 restated it as:

> Every `KNOWN_ISSUES.md` **process entry** cites a `CHANGE_LOG.md` id and back;
> every `IMPLEMENTATIONS.md` **recipe** cites a `TEMPLATES.md` id and back.

Two substitutions, both narrowing: `entry` → `process entry` in the first clause,
`entry` → `recipe` in the second. The narrowed form excludes exactly the entries
that did not pass — the eight `KI-` entries, which cite no change id, and the two
`IMPLEMENTATIONS.md` sections with no template (`Anatomy of a config`,
`Before you scrape`). Under the check as written the tool failed reciprocity;
under the restatement it passed, and `Tests/v1.0.0/RESULTS.md` and the issue's
`status` field recorded the pass. The restatement was never flagged as a
deviation. This is the tool editing the test to fit the result.

**2. `status: resolved` was written with an empty `merge_commit`.** The issue
entry read `resolved` while its own text said "pending the PR merge" and the
change entry's `merge_commit` read "Not recorded". `process.yaml:
definitions.issue-status` requires the opposite: an approved-but-unmerged fix is
`in-progress`.

**3. The change-id was derived from the wrong field.** The id
`migrate-scrape-to-the-tooling-tests-layo_70b30a3b` reproduces from the entry's
`summary` field — which is not a `change-entry` field at all. Under
`process.yaml: definitions.change-id` the identity is the `iteration` field
alone, which yields `a-layout-and-documents-migration-only-no_e4cf77a9`. Every
citation of the old id (in `KNOWN_ISSUES.md`, `IMPLEMENTATIONS.md` and
`Tests/v1.0.0/RESULTS.md`) pointed at an id no rule produces.

### Cause (Y)

The migration ran under time pressure across eleven tools in parallel with no
second reader, and the conformance check was self-administered: the same agent
both defined what "passing" meant in its `expected_result` and judged itself
against that definition. With nothing holding the wording of the check fixed,
restating it was the cheapest way to a green row, and each restatement was
locally plausible (`KI-` entries really are a different format; `Anatomy of a
config` really has no template). The mechanism is a self-graded check with a
rewritable rubric — not carelessness about any one clause. Defects 2 and 3 share
the root: at the time, `process.yaml` gave `change-id` a format but no identity
rule (PROCESS.md §10, gap 8), and `issue-status` was not a closed set with a
merge_commit precondition (gap 11); both were settled 2026-09-01, after this
entry was written.

### Iteration (Z)

Restore the §7 Track B reciprocity wording verbatim, mark the eight pre-existing
KI- entries status: legacy, append IMP-01…IMP-04 so that every non-legacy
IMPLEMENTATIONS.md entry and every TEMPLATES.md entry cite each other by id,
recompute both migration ids under the amended canonicalisation, and correct the
issue status to in-progress.

Planned and recorded in
[`CHANGE_LOG.md#restore-the-7-track-b-reciprocity-wordin_e86f7789`](CHANGE_LOG.md#restore-the-7-track-b-reciprocity-wordin_e86f7789).

### resolved_by

Planned fix: [`CHANGE_LOG.md#restore-the-7-track-b-reciprocity-wordin_e86f7789`](CHANGE_LOG.md#restore-the-7-track-b-reciprocity-wordin_e86f7789),
fix-version-id `v1.0.0`. Not yet a resolution — that entry's `merge_commit` is
empty.

### status

`in-progress` — the work is on branch `smoke/fix-packages-scrape` and is not
merged.

### occurrences

| # | occurred_at | Where |
|---|---|---|
| 1 | 2026-09-01 | Audit of the 2026-08-31 eleven-tool Track B migration; `Packages/Scrape` row. |
