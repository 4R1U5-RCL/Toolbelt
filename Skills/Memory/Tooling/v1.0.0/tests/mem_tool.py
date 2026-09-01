#!/usr/bin/env python3
# stdlib-only. `build <memdir> <templatedir>` cuts a fixture memory dir from the shipped templates;
# `lint <memdir>` checks format + the index<->dir consistency the memory system relies on.
import sys, os, re, glob
ENUM = {"user","feedback","project","reference"}

def parse_frontmatter(path):
    with open(path, encoding="utf-8") as f: lines = f.read().splitlines()
    if not lines or lines[0].strip() != "---": return None
    fm, i = {}, 1
    while i < len(lines) and lines[i].strip() != "---":
        m = re.match(r"^(\w+):\s*(.*)$", lines[i])
        if m: fm[m.group(1)] = m.group(2).strip()
        mt = re.match(r"^\s+type:\s*(.*)$", lines[i])
        if mt: fm["type"] = mt.group(1).strip()
        i += 1
    return fm if lines[i:i+1]==["---"] else None

def build(memdir, tdir):
    os.makedirs(memdir, exist_ok=True)
    tmpl = open(os.path.join(tdir,"memory-entry.md.template"), encoding="utf-8").read()
    def entry(name, desc, typ, body):
        out=[]
        for ln in tmpl.splitlines():
            if ln.startswith("name:"): out.append(f"name: {name}")
            elif ln.startswith("description:"): out.append(f"description: {desc}")
            elif re.match(r"^\s+type:", ln): out.append(f"  type: {typ}")
            elif "{{Memory content.}}" in ln: out.append(body)
            elif ln.strip().startswith("<!--"): continue   # drop guidance comments
            else: out.append(ln)
        open(os.path.join(memdir,f"{name}.md"),"w",encoding="utf-8").write("\n".join(out).rstrip()+"\n")
    entry("reference_toolbelt-repo",
          "4R1U5-RCL/Toolbelt: reusable tool kits (Packages/Skills/Workflows)",
          "reference",
          "The Toolbelt repo holds replicable working-method packages. See [[project_toolbelt-skills]].")
    entry("project_toolbelt-skills",
          "Handoff + Memory skills packaged into Toolbelt/Skills",
          "project",
          "Handoff and Memory shipped to Toolbelt/Skills as working-method packages.\n"
          "**Why:** durable, shareable record of how we track work across sessions.\n"
          "**How to apply:** consult [[reference_toolbelt-repo]] before rebuilding either; "
          "future work tracked in [[project_future-thing]].")
    # index (no frontmatter; one row per entry, sectioned)
    idx = ("# Memory Index\n\n"
           "## Project\n"
           "- [Toolbelt skills](project_toolbelt-skills.md) — Handoff+Memory packaged into Toolbelt/Skills\n\n"
           "## Reference\n"
           "- [Toolbelt repo](reference_toolbelt-repo.md) — reusable tool kits\n")
    open(os.path.join(memdir,"MEMORY.md"),"w",encoding="utf-8").write(idx)

def lint(memdir):
    idxp = os.path.join(memdir,"MEMORY.md")
    idx = open(idxp, encoding="utf-8").read()
    entries = [os.path.basename(p) for p in glob.glob(os.path.join(memdir,"*.md")) if os.path.basename(p)!="MEMORY.md"]
    referenced = set(re.findall(r"\]\(([^)]+\.md)\)", idx))
    orphans = sorted(e for e in entries if e not in referenced)               # entry not in index = invisible
    dangling_idx = sorted(r for r in referenced if not os.path.exists(os.path.join(memdir,r)))
    bad_fm = []
    for e in entries:
        fm = parse_frontmatter(os.path.join(memdir,e))
        stem = e[:-3]
        if not fm or "name" not in fm or "description" not in fm or fm.get("type") not in ENUM or fm.get("name")!=stem:
            bad_fm.append(e)
    slugs = {e[:-3] for e in entries}
    wl = set(re.findall(r"\[\[([A-Za-z0-9_-]+)\]\]", "".join(open(os.path.join(memdir,e),encoding="utf-8").read() for e in entries)))
    wl_dangling = sorted(s for s in wl if s not in slugs)
    wl_resolved = sorted(s for s in wl if s in slugs)
    idx_has_fm = 1 if idx.lstrip().startswith("---") else 0
    row_bad = sum(1 for ln in idx.splitlines() if ln.startswith("- [") and not re.match(r"^- \[[^\]]+\]\([^)]+\.md\)\s+—\s+.+", ln))
    maxlen_ok = 1 if len(idx.splitlines()) <= 200 else 0
    q=lambda xs:"'"+" ".join(xs)+"'"
    print(f"ENTRIES={len(entries)}")
    print(f"INDEXED_OK={1 if not orphans else 0}")
    print(f"ORPHANS={q(orphans)}")
    print(f"DANGLING_INDEX={q(dangling_idx)}")
    print(f"FRONTMATTER_BAD={q(bad_fm)}")
    print(f"WL_RESOLVED={q(wl_resolved)}")
    print(f"WL_DANGLING={q(wl_dangling)}")
    print(f"INDEX_HAS_FRONTMATTER={idx_has_fm}")
    print(f"INDEX_ROWS_MALFORMED={row_bad}")
    print(f"MAXLEN_OK={maxlen_ok}")

if __name__=="__main__":
    {"build":lambda:build(sys.argv[2],sys.argv[3]),"lint":lambda:lint(sys.argv[2])}[sys.argv[1]]()
