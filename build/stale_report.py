#!/usr/bin/env python3
"""stale_report.py [root]: read-only (#887 step 5). For each kind of derived data (an outline, a story, a food web) says how many items there are, how many record what they were built from
(so that a change of the input can be seen), and what disagrees today. Prints a table; exits 0 always (the stale check that fails a data pull request comes after this report has shown the numbers).
An item "records its inputs" when it stores the facts it was built from: an outline the place point and the source, a story the text it was written from, a food web the list of species and the diet evidence."""
import json, os, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')

def load(*p):
    path = os.path.join(ROOT, *p)
    return json.load(open(path)) if os.path.exists(path) else None

def places():
    d = os.path.join(ROOT, 'data', 'places')
    for f in sorted(os.listdir(d)):
        if f.endswith('.json') and f not in SKIP:
            try: e = json.load(open(os.path.join(d, f)))
            except (OSError, ValueError): continue
            if isinstance(e, dict): yield f[:-5], e

def report():
    rows = []; notes = []
    recs = load('data', 'outline_records.json') or {}
    od = os.path.join(ROOT, 'data', 'outlines')
    files = {f[:-5] for f in os.listdir(od) if f.endswith('.json')} if os.path.isdir(od) else set()
    ps = dict(places())
    # outlines: each record should say which place point it was built for (so a moved point shows as stale)
    with_point = sum(1 for r in recs.values() if isinstance(r, dict) and isinstance(r.get('inputs'), dict))
    rows.append(('outlines', len(files), with_point, 'record has `inputs` (the place point and name it was built for)'))
    if files - set(recs): notes.append('%d outline files have no record (e.g. %s)' % (len(files - set(recs)), sorted(files - set(recs))[0]))
    if set(recs) - files: notes.append('%d outline records have no file (e.g. %s)' % (len(set(recs) - files), sorted(set(recs) - files)[0]))
    if set(recs) - set(ps): notes.append('%d outline records name no place (e.g. %s)' % (len(set(recs) - set(ps)), sorted(set(recs) - set(ps))[0]))
    # stories and food webs: recorded in data/place_inputs.json (lib/place_inputs.py): a web by the hash of its nodes and links, a story by the hash of the research text it came from
    pi = load('data', 'place_inputs.json') or {}
    stories = [i for i, e in ps.items() if e.get('story')]
    with_src = sum(1 for i in stories if isinstance((pi.get(i) or {}).get('story'), dict))
    rows.append(('stories', len(stories), with_src, 'record has `story` (hash of the research text)'))
    webs = [i for i, e in ps.items() if e.get('nodes')]
    with_web = sum(1 for i in webs if isinstance((pi.get(i) or {}).get('web'), dict))
    rows.append(('food webs', len(webs), with_web, 'record has `web` (hash of the nodes and links)'))
    import sys as _s; _s.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib')); import place_inputs
    stale = [x for x in place_inputs.PlaceInputs(ROOT).stale_webs() if x[1] != 'no record']
    if stale: notes.append('%d food webs changed since their record, first %s' % (len(stale), ', '.join('%s (%s)' % x for x in stale[:5])))
    return rows, notes

if __name__ == '__main__':
    rows, notes = report()
    print('%-10s %7s %9s  %s' % ('kind', 'items', 'recording', 'what is recorded'))
    for k, n, r, what in rows: print('%-10s %7d %9d  %s' % (k, n, r, what))
    for n in notes: print('note:', n)
