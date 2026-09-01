# Test results — Skills/Memory v1.0.0

## What was run

`Tooling/v1.0.0/tests/verify.sh` — the package's only test entrypoint. There is
**no `run-tests.sh`** in this tool; `verify.sh` is what the README names as the
committed self-check. It is an offline smoke test: it sandboxes a temp dir,
installs the two shipped templates, cuts a fixture memory directory from them
with `tests/mem_tool.py build`, then lints the result (`mem_tool.py lint`) for
frontmatter validity, the index-is-recall invariant, wikilink resolution, and a
deliberate drift demo (un-indexed entry caught, then fixed).

Command, run from the new version directory after the migration:

```
cd /studio/scratch/tb/Skills/Memory/Tooling/v1.0.0 && bash tests/verify.sh
```

## When

2026-08-31T15:19Z (UTC), on the host running this migration. `python3` and
`bash` only; no network, no credentials.

## Outcome — verbatim

```
== memory smoke: 18 passed, 0 failed ==
exit=0
```

Full captured output: [`run-tests.log`](run-tests.log).

## Notes

- The suite was run **before** the move (from the old `tests/` at the tool root)
  and gave the same result — 18 passed, 0 failed, exit 0. It was then re-run
  from `Tooling/v1.0.0/` and from the tool root as
  `bash Tooling/v1.0.0/tests/verify.sh`; all three runs were identical.
- **No path repair was needed.** `verify.sh` resolves its own location from
  `BASH_SOURCE` (`HERE=…/tests`, `PKG="$HERE/.."`) and reads the templates as
  `$PKG/templates/`, so moving `tests/` and `templates/` together into
  `Tooling/v1.0.0/` preserved the relationship. `mem_tool.py` does no
  `sys.path` manipulation and takes all paths as arguments.
- This is a conformance/layout migration, so the suite corroborates only that
  the code still runs where it now lives. It does not exercise any logged
  functional error, because none was logged — the issue recorded in
  `KNOWN_ISSUES.md` for this change is a Track B conformance failure.
