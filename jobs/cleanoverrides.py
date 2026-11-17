#!/usr/bin/env python3
"""One-off (#887 step 7): a place node keeps a `name` of its own only when it says something the species row does not. A name that differs from the row's only in capital letters, spacing or punctuation
("Common Raven" against the row's "Common raven") is the same name, so the node drops it and the row's wins. Reads and writes data/places/*.json (the node's own fields only); changes nothing else.
  python3 jobs/cleanoverrides.py          # rewrite the place files
  python3 jobs/cleanoverrides.py --dry    # count only"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import species

same_name = species.same_name

def clean(eco, by_sid):
    """Drop the noise `name` overrides of one place file's nodes; return how many."""
    n = 0
    for node in eco.get('nodes', []):
        row = by_sid.get(node.get('sp'))
        if row and same_name(node.get('name'), row.get('name')): del node['name']; n += 1
    return n

def main(dry=False):
    tab = species.table(); by_sid = {r['sid']: r for r in tab.values() if r.get('sid')}
    total = files = 0
    d = os.path.join(ROOT, 'data', 'places')
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json') or f in ('links.json', 'order.json', 'species.json', 'bounds.json'): continue
        p = os.path.join(d, f); e = json.load(open(p))
        if not isinstance(e, dict): continue
        n = clean(e, by_sid)
        if n:
            total += n; files += 1
            if not dry: json.dump(e, open(p, 'w'), ensure_ascii=False)
    print('%d name overrides dropped in %d place files%s' % (total, files, ' (dry run)' if dry else ''))

if __name__ == '__main__': main('--dry' in sys.argv)
