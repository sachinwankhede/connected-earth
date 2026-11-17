#!/usr/bin/env python3
"""data_status.py [root] [--json FILE]: the current state of each kind of data, one row each (#887 step 8; owner, 17 Nov: "the current status is more important than a trend").
Columns: items (what should have the thing), have, recorded as missing, invalid (the writer's own check() fails: files and lists disagree, a stale record), due (a miss whose hold has run out, so the weekly job tries it again),
doubts (a picture credited to "unknown author": the owner decides) and a verdict: fine, or what needs attention and what fixes it. No thresholds: a verdict comes only from rules already enforced.
Prints a table and, with --json, writes the same rows. Read-only, offline."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, HERE)

def unknown(pics):
    return sum(1 for r in pics.values() if isinstance(r, dict) and str(r.get('a', '')).strip().lower() in ('unknown author', 'unknown'))

def due(miss):
    import photo_registry as pr
    return sum(1 for v in miss.values() if not pr.cache_active(v))

def place_ids(root):
    d = os.path.join(root, 'data', 'places'); skip = ('links.json', 'order.json', 'species.json', 'bounds.json')
    return [f[:-5] for f in sorted(os.listdir(d)) if f.endswith('.json') and f not in skip] if os.path.isdir(d) else []

def row(name, items, have, missing=0, invalid=0, due_=0, doubts=0, fix=None):
    notes = []
    if invalid: notes.append('%d invalid: %s' % (invalid, (fix or {}).get('invalid', 'see the validator')))
    if due_: notes.append('%d due a retry: %s' % (due_, (fix or {}).get('due', 'the weekly job')))
    if doubts: notes.append('%d credited to an unknown author: owner decision' % doubts)
    return {'dataset': name, 'items': items, 'have': have, 'missing': missing, 'invalid': invalid, 'due': due_, 'doubts': doubts, 'verdict': 'attention' if notes else 'fine', 'notes': notes}

def rows(root=ROOT):
    out = []; places = place_ids(root)
    def add(name, make):
        try: out.append(make())
        except Exception as e: out.append(dict(row(name, 0, 0), verdict='attention', notes=['could not be read: %s' % e]))
    import place_photos, species_photos, journey_photos, node_photos, outline_records, place_inputs
    def pp():
        w = place_photos.PlacePhotos(root); return row('Place pictures', len(places), len(w.pics), len(w.miss_), len(w.check()), due(w.miss_), unknown(w.pics), {'invalid': 'lib/place_photos.py check', 'due': 'data-placepictures'})
    def sp():
        import species; w = species_photos.SpeciesPhotos(root); n = len(species.table(root)); return row('Species pictures', n, len(w.pics), len(w.miss_), len(w.check()), due(w.miss_), unknown(w.pics), {'due': 'the species picture jobs'})
    def jp():
        import journey_pics; w = journey_photos.JourneyPhotos(root); return row('Journey pictures', len(journey_pics.journey_ids(root)), len(w.pics), len(w.miss_), len(w.check()), due(w.miss_), unknown(w.pics))
    def npc():
        w = node_photos.NodePhotos(root); return row('Node pictures', len(w.pics) + len(w.miss_), len(w.pics), len(w.miss_), len(w.check()), due(w.miss_), unknown(w.pics))
    def ol():
        w = outline_records.OutlineRecords(root); return row('Outlines', len(places), len(w.recs), len(w.miss_), len(w.check()) + len(w.stale()), due(w.miss_), 0, {'invalid': 'python3 lib/outline_check.py review; jobs/dropoutlines.py', 'due': 'data-outlines'})
    def fw():
        w = place_inputs.PlaceInputs(root); errs, _ = w.check(); webs = [p for p, e in place_inputs.places(root)]
        return row('Food webs', len(webs), sum(1 for p in webs if (w.recs.get(p) or {}).get('web')), 0, len(errs), 0, 0, {'invalid': 'python3 build/species.py pack'})
    def st():
        w = place_inputs.PlaceInputs(root); stories = [p for p, e in place_inputs.places(root) if e.get('story')]
        return row('Stories', len(places), len(stories), len(places) - len(stories))
    for n, f in (('Place pictures', pp), ('Species pictures', sp), ('Journey pictures', jp), ('Node pictures', npc), ('Outlines', ol), ('Food webs', fw), ('Stories', st)): add(n, f)
    return out

def table(rs):
    L = ['| Data | Have | Missing | Invalid | Due a retry | Doubts | Status |', '|---|---:|---:|---:|---:|---:|---|']
    for r in rs: L.append('| %s | %d of %d | %d | %d | %d | %d | %s |' % (r['dataset'], r['have'], r['items'], r['missing'], r['invalid'], r['due'], r['doubts'], 'fine' if r['verdict'] == 'fine' else '**attention**: ' + '; '.join(r['notes'])))
    return '\n'.join(L)

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; root = args[0] if args and os.path.isdir(args[0]) else ROOT; rs = rows(root); print(table(rs))
    if '--json' in sys.argv:
        with open(sys.argv[sys.argv.index('--json') + 1], 'w') as h: json.dump(rs, h, indent=1)
