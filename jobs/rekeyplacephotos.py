#!/usr/bin/env python3
"""rekeyplacephotos.py: the one-time migration of the place-picture files from title keys to place-id keys (docs/DATA-PLAN.md, step 3, phase 3; #887).
Usage: rekeyplacephotos.py [--dry]   (run from the repository root; --dry prints the report and changes nothing; no network)

Before: photos/places/places.json, missing.json, photos/places_large.json and four retry ledgers (places_{nearby,category,commons,openverse}_tried.json) are keyed by the Wikipedia title (the place's `imgwiki`).
After:  the same data keyed by PLACE ID, the title kept as the row field `wiki`; one ledger photos/places_tried.json {id: {source: date}}; file names are <id>.jpg and <id>.webp (lib/place_photos.py).
A title used by more than one place (the shared titles) is NOT copied: its picture is removed (file and larger copy) and each of its places is recorded as missing ('nophoto', source 'rekey'), so two places never share a record again.
A title no place uses, a missing row or a ledger row of a shared or unused title is dropped and listed. Files no list mentions are removed at the end (lib/place_photos.repair()); the result must pass PlacePhotos.check() or the job fails.
The round trip is proved: unkeying the new files gives the old rows (ignoring file name and `wiki`) for every unshared place.
Files are written first, lists next, deletions last, as lib/place_photos.py does."""
import collections, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib')); import place_photos as pp, photo_registry as pr

SOURCES = ('nearby', 'category', 'commons', 'openverse')

def ids_by_title(place_dir):
    """{imgwiki title: [place ids]} from data/places/*.json (only id and imgwiki are read)."""
    out = collections.defaultdict(list)
    for f in sorted(glob.glob(os.path.join(place_dir, '*.json'))):
        try: d = json.load(open(f, encoding='utf-8'))
        except (OSError, ValueError): continue
        if isinstance(d, dict) and d.get('id') and d.get('imgwiki'): out[d['imgwiki']].append(d['id'])
    return dict(out)

def migrate(pics, miss, large, ledgers, ids, now=None):
    """Pure. pics {title: row}, miss {title: row}, large {title: file}, ledgers {source: {title: date}}, ids {title: [place ids]}.
    Returns dict(pics, miss, large, tried, moves, delete, shared, unplaced, dropped): new id-keyed dicts, jpg/webp renames [(old, new)], files to delete, and what was left out."""
    by_id, shared, unplaced = pp.rekey(pics, ids)
    new_large, moves, delete = {}, [], []
    for pid, row in by_id.items():
        old = dict(pics[row['wiki']]); f_old = old.get('f') or pid + '.jpg'
        by_id[pid] = dict(row, f=pid + '.jpg')
        if f_old != pid + '.jpg': moves.append((os.path.join('photos', 'places', f_old), os.path.join('photos', 'places', pid + '.jpg')))
        name = large.get(row['wiki'])
        if name:
            new_large[pid] = pid + '.webp'
            if name != pid + '.webp': moves.append((os.path.join('photos', 'places-lg', name), os.path.join('photos', 'places-lg', pid + '.webp')))
    for title, pids in shared.items():   # the picture of a shared title goes; each of its places is missing
        if title in pics:
            delete.append(os.path.join('photos', 'places', pics[title].get('f') or ''))
            if large.get(title): delete.append(os.path.join('photos', 'places-lg', large[title]))
    new_miss = {}; dropped = collections.Counter()
    for title, row in miss.items():
        pids = ids.get(title, [])
        if len(pids) == 1 and title not in pics: new_miss[pids[0]] = row
        else: dropped['missing:shared' if len(pids) > 1 else 'missing:unplaced'] += 1
    for title, pids in shared.items():
        if title in pics:
            for pid in pids: new_miss[pid] = pr.negative_entry('nophoto', 1, now)
    tried = {}
    for src in SOURCES:
        for title, day in ledgers.get(src, {}).items():
            pids = ids.get(title, [])
            if len(pids) == 1: tried.setdefault(pids[0], {})[src] = day
            else: dropped['ledger:shared' if len(pids) > 1 else 'ledger:unplaced'] += 1
    return dict(pics=by_id, miss=new_miss, large=new_large, tried=tried, moves=moves, delete=sorted(set(delete)), shared=shared, unplaced=unplaced, dropped=dict(dropped))

