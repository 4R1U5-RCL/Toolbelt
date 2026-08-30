# scrape — web pages into LLM-ready text

Point it at a URL and get back clean, bounded, LLM-ready markdown — the page
fetched through Firecrawl, its markdown normalized, hard-capped to a
context-window-safe size, and (on request) split into token-bounded chunks with
a little provenance frontmatter on top. One URL or a whole list; markdown, JSON,
or plain text.

Zero dependencies: Python 3.9+ standard library only. No pip, no Node, no paths
into other repos. The same tree runs in a container, on a VPS, or under cron on a
laptop. The one network boundary is injected, so the whole pipeline is unit-tested
offline against fake Firecrawl responses.

- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** — the ways web scrapes actually break, each with the guard that now prevents it.
- **[IMPLEMENTATIONS.md](IMPLEMENTATIONS.md)** — how to configure a scrape, chunk for a model, and plug in a new backend.

## Why this exists

Firecrawl already returns markdown, so the hard part isn't fetching — it's the
handling around it that everyone re-derives: a page that 200s with an empty body
isn't a success; one slow URL shouldn't abort a batch of forty; a giant page
shouldn't silently blow a context window; a fatal 401 shouldn't be retried four
times; and the API key must never touch a log line. This package is that handling,
written once, with a test behind every guard.

## Quickstart

```bash
cd Packages/Scrape
./run-tests.sh                                  # 59 tests, offline, no key needed

export FIRECRAWL_API_KEY=fc-...                 # the one credential

./bin/scrape url https://example.com                        # markdown to stdout
./bin/scrape url https://example.com --format json -o out.json
./bin/scrape url https://example.com --chunk --max-tokens 800 --format json
printf 'https://a.com\nhttps://b.com\n' | ./bin/scrape batch --format json
./bin/scrape version
```

Minimum viable config (everything is optional — flags override the file):

```json
{ "out_format": "markdown", "clean": true, "max_chars": 40000 }
```

## How it works

```
url ─▶ FirecrawlClient.scrape ─▶ raw { markdown, metadata, links }
                                          │
                                          ▼
                     transform:  clean · truncate  ─▶  Document
                                          │
                              (--chunk)  chunk  ─▶  [Chunk, …]
                                          │
                                          ▼
                     render:  markdown+frontmatter │ json │ text
```

Each scrape is one fetch, one translation, and one render; a batch is that same
pipeline run per URL, independently, so one failure is recorded rather than fatal.

### The guarantees

| Property | How |
|---|---|
| Never a blank "success" | a 2xx with no `data.markdown` raises `EmptyContentError`, not an empty doc (KI-02) |
| One bad page can't kill a batch | `scrape_many` scrapes each URL independently, continue-on-error (KI-01) |
| Bounded output | hard char cap (default & cap 40000) with a `truncated` flag, plus optional token chunking (KI-03) |
| The key never leaks | the key lives only in the `Authorization` header, resolved by env-var *name* (KI-04) |
| Fatal errors aren't retried | 401/403/404/bad-URL are fatal; only 429/5xx/timeout retry with backoff honoring `Retry-After` (KI-05) |
| Offline-testable | the single HTTP boundary is injected — 59 tests, no network, no secrets |

## Commands

| Command | Does | Exit codes |
|---|---|---|
| `scrape url <URL>` | scrape one URL → stdout or `--out FILE` | `0` ok · `2` fatal |
| `scrape batch [-i FILE]` | scrape many (one URL per line, `#` comments ok; `-i -`/stdin) | `0` if ≥1 ok · `2` if all failed or no URLs |
| `scrape version` | print the version | `0` |

## Layout

```
Packages/Scrape/
├── bin/scrape              # no-install shim -> scrape.cli:main
├── scrape/
│   ├── cli.py              # argparse; url / batch / version
│   ├── config.py           # Config dataclass, load_config, resolve_api_key (honest missing-key)
│   ├── client.py           # FirecrawlClient (the backend) + build_client registry
│   ├── http.py             # injectable stdlib HTTP client (retry/backoff, transient vs fatal)
│   ├── transform.py        # raw payload -> Document: clean · truncate · map fields
│   ├── chunk.py            # token-bounded markdown chunker
│   ├── render.py           # Document -> markdown(+frontmatter) / json / text
│   ├── engine.py           # scrape_url · scrape_many (independent batch)
│   ├── model.py            # Document · Chunk value objects
│   └── errors.py           # ScrapeError taxonomy (transient vs fatal)
├── examples/               # one JSON config per scenario
├── tests/                  # stdlib unittest, offline, injected fakes
├── run-tests.sh
├── README.md · KNOWN_ISSUES.md · IMPLEMENTATIONS.md
```

## Testing

```bash
./run-tests.sh          # or: python3 -m unittest discover -s tests -t tests
```

Every test is offline and deterministic: the HTTP transport is faked at the
`urlopen` seam (with injected clock and RNG so backoff windows are exact), and the
backend is faked above that, so the client, translation, chunking, render, engine,
and CLI layers are each exercised without a network or a key. Every `KI-` guard in
`KNOWN_ISSUES.md` names the test that holds it.

## Adding to the package

- **A new output shape** → extend `render.py` (`render_document` / `render_chunks`) and the `--format` choices.
- **A new scrape backend** (not Firecrawl) → add a class with a `scrape(url) -> data` method, register it in `BUILTIN_BACKENDS`, and select it with `--backend`. The engine never learns which backend it holds. See IMPLEMENTATIONS.md.
- **A new failure you hit** → add a `KI-` entry with a `**Code.**`/`**Test.**` back-reference, and write the guard + its test. An entry without a code reference is a warning; one with it is a guard.
