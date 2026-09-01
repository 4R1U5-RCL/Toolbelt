#!/usr/bin/env python3
"""Track-B conformance checker — PROCESS.md §7, repo-wide.

Promoted from Workflows/Sprint/Tests/v1.0.0/trackb-check.py, which was written
for one tool and hardcoded that tool's id convention. PROCESS.md §4 gives this
repo-level home (decision 21): bin/ is not a tool directory, so §3 and §4 do not
apply to it.

Run from the repository root:

    python3 bin/trackb-check.py            # every tool
    python3 bin/trackb-check.py Skills/Memory   # one tool

Exits 0 if every check passes, 1 otherwise. Prints what it found, not just a
verdict — a heading it cannot parse is reported as unparsed, never skipped
silently. That loophole is exactly how the 2026-08-31 run recorded a false pass
(PROCESS.md §10 decision 11 and the Scrape entry).

Stdlib only, matching the rest of the repo.
"""
import hashlib
import os
import re
import sys

AREAS = ("Packages", "Skills", "Workflows")
FIVE = ("README.md", "IMPLEMENTATIONS.md", "TEMPLATES.md",
        "KNOWN_ISSUES.md", "CHANGE_LOG.md")
PAIRED = ("KNOWN_ISSUES.md", "CHANGE_LOG.md",
          "IMPLEMENTATIONS.md", "TEMPLATES.md")

# process.yaml: definitions.issue-status — the closed set of seven
STATUSES = {"open", "planned", "in-progress", "resolved",
            "escalated", "legacy", "wont-fix"}

SEMVER = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
HASHED_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*_[0-9a-f]{8}$")
# decision 20: impl/template ids are free slugs, deliberately not hashed
SLUG_ID = re.compile(r"^[A-Za-z0-9]+([-_][A-Za-z0-9]+)*$")


def canonical(text):
    """process.yaml: definitions.issue-id.hash8.canonical — the five steps, in order."""
    text = re.sub(r"[`*_]", "", text)                 # 1. strip inline markdown
    text = text.strip()                                # 2. trim
    text = text.lower()                                # 3. lowercase
    text = re.sub(r"\s+", " ", text)                   # 4. collapse whitespace
    return text.rstrip(".,;:!?")                       # 5. strip trailing punctuation


def hash8(text):
    return hashlib.sha256(canonical(text).encode()).hexdigest()[:8]


def entries(path):
    """Every level-2 heading is an entry (process.yaml: definitions.entry).

    Prose sections belong at level 3 or lower (decision 18); one left at level 2
    shows up here as a counterpart-less entry, which is the intended behaviour.
    """
    if not os.path.isfile(path):
        return []
    out, ident, buf = [], None, []
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            if ident is not None:
                out.append((ident, "".join(buf)))
            ident, buf = line[3:].strip(), []
        elif ident is not None:
            buf.append(line)
    if ident is not None:
        out.append((ident, "".join(buf)))
    return out


# A field value ends at a blank line, the next bullet-labelled field, or a heading.
_CONT_END = re.compile(r"^(\s*$|\s*[-*+]\s*\*{0,2}[a-z_]+\s*[.:]|#{1,6}\s|\|)", re.I)


def field(body, name, multiline=False):
    """Read one field. Tools may use a table or a definition list (definitions.entry
    allows either), so accept both, plus the bolded-label form actually in use.

    Values may wrap across lines; truncating at the newline silently changes the
    string that gets hashed, which is the same class of quiet-wrong-answer this
    checker exists to catch.
    """
    m = re.search(r"^\|\s*\*{0,2}%s\*{0,2}\s*\|([^|]*)\|" % re.escape(name),
                  body, re.M | re.I)
    if m:
        return m.group(1).strip()
    # A delimiter is mandatory — without it a prose line merely containing the
    # word ("status vocabulary is a closed set") reads as the field itself.
    # Two forms are in use: "**status:** x" and "**status.** x".
    pat = re.compile(r"^\s*[-*+]?\s*(?:\*{0,2}%s\*{0,2}\s*[.:]|\*{0,2}%s\s*[.:]\s*\*{0,2})\s*(.*)$"
                     % (re.escape(name), re.escape(name)), re.I)
    lines = body.split("\n")
    for i, line in enumerate(lines):
        m = pat.match(line)
        if not m:
            continue
        parts = [(m.group(1) or "").strip()]
        for cont in (lines[i + 1:] if multiline else []):
            if _CONT_END.match(cont):
                break
            parts.append(cont.strip())
        return " ".join(p for p in parts if p).strip()
    return None


