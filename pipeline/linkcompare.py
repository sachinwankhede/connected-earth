#!/usr/bin/env python3
"""linkcompare.py ST base_dir new_dir: compare two generated sets of places (before and after the plant re-pick in autogen.py).
Prints parks, how many pass the promotion floors, the share of links that are family-level, and which parks changed."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'build'))
import promote_check as pc
st, a, b = sys.argv[1:4]
def load(d):
    out = {}
    for f in sorted(os.listdir(os.path.join(d, 'out'))):
        if f.endswith('.json'): e = json.load(open(os.path.join(d, 'out', f))); out[e['id']] = (e, pc.check(e))
    return out
def stats(m):
    rows = list(m.values()); links = sum(r['links'] for _, r in rows)
    fam = sum(sum(1 for v in (e.get('ev') or {}).values() if v[0] == 'gf') for e, _ in rows)
    return len(rows), sum(1 for _, r in rows if r['pass_']), (100 * fam / links) if links else 0, links
A, B = load(a), load(b)
for label, m in (('before', A), ('after', B)):
    n, ok, fam, links = stats(m); print('%s | %s | parks %d | pass %d | links %d | family-level %.0f%%' % (st, label, n, ok, links, fam))
chg = [(i, A[i][1]['pass_'], B[i][1]['pass_']) for i in A if i in B and A[i][1]['pass_'] != B[i][1]['pass_']]
print('%s | pass changed for %d parks: %s' % (st, len(chg), ', '.join('%s %s->%s' % x for x in chg)))
# 10 random links from the "after" set for the spot check (docs/PROMOTION.md rule 3). Only links that are new in the after set are sampled,
# because those are the ones this change added.
import random
new = []
for i, (e, r) in B.items():
    nm = {n['id']: n['name'] for n in e['nodes']}
    old = set((A[i][0].get('ev') or {}).keys()) if i in A else set()
    for k, v in (e.get('ev') or {}).items():
        a, b2 = k.split('>')
        if k not in old and a in nm and b2 in nm: new.append((e['name'], nm[b2], nm[a], {'g': 'species-level', 'gg': 'genus-level', 'gf': 'family-level'}.get(v[0], v[0])))
random.Random(7).shuffle(new)
print('\n%s | spot check: 10 random links that are new in the after set (of %d)\n\n| Park | Eater | Eaten | GloBI match | Verdict |\n|---|---|---|---|---|' % (st, len(new)))
for p, eater, eaten, lvl in new[:10]: print('| %s | %s | %s | %s | |' % (p, eater, eaten, lvl))
