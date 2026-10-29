#!/usr/bin/env python3
"""syncmain.py: finish a merge of main into a data branch when the only clashes are the shared files that every data job edits.
  data/species.json   rows from both sides are kept (main's row wins when both changed the same species), then `species.py pack` rebuilds it
  data-auto/order.json  main's order, then the branch's new ids that are not already in main or promoted to data/
Any other conflicting file is left alone and the script exits 1, so a person looks at it."""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
def git(*a): return subprocess.run(('git',) + a, capture_output=True, text=True)
def show(stage, path):
    r = git('show', ':%d:%s' % (stage, path)); return json.loads(r.stdout) if r.returncode == 0 else None
conf = [l[3:] for l in git('status', '--porcelain').stdout.splitlines() if l[:2] in ('UU', 'AA', 'DU', 'UD')]
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
