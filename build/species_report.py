#!/usr/bin/env python3
"""species_report.py [root] [--all]: read-only (#1061, step 1). Finds rows of the species table (species rows and the resource rows of data/nodes/rows) that say the same thing under different ids, and how many place nodes point at each, so the agent can decide what to merge. Nothing is changed.
Classes:
  same-name  two or more rows with the same display name (Phytoplankton x12, Decomposers x9)          -> merge candidate: one concept, one row
  wording    rows whose names differ only by words that carry no new concept (plural, 'and' / '&', order)  -> merge or keep as one fixed set; read by a person
  common-name  the same, but for taxon rows: each has its own Latin name, so they are different organisms that share a common name (Poison Ivy: radicans and rydbergii) -> NOT a merge; listed so a person can see the names that are ambiguous
Rows of different kinds (taxon / group / resource) are never reported together. Prints the counts per class and kind, then the groups with most place nodes; `--all` prints every group."""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.dirname(HERE))
sys.path.insert(0, HERE)
SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')

def words(s): return re.findall(r'[a-z]+', re.sub(r"[-'’]", '', (s or '').lower().replace('&', ' and ')))
def stem(w): return w[:-1] if len(w) > 3 and w.endswith('s') and not w.endswith('ss') else w
def wording(name): return tuple(sorted(stem(w) for w in words(name) if w != 'and'))

def uses(root):
    """{species id: number of place nodes that point at it}."""
    out = collections.Counter(); d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not f.endswith('.json') or f in SKIP: continue
        try: e = json.load(open(os.path.join(d, f)))
        except (OSError, ValueError): continue
        for n in (e.get('nodes') or []) if isinstance(e, dict) else []:
            if n.get('sp'): out[n['sp']] += 1
    return out

def groups(rows, used):
    """[(class, kind, name or wording, [(sid, name, nodes)])], same-name first, then wording groups that are not already one same-name group."""
    out = []; seen = set(); by = collections.defaultdict(list)
    for r in rows: by[(r.get('sk'), r['name'])].append(r)
    for (kind, name), rs in by.items():
        if len(rs) > 1: out.append(('common-name' if kind == 'taxon' else 'same-name', kind, name, [(r['sid'], r['name'], used[r['sid']]) for r in sorted(rs, key=lambda r: r['sid'])])); seen.update(r['sid'] for r in rs)
    by = collections.defaultdict(list)
    for r in rows:
        if r['sid'] not in seen and wording(r['name']): by[(r.get('sk'), wording(r['name']))].append(r)
    for (kind, w), rs in by.items():
        if len({r['name'] for r in rs}) > 1: out.append(('common-name' if kind == 'taxon' else 'wording', kind, ' '.join(w), [(r['sid'], r['name'], used[r['sid']]) for r in sorted(rs, key=lambda r: r['sid'])]))
    return sorted(out, key=lambda g: (g[0], -sum(n for _, _, n in g[3]), g[2]))

def report(root=ROOT):
    import species
    rows = [r for r in species.table(root).values() if r.get('sid') and r.get('name')]
    return groups(rows, uses(root))

if __name__ == '__main__':
    gs = report(); full = '--all' in sys.argv; tot = collections.Counter()
    for c, k, _, m in gs: tot[(c, k)] += 1; tot[(c, k, 'rows')] += len(m)
    for key in sorted(k for k in tot if len(k) == 2): print('%-9s %-8s %3d groups %4d rows' % (key[0], key[1], tot[key], tot[key + ('rows',)]))
    for c, k, name, m in (gs if full else gs[:15]):
        print('%s %s %r: %d rows, %d nodes' % (c, k, name, len(m), sum(n for _, _, n in m)))
        for sid, nm, n in m: print('    %-45s %-40s %d' % (sid, nm, n))
