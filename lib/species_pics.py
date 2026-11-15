#!/usr/bin/env python3
"""species_pics.py: read the species pictures by species id, from either shape (docs/DATA-PLAN.md, "Species pictures", phase 2; #934).

Until the migration (phase 3) the pictures are title-keyed lists (`photos/species.json`, `species_hosted.json`, `species_metadata.json`, `species_large.json`, `species_medium.json`,
`species_missing.json`); after it they are `photos/species_pictures.json` and friends, keyed by `sid` (lib/species_photos.py). `load(root)` returns the same thing from both: one row per
`sid` that has a picture, so a consumer never needs to know which shape is on disk. Reading the old shape gives every species row whose Wikipedia title is in the lists its own entry
(a title shared by two species gives each of them the picture, which is what the build showed before); the migration writes exactly that. Read only."""
import glob, json, os


def _read(root, *parts):
    p = os.path.join(root, *parts)
    if not os.path.exists(p): return None
    with open(p) as f: return json.load(f)


def rows(root='.'):
    """Every species row of data/species/rows (sid, latin, name, wiki), sorted by sid."""
    out = []
    for f in glob.glob(os.path.join(root, 'data', 'species', 'rows', '*', '*.json')):
        with open(f) as h: r = json.load(h)
        out.append({k: r.get(k) for k in ('sid', 'latin', 'name', 'wiki')})
    return sorted(out, key=lambda r: r['sid'])


def new_shape(root='.'): return os.path.exists(os.path.join(root, 'photos', 'species_pictures.json'))


<<<<<<< HEAD
def load(root='.', titles=None):
    """{'pics': {sid: row}, 'medium': {sid: file}, 'large': {sid: file}, 'missing': {sid: entry}, 'titles': {title: row}, 'title_large': {title: file}, 'shape': 'sid'|'title'}. `titles` (old shape only) is {sid: [titles a species is shown under on the places, e.g. from
    the nodes' wiki and canonicalWiki]}: the old build looked a species' picture up under those, its Latin name first, so a species' row is the first of them that has a picture. The `titles` and
    `title_large` results are the same pictures by Wikipedia title, for the journeys, which still name a picture by title (every hosted title in the old shape). A row is the credit row ({a, l, lu, p, ...}) plus
    `f` (the 96 px file name), `wiki` (the title the picture was found under), `page` (the Wikipedia page the species page links to) and `u` (the source path the larger copies
    are made from; a job that stores a picture in the new shape sets both)."""
    if new_shape(root):
        d = {'pics': _read(root, 'photos', 'species_pictures.json'), 'medium': _read(root, 'photos', 'species_medium.json') or {},
                'large': _read(root, 'photos', 'species_large.json') or {}, 'missing': _read(root, 'photos', 'species_missing.json') or {}, 'shape': 'sid'}
        d['titles'] = by_title(d['pics']); d['title_large'] = {}
        for sid in sorted(d['pics']):
            if d['large'].get(sid) == d['pics'][sid]['f']: d['title_large'].setdefault(d['pics'][sid].get('wiki'), d['pics'][sid]['f'])
        return d
    man = _read(root, 'photos', 'species.json') or {}; hosted = _read(root, 'photos', 'species_hosted.json') or {}; meta = _read(root, 'photos', 'species_metadata.json') or {}
    med = _read(root, 'photos', 'species_medium.json') or {}; lg = _read(root, 'photos', 'species_large.json') or {}; miss = _read(root, 'photos', 'species_missing.json') or {}
    out = {'pics': {}, 'medium': {}, 'large': {}, 'missing': {}, 'shape': 'title'}
    out['titles'] = {t: dict(meta.get(t) or {}, f=hosted[t], wiki=t, **({'u': man[t][0], 'page': man[t][1]} if t in man else {})) for t in sorted(hosted)}
    out['title_large'] = {t: lg[t] for t in sorted(hosted) if lg.get(t) == hosted[t]}
    for r in rows(root):
        # the title the old build looked a species' picture up under: its Latin name first, then the titles of its place nodes, then its row title (#934: 'Canis lupus' and 'Gray wolf' can carry different pictures)
        cands = sorted(set((titles or {}).get(r['sid'], ())), key=lambda x: (x != r['latin'], x)) or [r['latin'], r['wiki']]
        cands = list(dict.fromkeys(cands + [r['latin'], r['wiki']]))
        t = next((x for x in cands if x in hosted), None) or next((x for x in cands if x in miss), r['wiki'])
        if t in hosted:
            e = dict(meta.get(t) or {}); e['f'] = hosted[t]; e['wiki'] = t
            if t in man: e['u'] = man[t][0]; e['page'] = man[t][1]
=======
def load(root='.'):
    """{'pics': {sid: row}, 'medium': {sid: file}, 'large': {sid: file}, 'missing': {sid: entry}, 'shape': 'sid'|'title'}. A row is the credit row ({a, l, lu, p, ...}) plus
    `f` (the 96 px file name), `wiki` (the Wikipedia title) and `u` (the source path the larger copies are made from; absent in the new shape until a job stores it)."""
    if new_shape(root):
        return {'pics': _read(root, 'photos', 'species_pictures.json'), 'medium': _read(root, 'photos', 'species_medium.json') or {},
                'large': _read(root, 'photos', 'species_large.json') or {}, 'missing': _read(root, 'photos', 'species_missing.json') or {}, 'shape': 'sid'}
    man = _read(root, 'photos', 'species.json') or {}; hosted = _read(root, 'photos', 'species_hosted.json') or {}; meta = _read(root, 'photos', 'species_metadata.json') or {}
    med = _read(root, 'photos', 'species_medium.json') or {}; lg = _read(root, 'photos', 'species_large.json') or {}; miss = _read(root, 'photos', 'species_missing.json') or {}
    out = {'pics': {}, 'medium': {}, 'large': {}, 'missing': {}, 'shape': 'title'}
    for r in rows(root):
        t = r['wiki']
        if t in hosted:
            e = dict(meta.get(t) or {}); e['f'] = hosted[t]; e['wiki'] = t
            if t in man: e['u'] = man[t][0]
>>>>>>> origin/main
            out['pics'][r['sid']] = e
            if t in med: out['medium'][r['sid']] = med[t]
            if t in lg: out['large'][r['sid']] = lg[t]
        elif t in miss: out['missing'][r['sid']] = miss[t]
    return out
<<<<<<< HEAD


CREDIT = ('a', 'l', 'lu', 'p')   # the credit fields of a row; everything else (f, wiki, page, u) is bookkeeping


def credit(row):
    """The credit of a picture as the app and the species file carry it: the credit fields the row has."""
    return {k: row[k] for k in row if k not in ('f', 'wiki', 'page', 'u')}


def by_title(pics):
    """{title: row} from the by-sid rows, for the code that still looks a picture up by Wikipedia title (the journeys' covers and ends). A title shared by several species gives the row of the first sid in
    order; a consumer that knows the species uses its own sid instead."""
    out = {}
    for sid in sorted(pics): out.setdefault(pics[sid].get('wiki'), pics[sid])
    out.pop(None, None); return out
=======
>>>>>>> origin/main
