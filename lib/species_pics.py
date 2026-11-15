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
            out['pics'][r['sid']] = e
            if t in med: out['medium'][r['sid']] = med[t]
            if t in lg: out['large'][r['sid']] = lg[t]
        elif t in miss: out['missing'][r['sid']] = miss[t]
    return out
