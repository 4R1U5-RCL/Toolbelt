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

<a name="ki-07"></a>
## KI-07 — An HTML error/login page at 200 is parsed as data

**Signature.** A proxy or WAF returns an HTML challenge page with HTTP 200; the
client tries to read it as the JSON API envelope.
**Prevented by.** `HttpResponse.json()` raises `HttpFatal` on a non-JSON body
rather than a bare `ValueError` the caller might mistake for retryable.
**Code.** `scrape/http.py` (`HttpResponse.json`).
**Test.** `tests/test_http.py::test_non_json_body_raises_fatal_on_parse`

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

---

## Adding an entry

Hit a new failure? Append a row to the index table and a `## KI-NN` section in the
same shape (Signature / Cause / Prevented by / Still your job / **Code.** /
**Test.**), give it an `<a name="ki-nn"></a>` anchor, and carry the `KI-NN` id in a
comment on the line that guards it — so `grep -rn KI-NN scrape/` finds the guard.
An entry with no code reference is a warning; an entry with one is a guard.
