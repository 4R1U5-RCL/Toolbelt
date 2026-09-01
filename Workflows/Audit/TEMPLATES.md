# Templates — Workflows/Audit

The production-ready application forms of this tool, each cited from
[`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) (PROCESS.md §3).

**Status: empty-but-valid. No templates exist for this tool.**

---

## What was actually looked for

`Workflows/Audit` has **no `templates/` directory**, and no file anywhere in the
tool that functions as a template — no prompt file, no config skeleton, no
document skeleton, no example. The complete file listing of the tool directory
before this migration was one line:

```
$ find . -type f | sort
./README.md
```

That capture, with its timestamp and exit code, is preserved verbatim in
[`Tests/v1.0.0/run-tests.log`](Tests/v1.0.0/run-tests.log).

## Why nothing is invented here

A template in this repo is a *proven, reusable* form — PROCESS.md §1 — something
copied because it is known to work. Nothing about this workflow is known: the
README states only that the folder contains "the audit workflow", without naming
what is audited, by whom, against what standard, or what the run produces.
Composing a template from that would mean inventing the tool, and a fabricated
template is worse than a missing one, because the missing one is visibly missing.

This file therefore exists to record the absence, which is exactly the
"empty-but-valid" case PROCESS.md §9 provides for.

## Adding the first template

When the workflow gains an implementation, add its application forms here — the
actual files under `Tooling/v<version>/templates/` plus a description of each —
and append the matching entry to [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) in
the same change, so both directions of the §3 reciprocity check hold.
