#!/usr/bin/env python3
"""Track-B conformance checker for one tool dir (PROCESS.md §7 Track B).
Run from the tool directory. Prints verbatim results; exits 1 on any FAIL."""
import os,re,sys,hashlib

fail=0
def res(name,ok,detail):
    global fail
    tag='PASS' if ok else 'FAIL'
    if not ok: fail+=1
    print("[%s] %-18s %s"%(tag,name,detail))

# --- 1. Canonical files -----------------------------------------------------
five=['README.md','IMPLEMENTATIONS.md','TEMPLATES.md','KNOWN_ISSUES.md','CHANGE_LOG.md']
missing=[f for f in five if not (os.path.isfile(f) and os.path.getsize(f)>0)]
res('Canonical files',not missing,
    'all five exist and are non-empty' if not missing else 'missing/empty: '+', '.join(missing))

# --- entry parsing ----------------------------------------------------------
def entries(path):
    """returns list of (id, body). An entry = level-2 heading whose text is the bare id."""
    out=[];cur=None;buf=[]
    for ln in open(path):
        if ln.startswith('## '):
            if cur is not None: out.append((cur,''.join(buf)))
            cur=ln[3:].strip(); buf=[]
        elif cur is not None:
            buf.append(ln)
    if cur is not None: out.append((cur,''.join(buf)))
    return out

def heading_ok(i):
    return bool(re.match(r'^[a-z0-9]+(-[a-z0-9]+)*_[0-9a-f]{8}$',i)) or bool(re.match(r'^(IMP|T)-\d+$',i))

# --- 2. Reciprocity ---------------------------------------------------------
ki=entries('KNOWN_ISSUES.md'); cl=entries('CHANGE_LOG.md')
im=entries('IMPLEMENTATIONS.md'); tm=entries('TEMPLATES.md')
bad=[]
for path,es in (('KNOWN_ISSUES.md',ki),('CHANGE_LOG.md',cl),
                ('IMPLEMENTATIONS.md',im),('TEMPLATES.md',tm)):
    for i,_ in es:
        if not heading_ok(i): bad.append('%s: non-id heading "## %s"'%(path,i))

clids={i for i,_ in cl}; kiids={i for i,_ in ki}
tmids={i for i,_ in tm}; imids={i for i,_ in im}
for i,b in ki:
    if 'legacy' in re.findall(r'status:\**\s*`?([a-z-]+)',b): continue
    cited=[c for c in clids if c in b]
    if not cited: bad.append('KNOWN_ISSUES#%s cites no CHANGE_LOG id'%i)
for i,b in cl:
    cited=[c for c in kiids if c in b]
    if not cited: bad.append('CHANGE_LOG#%s cites no KNOWN_ISSUES id'%i)
for i,b in im:
    if not [t for t in tmids if t in b]: bad.append('IMPLEMENTATIONS#%s cites no TEMPLATES id'%i)
for i,b in tm:
    if not [t for t in imids if t in b]: bad.append('TEMPLATES#%s cites no IMPLEMENTATIONS id'%i)
res('Reciprocity',not bad,
    '%d KI / %d CL / %d IMP / %d T entries, all bare-id headings, all cross-cited'
      %(len(ki),len(cl),len(im),len(tm)) if not bad else '; '.join(bad))

# --- 3. Code layout ---------------------------------------------------------
vre=re.compile(r'^v\d+\.\d+\.\d+$')
tvers=sorted([d for d in os.listdir('Tooling')] if os.path.isdir('Tooling') else [])
loose=[e for e in os.listdir('.') if e not in five+['Tooling','Tests']]
ok3=os.path.isdir('Tooling') and all(vre.match(v) for v in tvers) and not loose
res('Code layout',ok3,
    'Tooling/%s holds all implementation files; nothing loose at the tool root'%(','.join(tvers))
      if ok3 else 'Tooling dirs=%s loose-at-root=%s'%(tvers,loose))

# --- 4. Test layout ---------------------------------------------------------
cur=sorted(tvers)[-1] if tvers else None
tests_dir=os.path.join('Tests',cur) if cur else None
ok4=bool(tests_dir and os.path.isdir(tests_dir) and os.listdir(tests_dir))
res('Test layout',ok4,
    'Tests/%s exists and holds %s'%(cur,', '.join(sorted(os.listdir(tests_dir)))) if ok4
      else 'no recorded results for current version %s'%cur)

# --- 5. Version agreement ---------------------------------------------------
readme=open('README.md').read()
m=re.search(r'Current version:\s*`?(v\d+\.\d+\.\d+)`?',readme)
rv=m.group(1) if m else None
cm=re.search(r'^\|\s*\[[^\]]+\]\([^)]+\)\s*\|[^|]*\|\s*`?(v\d+\.\d+\.\d+)`?\s*\|',
             open('CHANGE_LOG.md').read(),re.M)
cv=cm.group(1) if cm else None
ok5 = rv is not None and rv==cur==cv
res('Version agreement',ok5,
    'README=%s  newest Tooling/=%s  newest CHANGE_LOG entry=%s'%(rv,cur,cv))

print()
print('RESULT: %s (%d FAIL)'%('ALL FIVE PASS' if fail==0 else 'NOT CONFORMANT',fail))
sys.exit(1 if fail else 0)
