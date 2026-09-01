# Implementation guide — configuring a scrape and plugging in a backend

Most of the time you never touch code: you choose a few options, on the command
line or in a JSON config, and let the pipeline (fetch → translate → chunk →
render) do the rest. The questions you answer:

1. **What do you want back** — clean markdown, structured JSON, or plain text? (`--format`)
2. **How big can it be** — what's your model's context window? (`--max-chars`, `--chunk`, `--max-tokens`)
3. **One URL or many** — a single page, or a list that must survive a bad entry? (`url` vs `batch`)
4. **Which credential** — the default `FIRECRAWL_API_KEY`, or a differently-named var? (`--api-key-env`)
5. **A different backend** — Firecrawl, or something you register yourself? (`--backend`)

## Anatomy of a config

Flags override the file, so a config carries your defaults and the command line
carries the exceptions.

```jsonc
{
  "backend": "firecrawl",          // which registered backend (default firecrawl)
  "base_url": "https://api.firecrawl.dev/v1",
  "api_key_env": "FIRECRAWL_API_KEY", // env var the key is read from (never the key itself)
  "formats": ["markdown"],         // Firecrawl formats to request; markdown is always kept

  "clean": true,                   // normalize the markdown (KI-08); false = raw
  "max_chars": 40000,              // hard cap on output size (default & cap 40000; KI-03)
  "chunk": false,                  // split into token-bounded pieces
  "max_tokens": 1500,              // chunk size, in ~tokens (KI-06)
  "overlap": 0,                    // ~tokens of tail shared between chunks
  "out_format": "markdown",        // markdown | json | text

  "timeout": 60,                   // per-request seconds (Firecrawl gets the long window)
  "retries": 3,                    // transient-error retries (KI-05)
  "allow_insecure": false          // permit http:// (off by default)
}
```

## Worked example: one docs page, ready for a model

```bash
export FIRECRAWL_API_KEY=fc-...
./bin/scrape url https://docs.example.com/guide --format markdown -o guide.md
```

You get `guide.md` with a small YAML frontmatter (`url`, `title`, `source_status`,
`chars`, `truncated`) followed by normalized markdown — drop it straight into a
prompt, and the frontmatter tells the model (and you) where it came from and
whether it was cut.

## Recipe: batch a list of URLs

One URL per line; blank lines and `#` comments are ignored. The batch survives a
bad page (KI-01).

```bash
./bin/scrape batch --input urls.txt --format json -o pages.json
# or from stdin:
cat urls.txt | ./bin/scrape batch --format markdown > pages.md
```

Two things worth copying: `--format json` gives you one object per URL with an
`ok` flag and an `error` string for the failures (nothing is silently dropped),
and the process exits `2` only if *every* URL failed — a partial success is still
a success.

## Recipe: chunking for a context window

```bash
./bin/scrape url https://long.example.com/whitepaper \
    --chunk --max-tokens 1000 --overlap 100 --format json -o chunks.json
```

`chunks.json` is a list of `{index, tokens, text}` you can feed one-per-request.
Sizes are the ~4-char estimate (KI-06) — target ~80% of your model's real limit.

## Adding a backend

The engine only knows a backend is "a thing with `.scrape(url) -> data`", where
`data` is a dict shaped like Firecrawl's (`{"markdown", "metadata", "links"}`). To
add one — a raw HTTP + html-to-markdown path, a cache, a different vendor —
implement that method and register the class:

```python
# scrape/client.py
class MyBackend:
    name = "mine"
    def __init__(self, api_key, base_url=..., formats=None, http=None, **_):
        ...
    def scrape(self, url):
        # return {"markdown": "...", "metadata": {"title": ..., "statusCode": ...}, "links": [...]}
        ...

BUILTIN_BACKENDS["mine"] = MyBackend
```

Then `--backend mine`. The contract: take an injected `http` client (so it stays
offline-testable), never log the key (KI-04), and raise the package's
`FatalFetchError` / `TransientFetchError` / `EmptyContentError` so the engine's
retry and batch policies apply unchanged.

## Before you scrape

- [ ] `FIRECRAWL_API_KEY` (or your `--api-key-env`) is exported, not committed.
- [ ] `--max-chars` / `--max-tokens` match the model you'll feed.
- [ ] For a batch, you've decided `--on-error continue` (default) vs `stop`.
- [ ] For chrome-heavy sites, you've considered requesting `onlyMainContent` upstream (KI-08).
- [ ] `./run-tests.sh` is green.

---

## Template index (appended 2026-08-31, v1.0.0)

Reciprocal citations for [`TEMPLATES.md`](TEMPLATES.md), added when this tool was
brought into PROCESS.md §3/§4 conformance. The implementations above predate
`TEMPLATES.md`; this section supplies the link each of them owes its template
rather than rewriting them (IMPLEMENTATIONS.md is append-only, PROCESS.md §5.2).

| Implementation above | Template |
|---|---|
| "Worked example: one docs page, ready for a model" | [TEMPLATES.md#tpl-01](TEMPLATES.md#tpl-01) — single URL → markdown (`examples/single-url.json`) |
| "Recipe: batch a list of URLs" | [TEMPLATES.md#tpl-02](TEMPLATES.md#tpl-02) — batch → JSON (`examples/batch-json.json`) and [TEMPLATES.md#tpl-04](TEMPLATES.md#tpl-04) — URL-list file (`examples/urls.txt`) |
| "Recipe: chunking for a context window" | [TEMPLATES.md#tpl-03](TEMPLATES.md#tpl-03) — chunked config (`examples/llm-chunks.json`) |
| "Adding a backend" | [TEMPLATES.md#tpl-05](TEMPLATES.md#tpl-05) — new backend class form |
| "Anatomy of a config" | no dedicated template file — it is the annotated superset of TPL-01/02/03, not a shipped form |

Note on paths: every relative path in the sections above (`./bin/scrape`,
`examples/`, `scrape/`, `tests/`, `./run-tests.sh`) is now relative to
`Tooling/v1.0.0/`, not to the tool root. See
[`CHANGE_LOG.md`](CHANGE_LOG.md) → `migrate-scrape-to-the-tooling-tests-layo_70b30a3b`.
