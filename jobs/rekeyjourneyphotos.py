#!/usr/bin/env python3
"""rekeyjourneyphotos.py: one-time creation of the journey cover pictures, keyed by journey id (docs/DATA-PLAN.md, "Journey pictures: by journey id", phase 3; owner, 15 Nov: "Own").

Usage: rekeyjourneyphotos.py [dry]
Today a journey's cover is the picture of the Wikipedia title in its `imgwiki` (data/journeys/<id>.json), looked up in the title-keyed species lists. For each journey this reads that title's picture through
lib/species_pics.py (`titles`, `title_large`) and writes the journey its own row through lib/journey_photos.py: the 96 px file photos/journeys/<id>.webp (a copy of the species file) with its credit
({a, l, lu, p} plus f, wiki, page, u, src), the larger copy photos/journeys-lg/<id>.webp when the title has one, and photos/journey_pictures.json, journey_large.json, journey_missing.json, journey_tried.json.
A journey whose title has no hosted picture (a flow journey such as "Saharan Air Layer", or a species with no photo) gets no picture and a short-hold entry in journey_missing.json (status "notyet": nothing
has looked for it yet, so the acquire strategy of phase 4 retries it soon, not after the 180 days of a permanent "no photo"). The species files stay: species still show them.
Refuses when photos/journey_pictures.json already exists. Prints a table (journey, title, file, licence, author) and checks the round trip: every journey shows the same file and credit as before, a CC BY
cover with no author stops the migration (the writer would refuse it). `dry` writes nothing. This file is deleted after the migration has run (as the place and species ones were)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import species_pics, journey_pics, journey_photos
from journey_photos import author_missing


def read(root, name):
    p = os.path.join(root, 'photos', name + '.json')
    if not os.path.exists(p): return {}
    with open(p) as f: return json.load(f)


def blob(root, *parts):
    with open(os.path.join(root, *parts), 'rb') as f: return f.read()


def plan(root):
    """[(journey id, title, old row or None)] in id order."""
    import journeydata
    old = species_pics.load(root)['titles']
    return [(c['id'], c.get('imgwiki'), old.get(c.get('imgwiki'))) for c in sorted(journeydata.journeys(root), key=lambda c: c['id'])]


def migrate(root, dry=False):
    if journey_pics.new_shape(root): raise SystemExit('photos/journey_pictures.json exists: the journey pictures are already keyed by journey id')
    sp = species_pics.load(root); source = read(root, 'species_source'); items = plan(root)
    w = journey_photos.JourneyPhotos(root); problems = []; lines = []
    for jid, title, row in items:
        if not row:
            w.miss(jid, 'notyet'); lines.append('| %s | %s | none | | |' % (jid, title or '(no imgwiki)')); continue
        e = dict(row); e.pop('f')
        if source.get(title): e['src'] = source[title]
        if author_missing(e): problems.append('%s: %s picture of %r has no named author (the writer would refuse it)' % (jid, e.get('l'), title)); continue
        small = os.path.join(root, 'photos', 'species', row['f'])
        if not os.path.isfile(small): problems.append('%s: file photos/species/%s is missing' % (jid, row['f'])); continue
        w.put(jid, e, blob(root, 'photos', 'species', row['f']))
        lg = sp['title_large'].get(title)
        if lg:
            if os.path.isfile(os.path.join(root, 'photos', 'species-lg', lg)): w.put_large(jid, blob(root, 'photos', 'species-lg', lg))
            else: problems.append('%s: larger file photos/species-lg/%s is missing' % (jid, lg))
        lines.append('| %s | %s | %s | %s | %s |' % (jid, title, row['f'], row.get('l', ''), row.get('a', '')))
    problems += round_trip(items, w)
    table = '\n'.join(['| Journey | Title before | Species file | Licence | Author |', '|---|---|---|---|---|'] + lines +
                      ['', '%d journeys: %d with a picture, %d without (%s)' % (len(items), len(w.pics), len(w.miss_), ', '.join(sorted(w.miss_)) or 'none')])
    print(table)
    if problems:
        print('\n'.join('PROBLEM ' + p for p in problems)); sys.exit(1)
    if dry: print('dry run: nothing written'); return table
    w.commit(); errs = journey_pics.check(root)
    if errs: print('\n'.join('PROBLEM ' + e for e in errs)); sys.exit(1)
    return table


def round_trip(items, w):
    """Problems if a journey would show a different file or credit than the title lookup did."""
    errs = []
    for jid, title, row in items:
        n = w.pics.get(jid)
        if row and not n and jid not in w.miss_: errs.append('%s: picture lost' % jid)
        elif row and n and species_pics.credit(n) != species_pics.credit(row): errs.append('%s: credit differs' % jid)
        elif not row and n: errs.append('%s: has a picture the title did not' % jid)
        elif not row and jid not in w.miss_: errs.append('%s: missing record lost' % jid)
    return errs[:50]


if __name__ == '__main__':
    migrate(ROOT, dry=len(sys.argv) > 1 and sys.argv[1] == 'dry')
