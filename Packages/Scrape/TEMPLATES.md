# Templates — production application forms for `scrape`

Current version: **v1.0.0**.

**There is no `templates/` directory in this tool.** The production application
forms that ship with it are the JSON config files and the URL-list file under
`Tooling/v1.0.0/examples/`, plus the invocation forms documented in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md). Everything below is transcribed from
those files as they actually exist in the repository; nothing here is invented.

`scrape` takes no code-level scaffolding template (no cookiecutter, no generator).
A "template" for this tool is a config + command pair you copy and edit.

Every entry here is a `## <id>` heading — the bare id and nothing else on the
line, per `process.yaml: definitions.entry` — and every one cites the
`IMPLEMENTATIONS.md` id that uses it, and is cited back by it. That is the
`IMPLEMENTATIONS.md` ↔ `TEMPLATES.md` half of the PROCESS.md §7 Track B
reciprocity check, and it holds for all five with no exemption. The trailing
`Adding a template` section is author guidance, not an entry: it records no
template and has no id.

| ID | Template | Source file | Implementation (cites this template back) |
|---|---|---|---|
| [TPL-01](#TPL-01) | Single URL → markdown | `Tooling/v1.0.0/examples/single-url.json` | [IMPLEMENTATIONS.md#IMP-01](IMPLEMENTATIONS.md#IMP-01) |
| [TPL-02](#TPL-02) | Batch of URLs → JSON | `Tooling/v1.0.0/examples/batch-json.json` | [IMPLEMENTATIONS.md#IMP-02](IMPLEMENTATIONS.md#IMP-02) |
| [TPL-03](#TPL-03) | Chunked for a context window | `Tooling/v1.0.0/examples/llm-chunks.json` | [IMPLEMENTATIONS.md#IMP-03](IMPLEMENTATIONS.md#IMP-03) |
| [TPL-04](#TPL-04) | URL-list input file | `Tooling/v1.0.0/examples/urls.txt` | [IMPLEMENTATIONS.md#IMP-02](IMPLEMENTATIONS.md#IMP-02) |
| [TPL-05](#TPL-05) | New backend class | none — the form lives in `IMPLEMENTATIONS.md#IMP-04` | [IMPLEMENTATIONS.md#IMP-04](IMPLEMENTATIONS.md#IMP-04) |

---

<a name="TPL-01"></a>
## TPL-01

**Single URL → markdown.**

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

Implementation: [`IMPLEMENTATIONS.md#IMP-01`](IMPLEMENTATIONS.md#IMP-01), which cites this template back.

---

<a name="TPL-02"></a>
## TPL-02

**Batch of URLs → JSON.**

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

Implementation: [`IMPLEMENTATIONS.md#IMP-02`](IMPLEMENTATIONS.md#IMP-02), which cites this template back.

---

<a name="TPL-03"></a>
## TPL-03

**Chunked for a context window.**

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

Implementation: [`IMPLEMENTATIONS.md#IMP-03`](IMPLEMENTATIONS.md#IMP-03), which cites this template back.

---

<a name="TPL-04"></a>
## TPL-04

**URL-list input file.**

`Tooling/v1.0.0/examples/urls.txt`, verbatim:

```
# one URL per line; blank lines and #-comments are ignored
https://example.com
https://example.org
```

Fed to `batch` with `--input urls.txt`, or on stdin with `-i -`.

Implementation: [`IMPLEMENTATIONS.md#IMP-02`](IMPLEMENTATIONS.md#IMP-02), which cites this template back.

---

<a name="TPL-05"></a>
## TPL-05

**New backend class.**

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

Implementation: [`IMPLEMENTATIONS.md#IMP-04`](IMPLEMENTATIONS.md#IMP-04), which cites this template back.

---

# Adding a template

Add the config or form under `Tooling/v<version>/examples/`, add a row to the
index table and a `## TPL-NN` section here — the heading is the bare id, nothing
else on the line — and cite the `IMPLEMENTATIONS.md` id that uses it. The
citation must run both ways: add the matching `IMP-NN` entry there citing this
one (PROCESS.md §3, §7 Track B).
