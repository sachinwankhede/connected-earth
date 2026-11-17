#!/usr/bin/env python3
"""One-off (#1038 step 1, #887 step 7): the species row's name wins over a place node's `name` that is only another spelling of it (Cattails / Cattail, Gray / Grey wolf). Each pair below was read and the row's name kept,
so the node drops its override. Group nodes (Fungi and bacteria, Fungi & bacteria, Bacteria and fungi) are not touched. Reads and writes data/places/*.json (node `name` only).
  python3 jobs/cleanspelling.py [--dry]"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import species
PAIRS = {  # (row name, node name)
    ('Fremont cottonwood', "Fremont's cottonwood"), ('Willows', 'Willow'), ('Tree lichens', 'Tree lichen'), ('Steppe rat snake', 'Steppes ratsnake'),
    ("Sandberg's bluegrass", 'Sandberg bluegrass'), ('Rhododendron', 'Rhododendrons'), ('Milkweed', 'Milkweeds'), ('Mangroves', 'Mangrove'), ('Leafcutter ants', 'Leafcutter ant'),
    ('Groundsel tree', 'Tree Groundsel'), ('Cattails', 'Cattail'), ('Arctic copepods', 'Arctic copepod'), ('Gray wolf', 'Grey wolf'), ('European roe deer', 'Roe deer')}

def clean(eco, by_sid, log=None):
    n = 0
    for node in eco.get('nodes', []):
        row = by_sid.get(node.get('sp'))
        if row and 'name' in node and (row.get('name'), node['name']) in PAIRS:
            if log is not None: log.append((node['name'], row['name']))
            del node['name']; n += 1
    return n

def main(dry=False):
    tab = species.table(); by_sid = {r['sid']: r for r in tab.values() if r.get('sid')}
    total = files = 0; d = os.path.join(ROOT, 'data', 'places')
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json') or f in ('links.json', 'order.json', 'species.json', 'bounds.json'): continue
        p = os.path.join(d, f); e = json.load(open(p))
        if not isinstance(e, dict): continue
        n = clean(e, by_sid)
        if n:
            total += n; files += 1
            if not dry: json.dump(e, open(p, 'w'), ensure_ascii=False)
    print('%d spelling name overrides dropped in %d place files%s' % (total, files, ' (dry run)' if dry else ''))

if __name__ == '__main__': main('--dry' in sys.argv)
