#!/usr/bin/env python3
"""syncmain.py: finish a merge of main into a data branch when the only clashes are the shared files that every data job edits.
  data/species.json   rows from both sides are kept (main's row wins when both changed the same species), then `species.py pack` rebuilds it
  data/<id>.json  main's version when the branch only changed its packed food web (the repack); anything else needs a person
  data-auto/order.json  main's order, then the branch's new ids that are not already in main or promoted to data/
Any other conflicting file is left alone and the script exits 1, so a person looks at it."""
import json, os, subprocess, sys
ROOT = os.environ.get('SYNC_ROOT') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # SYNC_ROOT: run main's copy of this script inside a branch checkout
os.chdir(ROOT)
def git(*a): return subprocess.run(('git',) + a, capture_output=True, text=True)
def show(stage, path):
    r = git('show', ':%d:%s' % (stage, path)); return json.loads(r.stdout) if r.returncode == 0 else None
conf = [l[3:] for l in git('status', '--porcelain').stdout.splitlines() if l[:2] in ('UU', 'AA', 'DU', 'UD')]
GRAPH = ('nodes', 'raw', 'ev')   # the part that the species repack rewrites in every place
def repack_only(path):
    """True when the branch changed this place only in its packed food web (the repack), so main's version can be taken and the table rebuilt."""
    base, mine = show(1, path), show(2, path)
    if not base or not mine: return False
    strip = lambda d: {k: v for k, v in d.items() if k not in GRAPH}
    return strip(base) == strip(mine)
taken = [c for c in conf if c.startswith('data/') and c.count('/') == 1 and c not in ('data/species.json', 'data/links.json') and repack_only(c)]
for c in taken:
    git('checkout', '--theirs', '--', c); git('add', c)       # theirs = main
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
if taken: print('took main\'s version (the branch only had the repack):', ', '.join(taken))
