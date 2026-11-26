#!/usr/bin/env python3
"""addabiotic.py (#1138, owner 26 Nov: "Approve"): give a place with no abiotic node one accurate environment node, from a row that passed the identity check (its page is about exactly that thing).
The table below is the whole decision: place -> (row, node id, x hint, node `desc` in the place's own words, the nodes that use it). The node gets 'r' links (resource used by) to those nodes only.
  python3 jobs/addabiotic.py [--dry]     # default: list what would be added
  python3 jobs/addabiotic.py --apply     # write the nodes; run `python3 build/species.py pack` after
A place that already has an abiotic node, or a node id already taken, is left alone. Reads and writes data/places/<id>.json through jobs/strictrows.edit (same formatting)."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in ('build', 'lib', 'jobs'): sys.path.insert(0, os.path.join(ROOT, d))
import species, strictrows

TABLE = {
    'galapagos': ('volcanic-soils', 'soil', 0.5, 'The islands are young volcanoes; their thin lava and ash soils decide where plants grow, and so where tortoises and finches can feed.', ['tortoise', 'finch']),
    'ozarks': ('clear-fast-streams', 'stream', 0.34, 'Spring-fed, clear and cool, the Ozark streams are the home of mayflies, crayfish and the hellbender.', ['mayfly', 'crayfish', 'hellbender']),
    'xusct': ('tides', 'tide', 0.36, 'Twice a day the tide floods and uncovers the estuary marsh, setting when mussels and plankton can feed.', ['mussel', 'zoop']),
}

def plan(root=ROOT, table=TABLE):
    """{place: (row, node id, x, desc, users)} for the places in the table that still lack an abiotic node; problems = list of strings."""
    rows = {r['sid']: r for r in species.table(root).values() if r.get('sid')}; out, problems = {}, []
    for pid, (row, nid, x, desc, users) in sorted(table.items()):
        p = os.path.join(root, 'data', 'places', pid + '.json')
        if not os.path.exists(p): problems.append('%s: no such place' % pid); continue
        e = json.load(open(p, encoding='utf-8')); ids = {n['id']: n.get('sp') for n in e['nodes']}
        if row not in rows or rows[row].get('cat') != 'abiotic': problems.append('%s: %s is not an abiotic row' % (pid, row)); continue
        if any((rows.get(s) or {}).get('cat') == 'abiotic' for s in ids.values()): continue
        if nid in ids: problems.append('%s: node id %s is taken' % (pid, nid)); continue
        miss = [u for u in users if u not in ids]
        if miss: problems.append('%s: no node %s' % (pid, ', '.join(miss))); continue
        out[pid] = (row, nid, x, desc, users)
    return out, problems

def apply(root, todo):
    for pid, (row, nid, x, desc, users) in todo.items():
        def add(e):
            e['nodes'].append({'id': nid, 'sp': row, 'xh': x, 'desc': desc})
            e.setdefault('raw', []).extend([[nid, u, 'r'] for u in users]); return True
        strictrows.edit(os.path.join(root, 'data', 'places', pid + '.json'), add)

def main(argv):
    todo, problems = plan(ROOT)
    print('%d places %s' % (len(todo), 'to change' if '--apply' not in argv else 'changed'))
    for pid, (row, nid, x, desc, users) in todo.items(): print('add', pid, nid, row, '->', ', '.join(users))
    for q in problems: print('PROBLEM', q)
    if problems: sys.exit(1)
    if '--apply' in argv: apply(ROOT, todo)

if __name__ == '__main__': main(sys.argv[1:])