def is_legacy(body):
    st = field(body, "status")
    return bool(st) and canonical(st).split()[0].strip("`") == "legacy"


def status_word(body):
    st = field(body, "status")
    if not st:
        return None
    return canonical(st).split(" — ")[0].split()[0].strip("`") if st.strip() else None


def versions(tool, sub):
    d = os.path.join(tool, sub)
    if not os.path.isdir(d):
        return []
    return sorted((v for v in os.listdir(d) if SEMVER.match(v)),
                  key=lambda v: tuple(int(x) for x in SEMVER.match(v).groups()))


class Report:
    def __init__(self, tool):
        self.tool, self.rows = tool, []
        self.failed = self.warned = 0

    def add(self, name, ok, detail, advisory=False):
        self.rows.append((ok, name, detail, advisory))
        if not ok and not advisory:
            self.failed += 1
        if not ok and advisory:
            self.warned += 1

    def render(self):
        print("\n%s" % self.tool)
        for ok, name, detail, advisory in self.rows:
            tag = "PASS" if ok else ("WARN" if advisory else "FAIL")
            print("  [%s] %-18s %s" % (tag, name, detail))


def check(tool):
    r = Report(tool)

    missing = [f for f in FIVE
               if not (os.path.isfile(os.path.join(tool, f))
                       and os.path.getsize(os.path.join(tool, f)) > 0)]
    r.add("Canonical files", not missing,
          "all five present and non-empty" if not missing
          else "missing or empty: " + ", ".join(missing))

    tooling, tests = versions(tool, "Tooling"), versions(tool, "Tests")
    r.add("Code layout", bool(tooling),
          "Tooling/%s" % ", ".join(tooling) if tooling
          else "no Tooling/v<major>.<minor>.<patch>/ directory")
    r.add("Test layout", bool(tests) and tests[-1:] == tooling[-1:],
          "Tests/%s" % ", ".join(tests) if tests and tests[-1:] == tooling[-1:]
          else "no recorded results for the current version (Tooling=%s Tests=%s)"
               % (tooling or "-", tests or "-"))

    docs = {name: entries(os.path.join(tool, name)) for name in PAIRED}
    problems = []

    # Heading form. Legacy entries keep their original headings (decision 16).
    for name, es in docs.items():
        hashed = name in ("KNOWN_ISSUES.md", "CHANGE_LOG.md")
        for ident, body in es:
            if is_legacy(body):
                continue
            ok = (HASHED_ID if hashed else SLUG_ID).match(ident)
            if not ok:
                problems.append('%s: "## %s" is not a bare id '
                                "(prose sections belong at level 3)" % (name, ident))

    # Reciprocity, over every entry, with no entry excused for looking unusual.
    def cross(src, dst):
        dst_ids = {i for i, _ in docs[dst]}
        for ident, body in docs[src]:
            if is_legacy(body):
                continue
            if not any(d in body for d in dst_ids):
                problems.append("%s#%s cites no %s id" % (src, ident, dst))

    for a, b in (("KNOWN_ISSUES.md", "CHANGE_LOG.md"),
                 ("CHANGE_LOG.md", "KNOWN_ISSUES.md"),
                 ("IMPLEMENTATIONS.md", "TEMPLATES.md"),
                 ("TEMPLATES.md", "IMPLEMENTATIONS.md")):
        cross(a, b)

    counts = " / ".join("%d %s" % (len(docs[n]), n.split("_")[0].split(".")[0])
                        for n in PAIRED)
    legacy = sum(1 for es in docs.values() for _, b in es if is_legacy(b))
    r.add("Reciprocity", not problems,
          "%s entries (%d legacy, exempt), all cross-cited" % (counts, legacy)
          if not problems else "; ".join(problems))

    # Status vocabulary, and the rule that resolved needs a merge commit.
    bad = []
    for name in ("KNOWN_ISSUES.md", "CHANGE_LOG.md"):
        for ident, body in docs[name]:
            st = status_word(body)
            if st is None:
                if name == "KNOWN_ISSUES.md":
                    bad.append("%s#%s has no status field" % (name, ident))
                continue
            if st not in STATUSES:
                bad.append('%s#%s status "%s" is outside the closed set of seven'
                           % (name, ident, st))
            if st == "resolved":
                mc = field(body, "merge_commit") or ""
                if not re.search(r"[0-9a-f]{7,40}", mc):
                    bad.append("%s#%s is resolved with no merge commit" % (name, ident))
    r.add("Status", not bad,
          "every status in the closed set; no resolved-without-merge"
          if not bad else "; ".join(bad), advisory=True)

    # Ids reproduce from the field the spec names as identity.
    bad, stale = [], []
    for name, ident_field in (("KNOWN_ISSUES.md", "summary"),
                              ("CHANGE_LOG.md", "iteration")):
        for ident, body in docs[name]:
            if is_legacy(body) or "_" not in ident:
                continue
            src = field(body, ident_field, multiline=True)
            if src is None:
                bad.append("%s#%s has no %s field to hash" % (name, ident, ident_field))
                continue
            want = ident.rsplit("_", 1)[1]
            if hash8(src) == want:
                continue
            # Decision 19 (strip inline markdown) was settled after these entries
            # were written. An id that reproduces only without that step is a
            # casualty of the amendment, not a wrong id — say which.
            if hashlib.sha256(
                    re.sub(r"\s+", " ", src.strip().lower()).rstrip(".,;:!?")
                    .encode()).hexdigest()[:8] == want:
                stale.append("%s#%s reproduces only under the pre-decision-19 rule"
                             % (name, ident))
            else:
                bad.append("%s#%s does not reproduce from %s (got %s)"
                           % (name, ident, ident_field, hash8(src)))
    detail = "every id reproduces from its identity field"
    if stale:
        detail = "%d id(s) predate decision 19: %s" % (len(stale), "; ".join(stale))
    if bad:
        detail = "; ".join(bad)
    r.add("Id reproduction", not bad, detail, advisory=True)

    # Version agreement: README, newest Tooling dir, newest CHANGE_LOG entry.
    readme = open(os.path.join(tool, "README.md"), encoding="utf-8").read() \
        if os.path.isfile(os.path.join(tool, "README.md")) else ""
    cur = tooling[-1] if tooling else None
    cl_versions = [field(b, "version") for _, b in docs["CHANGE_LOG.md"]]
    cl_versions = [v for v in cl_versions if v and SEMVER.match(v.strip("`* "))]
    newest_cl = cl_versions[-1].strip("`* ") if cl_versions else None
    ok = bool(cur) and cur in readme and (newest_cl is None or newest_cl == cur)
    r.add("Version agreement", ok,
          "README, Tooling/ and CHANGE_LOG all name %s" % cur if ok
          else "disagreement: Tooling=%s README mentions=%s CHANGE_LOG=%s"
               % (cur, cur in readme if cur else "-", newest_cl))
    return r


def main(argv):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    if argv:
        tools = argv
    else:
        tools = sorted(os.path.join(a, t)
                       for a in AREAS if os.path.isdir(a)
                       for t in os.listdir(a) if os.path.isdir(os.path.join(a, t)))
    reports = [check(t) for t in tools]
    for rep in reports:
        rep.render()
    failed = [rep for rep in reports if rep.failed]
    warned = [rep for rep in reports if rep.warned]
    print("\n%d tool(s) checked, %d failing, %d with advisories"
          % (len(reports), len(failed), len(warned)))
    for rep in failed:
        print("  FAIL %s (%d check(s))" % (rep.tool, rep.failed))
    for rep in warned:
        print("  WARN %s (%d advisory check(s))" % (rep.tool, rep.warned))
    if warned and not failed:
        print("\nAdvisories do not fail the build. Status and Id reproduction "
              "depend on\nreading a named field out of an entry, and PROCESS.md "
              "does not specify how a\nfield is written in markdown — only 3 of 11 "
              "CHANGE_LOG.md files express\n`iteration` in a form any parser can "
              "find. See §10 decision 23.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
