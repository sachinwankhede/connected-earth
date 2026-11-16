#!/usr/bin/env python3
"""nodepictures_migrate.py: one-time creation of the pictures of non-species nodes, keyed by node id (#976 step A; docs/DATA-PLAN.md "Credits"; owner, 16 Nov).

Usage: nodepictures_migrate.py [dry]
Today the pictures of sunlight, rain, soil and decomposers are filed in photos/species_pictures.json as if they were species: one row per node label (`desert-soil`, `forest-soil-nutrients-2`, `summer-sunlight`...), the
`sk: resource` rows of data/species/rows, every one pointing at the picture of its Wikipedia concept title (`wiki`: Soil, Rain, Sunbeam, Decomposer). This reads those rows through lib/species_pics.py and writes ONE record
per concept through lib/node_photos.py: the id is the slug of the concept title, the record is the credit of the picture the rows share (a, l, lu, p, page, wiki, src), the file is a copy of the 192 px tile
photos/species-md/<f> as photos/nodes/<f2>, and the record gets `built` and `checkedAt` (no `expires`). It is ADDITIVE: no species row, picture or file is changed or removed (that is a later step, after the app reads
node pictures); a concept with no picture at all (antarctic-convergence, little-missouri-river) is recorded in photos/node_missing.json with status `notyet` (nothing has looked for it yet) for the acquire job; a taxon that happens to share a concept title (Termite, Sponge) is not a `resource` row and is left alone. Rows of one concept that disagree on the picture or credit are listed and the first by id is used.
Refuses when photos/node_pictures.json already exists. Prints a table (node id, concept title, rows, file, licence, author) and checks the round trip: every `resource` row with a picture shows the same credit through
its node id. `dry` writes nothing. Deleted after the migration has run (as the place, species and journey ones were)."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import species_pics, node_photos
import author_clean as ac
from node_photos import node_id
from place_photos import author_missing


def resource_rows(root):
    """{species id: concept title (`wiki`)} of the `sk: resource` rows (not taxa, not groups): node labels filed as species, with or without a picture."""
    out = {}
    for f in glob.glob(os.path.join(root, 'data', 'species', 'rows', '*', '*.json')):
        with open(f) as h: r = json.load(h)
        if r.get('sk') == 'resource': out[r['sid']] = r.get('wiki')
    return out


def blob(root, *parts):
    with open(os.path.join(root, *parts), 'rb') as f: return f.read()


def plan(root):
    """{node id: [(sid, row)]} for every resource row that has a picture and a concept title, rows in sid order."""
    pics = species_pics.load(root)['pics']; res = resource_rows(root); groups = {}
    for sid in sorted(pics):
        row = pics[sid]
        if sid in res and row.get('wiki'): groups.setdefault(node_id(row['wiki']), []).append((sid, row))
    return groups


def unpictured(root, groups):
    """Concept ids of resource rows that have a concept title but whose concept has no picture (e.g. antarctic-convergence, little-missouri-river): they go to the missing list so the acquire job looks for them by node id."""
    return sorted({node_id(w) for w in resource_rows(root).values() if w} - set(groups))


def migrate(root, dry=False):
    if os.path.exists(os.path.join(root, 'photos', 'node_pictures.json')): raise SystemExit('photos/node_pictures.json exists: the node pictures are already keyed by node id')
    sp = species_pics.load(root); groups = plan(root); w = node_photos.NodePhotos(root); problems = []; lines = []; differ = []
    for nid, rows in sorted(groups.items()):
        sid, row = rows[0]
        if len({(r['f'], tuple(sorted(species_pics.credit(r).items()))) for _, r in rows}) > 1: differ.append('%s: %d rows disagree on the picture or credit, using %s' % (nid, len(rows), sid))
        e = {k: v for k, v in row.items() if k not in ('f', 'u')}
        if author_missing(e): problems.append('%s: %s picture of %r has no named author (the writer would refuse it)' % (nid, e.get('l'), row.get('wiki'))); continue
        name = sp['medium'].get(sid) or row['f']; tile = os.path.join(root, 'photos', 'species-md', name)
        if not os.path.isfile(tile): tile = os.path.join(root, 'photos', 'species', row['f'])
        if not os.path.isfile(tile): problems.append('%s: no file for %s' % (nid, sid)); continue
        with open(tile, 'rb') as f: webp = f.read()
        w.put(nid, e, webp)
        lines.append('| %s | %s | %d | %s | %s | %s |' % (nid, row.get('wiki'), len(rows), w.pics[nid]['f'], row.get('l', ''), row.get('a', '')))
    for nid in unpictured(root, groups): w.miss(nid, 'notyet')
    problems += round_trip(groups, w)
    table = '\n'.join(['| Node id | Concept title | Rows | File | Licence | Author |', '|---|---|---:|---|---|---|'] + lines +
                      ['', '%d node pictures from %d resource rows; %d concepts without a picture go to node_missing.json (status notyet): %s' % (len(w.pics), sum(len(v) for v in groups.values()), len(w.miss_), ', '.join(sorted(w.miss_)) or 'none')] + (['', 'Rows that disagree (first used):'] + differ if differ else []))
    print(table)
    if problems:
        print('\n'.join('PROBLEM ' + p for p in problems)); sys.exit(1)
    if dry: print('dry run: nothing written'); return table
    w.commit(); errs = w.check()
    if errs: print('\n'.join('PROBLEM ' + e for e in errs)); sys.exit(1)
    return table


def core(row):
    """The credit fields a picture is shown with (author, licence, licence link, source page): the node record adds only `built` and `checkedAt` to them."""
    return {k: row.get(k) for k in ('a', 'l', 'lu', 'p')}


def shown(row):
    """`core` with the author as the writer stores it (the one author rule, lib/author_clean.py): 'Unknown' becomes 'Unknown author', a non-breaking space a space."""
    c = core(row); c['a'] = ac.clean_author(c['a']) or 'Unknown author'; return c


def round_trip(groups, w):
    """Problems if a resource row's concept would show a different credit than the row shows today (rows that disagree are reported above, not here)."""
    errs = []
    for nid, rows in groups.items():
        n = w.pics.get(nid)
        if not n: errs.append('%s: picture lost' % nid)
        elif core(n) != shown(rows[0][1]): errs.append('%s: credit differs' % nid)
    return errs[:50]


if __name__ == '__main__':
    migrate(ROOT, dry=len(sys.argv) > 1 and sys.argv[1] == 'dry')
