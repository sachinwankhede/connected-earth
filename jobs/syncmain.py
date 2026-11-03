#!/usr/bin/env python3
"""syncmain.py: finish a merge of main into a data branch when the only clashes are the shared files that every data job edits.
  (data/species/rows/ needs nothing here: each species is its own file, so two branches only meet on a species both added, and then git merges identical files and a person looks at different ones)
  data/places/<id>.json  (pilot places too: they carry stage "pilot" until promoted) merged key by key: the branch keeps its food web (nodes, raw, ev, tip) when it rebuilt it, otherwise main's; main keeps everything else
  jobs/names.json  every latin name from both sides; a real common name beats null, main's wins a tie
  jobs/state_queue.txt  the states both sides still list (each side removed the ones it finished), in main's order
  (place order is in data/order/, one new file per job, and journeys are one file each, so neither needs a rule here: #277)
Any other conflicting file is left alone and the script exits 1, so a person looks at it."""
import json, os, subprocess, sys
ROOT = os.environ.get('SYNC_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # SYNC_ROOT: run main's copy of this script inside a branch checkout
os.chdir(ROOT)
def git(*a): return subprocess.run(('git',) + a, capture_output=True, text=True)
def show(stage, path):
    r = git('show', ':%d:%s' % (stage, path)); return json.loads(r.stdout) if r.returncode == 0 else None
st = {l[3:]: l[:2] for l in git('status', '--porcelain').stdout.splitlines() if l[:2] in ('UU', 'AA', 'DU', 'UD')}
conf = list(st)
GONE = object()
GRAPH = ('nodes', 'raw', 'ev', 'tip')   # the food web: rebuilt by regen branches and rewritten by the species repack
def merge_place(path):
    """Key-by-key three-way merge of one place file. The food web comes from the branch only when the branch rebuilt it (its edges or species ids
    differ from the base; a repack alone does not), otherwise from main. Any other key: the side that changed it wins, main when both did. The repack follows."""
    base, mine, theirs = show(1, path), show(2, path), show(3, path)
    if not (base and mine and theirs): return False
    ids = lambda d: [n.get('id') for n in d.get('nodes', [])]
    rebuilt = (mine.get('raw'), mine.get('ev'), ids(mine)) != (base.get('raw'), base.get('ev'), ids(base))   # the repack alone never changes these
    out = {}
    for k in dict.fromkeys(list(mine) + list(theirs)):
        m, b, t = mine.get(k, GONE), base.get(k, GONE), theirs.get(k, GONE)   # GONE: the key is absent on that side (a promotion drops "stage")
        if k in GRAPH: v = m if rebuilt else t
        else: v = t if m == b else m if t == b else t
        if v is not GONE: out[k] = v
    json.dump(out, open(path, 'w'), ensure_ascii=False); git('add', path); return True
taken = [c for c in conf if c.startswith('data/places/') and c.count('/') == 2 and merge_place(c)]
conf = [c for c in conf if c not in taken]
SHARED = ('jobs/names.json', 'jobs/state_queue.txt')
other = [c for c in conf if c not in SHARED]
if other: print('Conflicts that need a person:', ', '.join(other)); sys.exit(1)
if 'jobs/names.json' in conf:
    ours, theirs = show(2, 'jobs/names.json') or {}, show(3, 'jobs/names.json') or {}   # {latin: common name or null}; keep every name, a real name beats null
    out = {k: (theirs.get(k) or ours.get(k)) for k in sorted(set(ours) | set(theirs))}
    json.dump(out, open('jobs/names.json', 'w'), indent=1, ensure_ascii=False)
if 'jobs/state_queue.txt' in conf:
    ours, theirs = git('show', ':2:jobs/state_queue.txt').stdout, git('show', ':3:jobs/state_queue.txt').stdout   # text; each side removed the states it finished, so keep only states both still list
    keep = set(ours.split())
    open('jobs/state_queue.txt', 'w').write(''.join(x + '\n' for x in theirs.split() if x in keep))
print('resolved:', ', '.join(conf) or 'nothing to resolve')
if taken: print('merged key by key (branch food web, main for the rest):', ', '.join(taken))
