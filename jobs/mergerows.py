#!/usr/bin/env python3
"""mergerows.py (#1061, owner 26 Nov: "complete all bad data items"): merge rows that sit on one Wikipedia page. The loser's nodes point at the winner (a place that has both keeps the winner's node, and the loser's edges move to it);
a node that had no text of its own keeps the loser's text as its own `desc`; then the loser row goes (jobs/strictrows.apply). One row, one page.
  python3 jobs/mergerows.py [--apply]"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in ('build', 'lib', 'jobs'): sys.path.insert(0, os.path.join(ROOT, d))
import species, strictrows
PAIRS = {'seasonal-floodwater': 'environment', 'brackish-lagoon-water': 'lagoon-water', 'deep-cold-lakes': 'lakes-waterholes', 'lakes-and-rivers': 'lakes-waterholes',
         'oasis-springs-and-wadi': 'oasis-groundwater', 'rainwater-depressions-rawdat': 'rainfall', 'rain-and-snowmelt': 'snowmelt-and-glacier-water',
         'mountain-streams-and-pools': 'clear-fast-streams', 'dalibarda': 'rubus'}

def merge(root, pairs, write=True):
    """Returns {loser: number of nodes moved or dropped}."""
    tab = {r['sid']: r for r in species.table(root).values() if r.get('sid')}
    pairs = {l: w for l, w in pairs.items() if l in tab and w in tab}; done = {l: 0 for l in pairs}
    jn = strictrows.journey_nodes(root)
    for f in strictrows.place_files(root):
        try: e = json.load(open(f, encoding='utf-8'))
        except ValueError: continue
        if not isinstance(e, dict) or not any(n.get('sp') in pairs for n in e.get('nodes') or []): continue
        def fix(e):
            nodes = e['nodes']; remap = {}
            for n in list(nodes):
                l = n.get('sp')
                if l not in pairs: continue
                w = pairs[l]; has = next((m for m in nodes if m.get('sp') == w), None); done[l] += 1
                if has is not None and (e.get('id'), n['id']) not in jn: remap[n['id']] = has['id']; nodes.remove(n)
                else:
                    if not n.get('desc') and tab[l].get('desc'): n['desc'] = tab[l]['desc']
                    n['sp'] = w
            if remap:
                seen = []; raw = []
                for r in e.get('raw') or []:
                    r = [remap.get(x, x) if i < 2 else x for i, x in enumerate(r)]
                    if r[0] == r[1] or r in seen: continue
                    seen.append(r); raw.append(r)
                e['raw'] = raw
                if (e.get('tip') or {}).get('id') in remap: e['tip']['id'] = remap[e['tip']['id']]
                if e.get('ev'):
                    ev = {}
                    for k, v in e['ev'].items(): ev.setdefault('>'.join(remap.get(x, x) for x in k.split('>')), v)
                    e['ev'] = ev
            return True
        if write: strictrows.edit(f, fix)
    if write:
        removed, kept = strictrows.apply(root, set(pairs), False, {l: 'merged into %s: one row for one page' % w for l, w in pairs.items()})
        if removed: strictrows.record(root, 'mergerows', removed, {l: 'merged into %s: one row for one page' % w for l, w in pairs.items()}, kept)
    return done

if __name__ == '__main__':
    print(merge(ROOT, PAIRS, '--apply' in sys.argv))
