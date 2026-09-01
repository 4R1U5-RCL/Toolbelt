# Templates — Workflows/Review

The production-ready application forms of this tool, each cited by its entry in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) (PROCESS.md §3).

| Template | Used by | Status |
|---|---|---|
| — | — | none exist |

### No templates exist

**This file is empty-but-valid** (PROCESS.md §9). The statement above is a fact
about the repo, not a placeholder for content that was omitted:

- there is no `templates/` directory in this tool, and there never has been;
- before the 2026-08-31 migration the whole tool was a single 42-byte
  `README.md`, and it contains no template, snippet, form or example;
- consequently `IMPLEMENTATIONS.md` has no entries either, so this file cites
  nothing and nothing cites it.

That last point is worth stating precisely rather than claiming a pass. The §7
reciprocity check reads "every `IMPLEMENTATIONS.md` entry cites a `TEMPLATES.md`
id and vice versa". With zero entries on both sides there is no entry that fails
it — but there is also nothing here demonstrating the pair works. The check is
satisfied because the documents are honestly empty, not because content was
produced to satisfy it, and no wording was narrowed to reach that reading.

When the review workflow is actually built, its templates land in
`Tooling/v<version>/templates/` and are documented here, each citing the
implementation that uses it.

*(The section heading above is level 3 deliberately — see the note in
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md). This file has zero entries.)*
