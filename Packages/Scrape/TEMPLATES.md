# Templates — production application forms for `scrape`

Current version: **v1.0.0**.

**There is no `templates/` directory in this tool.** The production application
forms that ship with it are the JSON config files and the URL-list file under
`Tooling/v1.0.0/examples/`, plus the invocation forms documented in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md). Everything below is transcribed from
those files as they actually exist in the repository; nothing here is invented.

`scrape` takes no code-level scaffolding template (no cookiecutter, no generator).
A "template" for this tool is a config + command pair you copy and edit.

| ID | Template | Source file | Used by |
|---|---|---|---|
| [TPL-01](#tpl-01) | Single URL → markdown | `Tooling/v1.0.0/examples/single-url.json` | [IMPLEMENTATIONS.md → "Worked example: one docs page, ready for a model"](IMPLEMENTATIONS.md) |
| [TPL-02](#tpl-02) | Batch of URLs → JSON | `Tooling/v1.0.0/examples/batch-json.json` | [IMPLEMENTATIONS.md → "Recipe: batch a list of URLs"](IMPLEMENTATIONS.md) |
| [TPL-03](#tpl-03) | Chunked for a context window | `Tooling/v1.0.0/examples/llm-chunks.json` | [IMPLEMENTATIONS.md → "Recipe: chunking for a context window"](IMPLEMENTATIONS.md) |
| [TPL-04](#tpl-04) | URL-list input file | `Tooling/v1.0.0/examples/urls.txt` | [IMPLEMENTATIONS.md → "Recipe: batch a list of URLs"](IMPLEMENTATIONS.md) |
| [TPL-05](#tpl-05) | New backend class | `IMPLEMENTATIONS.md` → "Adding a backend" (no example file) | [IMPLEMENTATIONS.md → "Adding a backend"](IMPLEMENTATIONS.md) |

---

<a name="tpl-01"></a>
## TPL-01 — Single URL → markdown

`Tooling/v1.0.0/examples/single-url.json`, verbatim:

```json
{
  "backend": "firecrawl",
  "formats": ["markdown"],
  "clean": true,
  "out_format": "markdown",
  "max_chars": 40000
}
```

Applied as:

```bash
export FIRECRAWL_API_KEY=fc-...
./bin/scrape url https://docs.example.com/guide -c examples/single-url.json -o guide.md
```

Implementation: IMPLEMENTATIONS.md, "Worked example: one docs page, ready for a model".

---

<a name="tpl-02"></a>
## TPL-02 — Batch of URLs → JSON

`Tooling/v1.0.0/examples/batch-json.json`, verbatim:

```json
{
  "out_format": "json",
  "clean": true,
  "timeout": 90,
  "retries": 3
}
```

Applied as:

```bash
./bin/scrape batch --input examples/urls.txt -c examples/batch-json.json -o pages.json
```

One object per URL carrying an `ok` flag and an `error` string; the process exits
`2` only if every URL failed (KNOWN_ISSUES.md KI-01).

Implementation: IMPLEMENTATIONS.md, "Recipe: batch a list of URLs".

---

<a name="tpl-03"></a>
## TPL-03 — Chunked for a context window

`Tooling/v1.0.0/examples/llm-chunks.json`, verbatim:

```json
{
  "clean": true,
  "chunk": true,
  "max_tokens": 1200,
  "overlap": 100,
  "out_format": "json"
}
```

Applied as:

```bash
./bin/scrape url https://long.example.com/whitepaper -c examples/llm-chunks.json -o chunks.json
```

Produces a list of `{index, tokens, text}`. Token counts are the ~4-chars-per-token
estimate — leave headroom (KNOWN_ISSUES.md KI-06).

Implementation: IMPLEMENTATIONS.md, "Recipe: chunking for a context window".

---

<a name="tpl-04"></a>
## TPL-04 — URL-list input file

`Tooling/v1.0.0/examples/urls.txt`, verbatim:

```
# one URL per line; blank lines and #-comments are ignored
https://example.com
https://example.org
```

Fed to `batch` with `--input urls.txt`, or on stdin with `-i -`.

Implementation: IMPLEMENTATIONS.md, "Recipe: batch a list of URLs".

---

<a name="tpl-05"></a>
## TPL-05 — New backend class

No file ships this one; the form lives in IMPLEMENTATIONS.md, "Adding a backend",
and is reproduced here as the template because it is the shape every new backend
must take:

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

Selected with `--backend mine`. The contract: accept the injected `http` client so
it stays offline-testable, never log the key (KI-04), and raise the package's
`FatalFetchError` / `TransientFetchError` / `EmptyContentError` so the engine's
retry and batch policies apply unchanged.

Implementation: IMPLEMENTATIONS.md, "Adding a backend".

---

## Adding a template

Add the config or form under `Tooling/v<version>/examples/`, add a row to the
index table and a `## TPL-NN` section here, and cite the IMPLEMENTATIONS.md entry
that uses it — the citation must run both ways (PROCESS.md §3).