def unkey(new):
    """The old title-keyed rows from the new id-keyed ones (without file name and `wiki`), for the round-trip proof."""
    return {r['wiki']: {k: v for k, v in r.items() if k not in ('f', 'wiki')} for r in new['pics'].values()}

def proof(old_pics, new, skip):
    """Problems with the round trip: every title not in `skip` (shared or unused titles are deliberately not copied) must come back with the same row (ignoring f and wiki)."""
    back = unkey(new); errs = []
    for t, row in old_pics.items():
        if t in skip: continue
        want = {k: v for k, v in row.items() if k not in ('f', 'wiki')}
        if back.get(t) != want: errs.append('%s: row does not round-trip' % t)
    for t in back:
        if t not in old_pics: errs.append('%s: not in the old file' % t)
    return errs

def report(old, new):
    lines = ['| file | before | after |', '|---|---:|---:|']
    for name, a, b in (('places.json (pictures)', len(old['pics']), len(new['pics'])), ('missing.json', len(old['miss']), len(new['miss'])), ('places_large.json', len(old['large']), len(new['large'])),
                       ('retry ledgers (rows, 4 files -> places_tried.json ids)', sum(len(v) for v in old['ledgers'].values()), sum(len(v) for v in new['tried'].values()))):
        lines.append('| %s | %d | %d |' % (name, a, b))
    lines += ['', 'file renames: %d; files removed with a shared title: %d' % (len(new['moves']), len(new['delete'])),
              'shared titles (picture removed, places recorded missing): %s' % (', '.join('%s -> %s' % (t, '+'.join(i)) for t, i in sorted(new['shared'].items())) or 'none'),
              'titles no place uses (not copied): %s' % (', '.join(new['unplaced']) or 'none'), 'rows left out: %s' % (json.dumps(new['dropped'], sort_keys=True) or '{}')]
    return '\n'.join(lines)

def _load(path):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}

def main(root=ROOT, dry=False):
    p = lambda *a: os.path.join(root, *a)
    old = dict(pics=_load(p(*pp.PLACES)), miss=_load(p(*pp.MISSING)), large=_load(p(*pp.LARGE)), ledgers={s: _load(p('photos', 'places_%s_tried.json' % s)) for s in SOURCES})
    if old['pics'] and not any('wiki' not in r for r in old['pics'].values()): print('already keyed by place id: nothing to do'); return 0
    ids = ids_by_title(p('data', 'places'))
    new = migrate(old['pics'], old['miss'], old['large'], old['ledgers'], ids)
    errs = proof(old['pics'], new, set(new['shared']) | set(new['unplaced']))
    print(report(old, new))
    if errs: print('ROUND TRIP FAILED:'); print('\n'.join(errs[:30])); return 1
    if dry: print('dry run: nothing written'); return 0
    # files first: every rename goes through a temporary name, so two places that swap names cannot collide
    tmp = []
    for k, (a, b) in enumerate(new['moves']):
        if os.path.exists(p(a)): t = p(a) + '.rekey%d' % k; os.replace(p(a), t); tmp.append((t, p(b)))
    for t, b in tmp: os.replace(t, b)
    for f in new['delete']:
        if f and os.path.exists(p(f)): os.remove(p(f))
    for parts, obj in ((pp.PLACES, new['pics']), (pp.MISSING, new['miss']), (pp.LARGE, new['large'])): pp._write_json(p(*parts), obj, indent=0)
    pp._write_json(p(*pp.TRIED), new['tried'])
    for s in SOURCES:
        if os.path.exists(p('photos', 'places_%s_tried.json' % s)): os.remove(p('photos', 'places_%s_tried.json' % s))
    w = pp.PlacePhotos(root); removed = w.repair()   # files no list mentions (the orphans) go; list rows without a file go too
    print('removed by repair (%d): %s' % (len(removed), ', '.join(removed) or 'none'))
    bad = pp.PlacePhotos(root).check()
    if bad: print('CHECK FAILED:'); print('\n'.join(bad[:30])); return 1
    print('check passed: files and lists agree'); return 0

if __name__ == '__main__': sys.exit(main(ROOT, '--dry' in sys.argv))
