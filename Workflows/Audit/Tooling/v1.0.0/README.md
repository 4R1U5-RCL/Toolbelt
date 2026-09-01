# Tooling/v1.0.0 — Workflows/Audit

**This directory holds no code, because `Workflows/Audit` has none.**

PROCESS.md §4 says `Tooling/v<version>/` holds "the tool's code at that version".
At v1.0.0 that code does not exist. Before the conformance migration of
2026-08-31 the whole tool was one file — a `README.md` containing the single
sentence *"This folder contains the audit workflow."* — and no script, module,
command, config, example or test was ever committed alongside it.

Nothing was moved into this directory, because there was nothing to move. This
file is a marker, not an implementation, and it is the only file here.

## Why the directory exists anyway

Three documents at the tool root name `v1.0.0` — `README.md`, the
`CHANGE_LOG.md` entry `brought-workflows-audit-into-track-b-con_be1c5a4b`, and
`Tests/v1.0.0/`. Without this directory that version would be named by every
document and represented by nothing, and git does not track empty directories,
so the anchor would vanish from the repository entirely.

**Do not read this directory's existence as the Track B code-layout check
passing.** That check is *vacuous* here, not satisfied: there is no code, so
there is nothing under `Tooling/` and nothing outside it either. The failure is
logged in [`../../KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md).

## For whoever writes the implementation

Two honest options, and the process does not settle which is correct for a
version directory that never shipped code:

1. Populate this directory, since v1.0.0 was never released and never ran.
2. Treat this as an empty anchor and seed `Tooling/v1.1.0/` (or `v2.0.0`) from
   it, per the §6 step-3 rule that iteration happens in a new version directory.

Whichever is chosen, PROCESS.md §6 applies from step 1: log the work in
`KNOWN_ISSUES.md` and `CHANGE_LOG.md` first, and record the real test output
under `Tests/`. Delete this file when real code lands here — its only job is to
state an absence, and once that absence ends the statement becomes false.
