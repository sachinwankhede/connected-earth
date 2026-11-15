#!/usr/bin/env python3
"""rekeyspeciesphotos.py: one-time migration of the species pictures from title keys to species ids (docs/DATA-PLAN.md, "Species pictures", phase 3; #934).

Usage: rekeyspeciesphotos.py [dry]
Reads the old title-keyed lists (photos/species.json, species_hosted.json, species_metadata.json, species_large.json, species_medium.json, species_missing.json, species_hosted_skipped.json, species_source.json and the
four ledgers species_{commons,openverse,inaturalist,gbif}_tried.json) through lib/species_pics.py, gives every species the picture it showed before (its Latin name's title first, then the titles of its place nodes),
and writes the new shape through lib/species_photos.py: photos/species_pictures.json, species_medium.json, species_large.json, species_missing.json and species_tried.json, all keyed by sid. The old lists that the new
shape replaces are removed. Files are not renamed (a file name is a hash of the picture and species that show one picture share the file); a file no species points at any more is removed by repair().
Refuses when the new shape is already there. Prints a before-and-after table and checks the round trip: every title the build looked up before gives the same picture after (a title shared by species gives each of them the picture).
`dry` writes nothing. This file is deleted after the migration has run (as the place one was, #912)."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import species_pics, species_photos
import photo_registry as pr

REPLACED = ('species', 'species_hosted', 'species_metadata', 'species_hosted_skipped', 'species_source',
            'species_commons_tried', 'species_openverse_tried', 'species_inaturalist_tried', 'species_gbif_tried')   # old lists the new shape replaces
LEDGERS = {'species_commons_tried': 'commons', 'species_openverse_tried': 'openverse', 'species_inaturalist_tried': 'inaturalist', 'species_gbif_tried': 'gbif'}


def read(root, name):
    p = os.path.join(root, 'photos', name + '.json')
    if not os.path.exists(p): return {}
    with open(p) as f: return json.load(f)


def node_titles(root):
    """{sid: set of titles}: the Latin name, wiki and canonicalWiki of the nodes that carry the species in the places, the titles the build looked a picture up under."""
    import species
    out = {}
    for f in glob.glob(os.path.join(root, 'data', 'places', '*.json')):
        with open(f) as h: d = json.load(h)
        for n in d.get('nodes', []):
            if n.get('latin') and not n.get('cat'):
                out.setdefault(species.slug(n['latin']), set()).update(k for k in (n['latin'], n.get('wiki'), n.get('canonicalWiki')) if k)
    return out


def migrate(root, dry=False):
    if species_pics.new_shape(root): raise SystemExit('photos/species_pictures.json exists: the species pictures are already keyed by species id')
    nt = node_titles(root); old = species_pics.load(root, nt); rows = species_pics.rows(root)
    titles_of = {r['sid']: list(dict.fromkeys(sorted(nt.get(r['sid'], ()), key=lambda x: (x != r['latin'], x)) + [r['latin'], r['wiki']])) for r in rows}
    source = read(root, 'species_source'); skipped = read(root, 'species_hosted_skipped'); ledgers = {n: read(root, n) for n in LEDGERS}
    w = species_photos.SpeciesPhotos(root)   # it read the old species_missing, species_large and species_medium files (same names, old shape): start from empty lists
    w.pics = {}; w.miss_ = {}; w.tried = {}; w.medium = {}; w.large = {}
    for sid, e in sorted(old['pics'].items()):
        e = dict(e); t = e['wiki']
        if source.get(t): e['src'] = source[t]
        w.pics[sid] = e
        if sid in old['medium']: w.medium[sid] = old['medium'][sid]
        if sid in old['large']: w.large[sid] = old['large'][sid]
    for sid, status in sorted(old['missing'].items()):
        if sid in w.pics: continue
        w.miss_[sid] = pr.negative_entry(status if isinstance(status, str) else status.get('status', 'nophoto'), 1)
    for r in rows:   # a species the old lists recorded as skipped (not on Commons) is a miss too
        sid = r['sid']
        if sid in w.pics or sid in w.miss_: continue
        t = next((x for x in titles_of[sid] if x in skipped), None)
        if t: w.miss_[sid] = pr.negative_entry('notcommons', 1)
    for r in rows:   # the retry ledgers, for species with no picture
        sid = r['sid']
        if sid in w.pics: continue
        for name, src in LEDGERS.items():
            d = next((ledgers[name][x] for x in titles_of[sid] if x in ledgers[name]), None)
            if d: w.tried.setdefault(sid, {})[src] = d
    problems = round_trip(root, old, w, nt)
    table = report(root, old, w)
    print(table)
    if problems:
        print('\n'.join('PROBLEM ' + p for p in problems)); sys.exit(1)
    if dry: print('dry run: nothing written'); return table
    w.commit()
    for n in REPLACED:
        p = os.path.join(root, 'photos', n + '.json')
        if os.path.exists(p): os.remove(p)
    removed = species_photos.SpeciesPhotos(root).repair()   # files no species points at any more
    errs = species_photos.SpeciesPhotos(root).check()
    print('removed %d unreferenced item(s): %s' % (len(removed), ', '.join(removed[:8])))
    if errs: print('\n'.join('PROBLEM ' + e for e in errs)); sys.exit(1)
    return table


def round_trip(root, old, w, nt):
    """Problems if the new lists give a species a different picture than the old build did."""
    errs = []
    for sid, e in old['pics'].items():
        n = w.pics.get(sid)
        if not n or n['f'] != e['f'] or species_pics.credit(n) != species_pics.credit(e): errs.append('%s: picture differs' % sid)
        if (old['large'].get(sid) == e['f']) != (w.large.get(sid) == e['f']): errs.append('%s: larger copy differs' % sid)
        if (old['medium'].get(sid) == e['f']) != (w.medium.get(sid) == e['f']): errs.append('%s: tile copy differs' % sid)
    for sid in old['missing']:
        if sid not in w.miss_ and sid not in w.pics: errs.append('%s: missing record lost' % sid)
    from species_photos import author_missing
    for sid, e in w.pics.items():
        if author_missing(e): errs.append('%s: %s picture with no named author (the writer would refuse it)' % (sid, e.get('l')))
    return errs[:50]


def report(root, old, w):
    hosted = read(root, 'species_hosted'); chosen = {e['wiki'] for e in w.pics.values()}
    unused = sorted(t for t in hosted if t not in chosen)
    rows = [('pictures (titles before, species after)', len(hosted), len(w.pics)), ('larger copies', len(read(root, 'species_large')), len(w.large)), ('tile copies', len(read(root, 'species_medium')), len(w.medium)),
            ('recorded as no photo', len(read(root, 'species_missing')), len(w.miss_)), ('species in the retry ledger', sum(len(read(root, n)) for n in LEDGERS), len(w.tried))]
    out = ['| What | Before (by title) | After (by species id) |', '|---|---:|---:|'] + ['| %s | %d | %d |' % r for r in rows]
    out.append('\nHosted titles no species row uses any more (their file is removed): %d%s' % (len(unused), ' (' + ', '.join(unused[:10]) + ')' if unused else ''))
    return '\n'.join(out)


if __name__ == '__main__':
    migrate(ROOT, dry=len(sys.argv) > 1 and sys.argv[1] == 'dry')
