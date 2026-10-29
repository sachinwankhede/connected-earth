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
