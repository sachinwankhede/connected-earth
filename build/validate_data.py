#!/usr/bin/env python3
"""validate_data.py [root]: format checks for the data files that are not places (places have build/validate.py).
Species table, journeys, outlines, hosted species pictures. Prints one line per problem and exits 1 if there is any."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def load(root, *p):
    path = os.path.join(root, *p)
    return json.load(open(path)) if os.path.exists(path) else None

def place_ids(root):
    ids = set()
    full = os.path.join(root, 'data/places')
    if os.path.isdir(full): ids |= {f[:-5] for f in os.listdir(full) if f.endswith('.json')}
    return ids

def check(root):
    errs = []; warns = []
    sp = load(root, 'data', 'species', 'species.json') or {}
    for k, v in sp.items():
        for f in ('latin', 'name', 'tl', 'wiki', 'desc', 'ic'):
            if f not in v: errs.append('species %r: missing %s' % (k, f))
        if v.get('latin') and k != v['latin'].lower(): errs.append('species %r: key is not the lowercase Latin name' % k)
        if 'tl' in v and not isinstance(v['tl'], int): errs.append('species %r: tl is not a whole number' % k)
    sids = [v.get('sid') for v in sp.values()]
    if sp and (None in sids or len(set(sids)) != len(sids)): errs.append('species: every row needs its own sid (stable id)')
    for k, v in sp.items():
        if v.get('sk') not in ('taxon', 'group', 'resource'): errs.append('species %r: sk must be taxon, group or resource' % k)
    ids = place_ids(root)
    links = load(root, 'data', 'journeys', 'links.json')
    if links is not None:
        order = links.get('order', [])
        if len(order) != len(set(order)): errs.append('journeys: place order has duplicates')
        for i in order:
            if i not in ids: errs.append('journeys: ordered place %r has no file' % i)
        seen = set()
        for c in links.get('cross', []):
            cid = c.get('id')
            if not cid or cid in seen: errs.append('journeys: missing or repeated id %r' % cid)
            seen.add(cid)
            for f in ('type', 'title', 'text'):
                if not c.get(f): errs.append('journey %r: missing %s' % (cid, f))
            for en in c.get('ends', []):
                if en.get('eco') not in ids: errs.append('journey %r: place %r has no file' % (cid, en.get('eco')))
    od = os.path.join(root, 'data', 'outlines')
    if os.path.isdir(od):
        for f in os.listdir(od):
            if f.endswith('.json') and f[:-5] not in ids: warns.append('outline %s has no place' % f)
    hosted = load(root, 'photos', 'species_hosted.json')
    if hosted is not None:
        meta = load(root, 'photos', 'species_metadata.json') or {}
        pd = os.path.join(root, 'photos', 'species')
        files = set(os.listdir(pd)) if os.path.isdir(pd) else set()
        for t, f in hosted.items():
            if f not in files: errs.append('hosted picture for %r: file %s is missing' % (t, f))
            m = meta.get(t)
            if not m or not m.get('a') or not m.get('l'): errs.append('hosted picture for %r: author or licence missing' % t)
        for f in files - set(hosted.values()): errs.append('photos/species/%s is not listed in species_hosted.json' % f)
    return errs, warns

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    errs, warns = check(root)
    for w in warns[:50]: print('warn ', w)
    for e in errs[:200]: print('ERROR', e)
    print('data format: %d problem(s), %d warning(s)' % (len(errs), len(warns))); sys.exit(1 if errs else 0)
