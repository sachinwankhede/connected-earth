#!/usr/bin/env python3
"""override_report.py [root] [--all]: read-only (#1038, step 1). Sorts the place-node names that differ from their species row (`name` overrides) into classes, so the agent can fix what is a spelling and keep what is a real name.
Classes (a heuristic, to be read by a person; nothing is changed):
  spelling  the same words: singular or plural, hyphen, spacing, and, & (Cattails / Cattail, Beavertail / Beaver-tail cactus)  -> choose one name in the row, drop the override
  form      one name contains the other plus a qualifier (Leopard / Javan leopard, Brittlebush / White brittlebush)           -> a regional or subspecies form: keep
  group     a group or resource rather than a species (fungi, microbes, soil, grasses, fish, trees, algae, 'a and b')        -> decide: a group row of its own, or one fixed wording
  other     a different common name (Argali / Marco Polo sheep, Cardinal catchfly / Indian-pink)                              -> a regional or alternative name: keep unless the node names the wrong species
Prints the count of pairs and nodes per class and the most-used pairs of each class; `--all` prints every pair."""
import collections, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = next((a for a in sys.argv[1:] if not a.startswith('--')), os.path.dirname(HERE))
sys.path.insert(0, HERE)
SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')
GROUP = set('fungi bacteria microbes microbe decomposers decomposer soil soils grass grasses fish trees tree shrubs shrub algae plankton phytoplankton zooplankton insects insect birds mammals peat water rain sun wood litter detritus herbs plants'.split())

def words(s): return re.findall(r'[a-z]+', re.sub(r"[-'’]", '', (s or '').lower().replace('&', ' and ')))
def stem(w): return w[:-1] if len(w) > 3 and w.endswith('s') and not w.endswith('ss') else w
def key(s): return [stem(w) for w in words(s) if w != 'and']

def classify(row, node):
    a, b = key(row), key(node)
    if ''.join(a) == ''.join(b) or sorted(a) == sorted(b): return 'spelling'
    wa, wb = set(words(row)) | set(words(node)), set(words(row)) & set(words(node))
    if (GROUP & wa) or ' and ' in (' ' + (row + ' ' + node).lower().replace('&', 'and') + ' ') or '/' in node: return 'group'
    if set(a) <= set(b) or set(b) <= set(a): return 'form'
    return 'other'

def pairs(root=ROOT):
    import species
    sp = species.table(root); by = {r['sid']: r for r in sp.values() if r.get('sid')}; out = collections.Counter(); d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json') or f in SKIP: continue
        try: e = json.load(open(os.path.join(d, f)))
        except (OSError, ValueError): continue
        for n in (e.get('nodes') or []) if isinstance(e, dict) else []:
            r = by.get(n.get('sp'))
            if r and 'name' in n and not species.same_name(n['name'], r.get('name')): out[(r.get('name') or '', n['name'])] += 1
    return out

def report(root=ROOT):
    by = collections.defaultdict(list)
    for (a, b), c in pairs(root).items(): by[classify(a, b)].append((c, a, b))
    return {k: sorted(v, reverse=True) for k, v in by.items()}

if __name__ == '__main__':
    rep = report(); full = '--all' in sys.argv
    for k in ('spelling', 'form', 'group', 'other'):
        v = rep.get(k, []); print('%-9s %4d pairs %4d nodes' % (k, len(v), sum(c for c, _, _ in v)))
        for c, a, b in (v if full else v[:6]): print('   %2d  %s  ->  %s' % (c, a, b))
