#!/usr/bin/env python3
"""validate_data.py [root]: format checks for the data files that are not places (places have build/validate.py).
Species table, journeys, outlines, hosted species pictures. Prints one line per problem and exits 1 if there is any."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))

def load(root, *p):
    path = os.path.join(root, *p)
    return json.load(open(path)) if os.path.exists(path) else None

SCHEMAS = os.path.join(HERE, 'schemas')
_validators = {}
def shape(obj, kind, where, errs):
    """Check one object against build/schemas/<kind>.schema.json (the written contract of that file); one error line per problem, with the path of the bad value."""
    import jsonschema
    if kind not in _validators:
        schema = json.load(open(os.path.join(SCHEMAS, kind + '.schema.json')))
        _validators[kind] = jsonschema.Draft202012Validator(schema)
    for e in sorted(_validators[kind].iter_errors(obj), key=lambda e: [str(p) for p in e.absolute_path]):
        path = '/'.join(str(p) for p in e.absolute_path)
        errs.append('%s%s: %s' % (where, ' [%s]' % path if path else '', e.message[:160]))

def place_ids(root):
    ids = set()
    full = os.path.join(root, 'data/places')
    if os.path.isdir(full): ids |= {f[:-5] for f in os.listdir(full) if f.endswith('.json')}
    return ids

def check(root):
    errs = []; warns = []
    sys.path.insert(0, HERE); import species
    sp = species.table(root)
    rows_dir = os.path.join(root, 'data', 'species', 'rows')
    if os.path.isdir(rows_dir):   # one file per species (#276): each is checked on its own, and sits where its sid says
        keys = {}
        for d in sorted(os.listdir(rows_dir)):
            for f in sorted(os.listdir(os.path.join(rows_dir, d))):
                if not f.endswith('.json'): continue
                r = json.load(open(os.path.join(rows_dir, d, f)))
                shape(r, 'species-row', 'species file %s/%s' % (d, f), errs)
                if isinstance(r, dict) and isinstance(r.get('sid'), str) and (d, f) != (r['sid'][:2], r['sid'] + '.json'):
                    errs.append('species file %s/%s: a row with sid %r belongs in %s/%s.json' % (d, f, r['sid'], r['sid'][:2], r['sid']))
                if isinstance(r, dict) and r.get('name'):
                    k = (r.get('latin') or r['name']).lower()
                    if k in keys: errs.append('species files %s and %s have the same table key %r (the loader keeps only one)' % (keys[k], '%s/%s' % (d, f), k))
                    keys.setdefault(k, '%s/%s' % (d, f))
    else:
        for k, v in sp.items(): shape(v, 'species-row', 'species %r' % k, errs)
    for k, v in sp.items():
        if v.get('latin') and k != v['latin'].lower(): errs.append('species %r: key is not the lowercase Latin name' % k)
    sids = [v.get('sid') for v in sp.values()]
    if sp and (None in sids or len(set(sids)) != len(sids)): errs.append('species: every row needs its own sid (stable id)')
    ids = place_ids(root)
    import journeydata
    errs += journeydata.order_problems(root)
    has_links = os.path.exists(os.path.join(root, 'data', 'journeys', 'links.json'))
    if has_links or journeydata.journeys_are_new(root):
        order = journeydata.order(root)[0]
        if len(order) != len(set(order)): errs.append('journeys: place order has duplicates')
        for i in order:
            if i not in ids: errs.append('journeys: ordered place %r has no file' % i)
        seen = set()
        for where, c in journeydata.raw_journeys(root):
            shape(c, 'journey', where, errs)
            if not isinstance(c, dict): continue
            cid = c.get('id')
            if not cid or cid in seen: errs.append('journeys: missing or repeated id %r' % cid)
            seen.add(cid)
            for en in list(c.get('ends') or []) + [c.get('from'), c.get('to')]:
                if isinstance(en, dict) and en.get('eco') not in ids: errs.append('journey %r: place %r has no file' % (cid, en.get('eco')))
        if journeydata.journeys_are_new(root): shape(json.load(open(os.path.join(root, 'data', 'journeys', 'config.json'))), 'journey-config', 'journeys/config.json', errs)
    od = os.path.join(root, 'data', 'outlines')
    if os.path.isdir(od):
        for f in sorted(os.listdir(od)):
            if not f.endswith('.json'): continue
            if f[:-5] not in ids: errs.append('outline %s has no place' % f)   # an error since #255 (a leftover usually means a rename went wrong)
            o = json.load(open(os.path.join(od, f)))
            shape(o, 'outline', 'outline %s' % f, errs)
            for n, ring in enumerate(o.get('r', []) if isinstance(o, dict) and isinstance(o.get('r'), list) else []):
                if not isinstance(ring, list) or any(not isinstance(v, (int, float)) for v in ring): continue   # the shape check reports it
                if len(ring) % 2: errs.append('outline %s: ring %d has an odd number of values (it is [lon, lat, ...])' % (f, n))
                elif any(not -180 <= ring[i] <= 180 or not -90 <= ring[i + 1] <= 90 for i in range(0, len(ring), 2)):
                    errs.append('outline %s: ring %d has a point outside lon -180..180 / lat -90..90' % (f, n))
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
        listed = load(root, 'photos', 'species.json')   # every species in the picture list is hosted or skipped on purpose (#238): none is left to a missing picture by accident
        if listed is not None:
            skipped = load(root, 'photos', 'species_hosted_skipped.json') or {}
            for t in sorted(set(listed) - set(hosted) - set(skipped)): errs.append('species picture list: %r is neither hosted nor in species_hosted_skipped.json' % t)
    # job-written lists (#255, PR 2): one schema each. Old-format records and empty values are warnings, not errors, until the jobs that wrote them are cleaned up
    about = load(root, 'data', 'species', 'about.json')
    if about is not None:
        shape(about, 'about', 'data/species/about.json', errs)
        empty = sorted(k for k, v in about.items() if v == '')
        if empty: warns.append('data/species/about.json: %d empty sentence(s), first %r' % (len(empty), empty[0]))
    sums = load(root, 'data', 'text', 'summaries.json')
    if sums is not None: shape(sums, 'summaries', 'data/text/summaries.json', errs)
    names = load(root, 'jobs', 'names.json')
    if names is not None: shape(names, 'names', 'jobs/names.json', errs)
    sm = load(root, 'photos', 'species_missing.json')
    if sm is not None: shape(sm, 'species-missing', 'photos/species_missing.json', errs)
    pm = load(root, 'photos', 'places', 'missing.json')
    if pm is not None:
        old = sorted(k for k, v in pm.items() if isinstance(v, str))
        if old: warns.append('photos/places/missing.json: %d old-format record(s) (plain text), first %r; the daily photo run stamps them' % (len(old), old[0]))
        shape({k: v for k, v in pm.items() if not isinstance(v, str)}, 'photo-missing', 'photos/places/missing.json', errs)
        for k, v in pm.items():
            if isinstance(v, dict) and isinstance(v.get('checkedAt'), str) and isinstance(v.get('expiresAt'), str) and v['expiresAt'] <= v['checkedAt']:
                errs.append('photos/places/missing.json [%s]: expiresAt is not after checkedAt' % k)
    geo = load(root, 'data', 'geo', 'geo.json')
    if geo is not None:
        shape(geo, 'geo', 'data/geo/geo.json', errs)
        for kind in ('countries', 'states'):
            ids = [f.get('id') for f in geo.get(kind, []) if isinstance(f, dict)]
            for i in sorted({i for i in ids if ids.count(i) > 1}, key=str):
                if i == 'undefined': warns.append('data/geo/geo.json %s: %d features have the id "undefined" (a lost id from the source file; Kosovo, N. Cyprus, Somaliland)' % (kind, ids.count(i)))
                else: errs.append('data/geo/geo.json %s: id %r is repeated' % (kind, i))
    land = load(root, 'data', 'geo', 'land.json')
    if land is not None: shape(land, 'land', 'data/geo/land.json', errs)
    return errs, warns

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    errs, warns = check(root)
    for w in warns[:50]: print('warn ', w)
    for e in errs[:200]: print('ERROR', e)
    print('data format: %d problem(s), %d warning(s)' % (len(errs), len(warns))); sys.exit(1 if errs else 0)
