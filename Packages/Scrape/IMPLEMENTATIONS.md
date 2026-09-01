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

**status.** `legacy` — predates v1.0.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

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

**status.** `legacy` — predates v1.0.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

```bash
export FIRECRAWL_API_KEY=fc-...
./bin/scrape url https://docs.example.com/guide --format markdown -o guide.md
```

You get `guide.md` with a small YAML frontmatter (`url`, `title`, `source_status`,
`chars`, `truncated`) followed by normalized markdown — drop it straight into a
prompt, and the frontmatter tells the model (and you) where it came from and
whether it was cut.

## Recipe: batch a list of URLs

**status.** `legacy` — predates v1.0.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

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

**status.** `legacy` — predates v1.0.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

```bash
./bin/scrape url https://long.example.com/whitepaper \
    --chunk --max-tokens 1000 --overlap 100 --format json -o chunks.json
```

`chunks.json` is a list of `{index, tokens, text}` you can feed one-per-request.
Sizes are the ~4-char estimate (KI-06) — target ~80% of your model's real limit.

## Adding a backend

**status.** `legacy` — predates v1.0.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

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

**status.** `legacy` — predates v1.0.0, this tool's first conformant version;
exempt from the §7 Track B reciprocity check (PROCESS.md §9). This field is the
only edit made to the section.

- [ ] `FIRECRAWL_API_KEY` (or your `--api-key-env`) is exported, not committed.
- [ ] `--max-chars` / `--max-tokens` match the model you'll feed.
- [ ] For a batch, you've decided `--on-error continue` (default) vs `stop`.
- [ ] For chrome-heavy sites, you've considered requesting `onlyMainContent` upstream (KI-08).
- [ ] `./run-tests.sh` is green.

---

# Conformant implementation entries (v1.0.0)

The six sections above predate `v1.0.0`, this tool's first conformant version.
They are prose with titles, not `## <id>` entries, and `IMPLEMENTATIONS.md` is
append-only (PROCESS.md §5.2) — the one edit PROCESS.md §9 permits to a
pre-existing entry is adding `status: legacy`, which is what each of them
carries. Their content is not restated here.

The entries below are the conformant form. Each is a `## <id>` heading, names the
use case, cites its `TEMPLATES.md` id, and is cited back by that template — the
reciprocity PROCESS.md §7 Track B requires, running in both directions and
resolvable by grep. Each also points at the legacy section that holds the long
prose. They carry no `status` field: `process.yaml: definitions.issue-status` is
the vocabulary for *issue* entries, and asserting one of its values on an
implementation entry would be a category error. All four were appended at
`v1.0.0` on branch `smoke/fix-packages-scrape` and are not merged.

Two of the legacy sections get no entry here, and that is a real gap rather than
a tidy one: `Anatomy of a config` is an annotated superset of TPL-01/02/03 and
ships as no single form, and `Before you scrape` is a pre-flight checklist, not a
use case. Neither has a template to cite. They stay `legacy` and exempt.

Every relative path below and in the sections above (`./bin/scrape`, `examples/`,
`scrape/`, `tests/`, `./run-tests.sh`) is relative to `Tooling/v1.0.0/`, not to
the tool root — see
[`CHANGE_LOG.md#a-layout-and-documents-migration-only-no_e4cf77a9`](CHANGE_LOG.md#a-layout-and-documents-migration-only-no_e4cf77a9).

<a name="IMP-01"></a>
## IMP-01

**One docs page, ready for a model.** Scrape a single URL and write clean
markdown with provenance frontmatter, sized for a prompt.

```bash
export FIRECRAWL_API_KEY=fc-...
./bin/scrape url https://docs.example.com/guide -c examples/single-url.json -o guide.md
```

- **Template.** [`TEMPLATES.md#TPL-01`](TEMPLATES.md#TPL-01) — single URL → markdown (`examples/single-url.json`).
- **Prose.** "Worked example: one docs page, ready for a model" above (legacy).

<a name="IMP-02"></a>
## IMP-02

**A list of URLs that survives a bad page.** One URL per line, blank lines and
`#` comments ignored; a failed page is recorded, not fatal (KI-01). The process
exits `2` only if every URL failed.

```bash
./bin/scrape batch --input examples/urls.txt -c examples/batch-json.json -o pages.json
cat examples/urls.txt | ./bin/scrape batch --format markdown > pages.md
```

- **Templates.** [`TEMPLATES.md#TPL-02`](TEMPLATES.md#TPL-02) — batch → JSON (`examples/batch-json.json`), and [`TEMPLATES.md#TPL-04`](TEMPLATES.md#TPL-04) — the URL-list input file (`examples/urls.txt`).
- **Prose.** "Recipe: batch a list of URLs" above (legacy).

<a name="IMP-03"></a>
## IMP-03

**Chunking for a context window.** Split one page into token-bounded pieces you
can feed one per request. Sizes are the ~4-chars-per-token estimate (KI-06) —
target ~80% of the model's real limit.

```bash
./bin/scrape url https://long.example.com/whitepaper -c examples/llm-chunks.json -o chunks.json
```

- **Template.** [`TEMPLATES.md#TPL-03`](TEMPLATES.md#TPL-03) — chunked config (`examples/llm-chunks.json`).
- **Prose.** "Recipe: chunking for a context window" above (legacy).

<a name="IMP-04"></a>
## IMP-04

**A backend that is not Firecrawl.** Implement `scrape(url) -> data` returning a
Firecrawl-shaped dict, register the class in `BUILTIN_BACKENDS`, and select it
with `--backend`. Take the injected `http` client so it stays offline-testable,
never log the key (KI-04), and raise the package's error types so the engine's
retry and batch policies apply unchanged.

- **Template.** [`TEMPLATES.md#TPL-05`](TEMPLATES.md#TPL-05) — the new-backend class form.
- **Prose.** "Adding a backend" above (legacy).
