#!/usr/bin/env python3
"""syncmain.py: finish a merge of main into a data branch when the only clashes are the shared files that every data job edits.
  data/species.json   rows from both sides are kept (main's row wins when both changed the same species), then `species.py pack` rebuilds it
  data/<id>.json, data-auto/<id>.json  merged key by key: the branch keeps its food web (nodes, raw, ev, tip), main keeps everything else
  data-auto/order.json  main's order, then the branch's new ids that are not already in main or promoted to data/
Any other conflicting file is left alone and the script exits 1, so a person looks at it."""
import json, os, subprocess, sys
ROOT = os.environ.get('SYNC_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # SYNC_ROOT: run main's copy of this script inside a branch checkout
os.chdir(ROOT)
def git(*a): return subprocess.run(('git',) + a, capture_output=True, text=True)
def show(stage, path):
    r = git('show', ':%d:%s' % (stage, path)); return json.loads(r.stdout) if r.returncode == 0 else None
conf = [l[3:] for l in git('status', '--porcelain').stdout.splitlines() if l[:2] in ('UU', 'AA', 'DU', 'UD')]
GRAPH = ('nodes', 'raw', 'ev', 'tip')   # the food web: rebuilt by regen branches and rewritten by the species repack
def merge_place(path):
    """Key-by-key three-way merge of one place file. A key only one side changed takes that side; when both changed it, the branch keeps its
    food web (the rebuild is the point of the branch) and main keeps everything else (stories, photos, names). The repack follows."""
    base, mine, theirs = show(1, path), show(2, path), show(3, path)
    if not (base and mine and theirs): return False
    out = {}
    for k in dict.fromkeys(list(mine) + list(theirs)):
        m, b, t = mine.get(k), base.get(k), theirs.get(k)
        v = t if m == b else m if t == b else (m if k in GRAPH else t)
        if (k in mine or k in theirs) and not (v is None and k not in mine and k not in theirs): out[k] = v
    json.dump(out, open(path, 'w'), ensure_ascii=False); git('add', path); return True
taken = [c for c in conf if c.startswith(('data/', 'data-auto/')) and c.count('/') == 1 and c not in ('data/species.json', 'data/links.json', 'data-auto/order.json') and merge_place(c)]
conf = [c for c in conf if c not in taken]
other = [c for c in conf if c not in ('data/species.json', 'data-auto/order.json')]
if other: print('Conflicts that need a person:', ', '.join(other)); sys.exit(1)
if 'data/species.json' in conf:
    ours, theirs = show(2, 'data/species.json') or {}, show(3, 'data/species.json') or {}   # ours = branch, theirs = main
    json.dump({**ours, **theirs}, open('data/species.json', 'w'), ensure_ascii=False)
if 'data-auto/order.json' in conf:
    ours, theirs = show(2, 'data-auto/order.json') or [], show(3, 'data-auto/order.json') or []
    promoted = {f[:-5] for f in os.listdir('data') if f.endswith('.json')}
    seen = set(theirs) | promoted
    json.dump(theirs + [i for i in ours if i not in seen and os.path.exists('data-auto/%s.json' % i)], open('data-auto/order.json', 'w'), ensure_ascii=False)
print('resolved:', ', '.join(conf) or 'nothing to resolve')
if taken: print('merged key by key (branch food web, main for the rest):', ', '.join(taken))
