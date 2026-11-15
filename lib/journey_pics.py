#!/usr/bin/env python3
"""journey_pics.py: read the journey cover pictures by journey id (docs/DATA-PLAN.md, "Journey pictures: by journey id", phase 1; owner, 15 Nov).

`load(root)` returns {'pics': {id: row}, 'large': {id: file}, 'missing': {id: entry}, 'shape': 'journey'|'none'}. Until the migration (phase 3) none of `photos/journey_pictures.json` and friends exist:
then every part is empty and `shape` is 'none', so a consumer that reads this changes nothing (the covers still come from the title-keyed lists). A row is the credit row ({a, l, lu, p}) plus `f` (the
96 px file), `wiki` (the title it was found under), `page`, `u` (the source path the larger copy is made from) and `src`. `check(root)` is the hook the data validator calls: the writer's
file/list problems, plus a row for an id that is not a journey. Read only."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _read(root, *parts):
    p = os.path.join(root, *parts)
    if not os.path.exists(p): return None
    with open(p) as f: return json.load(f)


def new_shape(root='.'): return os.path.exists(os.path.join(root, 'photos', 'journey_pictures.json'))


def load(root='.'):
    if not new_shape(root): return {'pics': {}, 'large': {}, 'missing': {}, 'shape': 'none'}
    return {'pics': _read(root, 'photos', 'journey_pictures.json') or {}, 'large': _read(root, 'photos', 'journey_large.json') or {},
            'missing': _read(root, 'photos', 'journey_missing.json') or {}, 'shape': 'journey'}


def journey_ids(root='.'):
    """The journey ids: the files in data/journeys/ (build/journeydata.py)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build'))
    import journeydata as jd
    return sorted(c.get('id') for c in jd.journeys(root))


def check(root='.', ids=None):
    """Problems in the journey pictures; empty means consistent (and empty when the new files are absent). `ids` is the set of journey ids (default: read from data/journeys/)."""
    if not new_shape(root): return []
    from journey_photos import JourneyPhotos
    w = JourneyPhotos(root); errs = w.check(); known = set(ids if ids is not None else journey_ids(root))
    for name, d in (('journey_pictures.json', w.pics), ('journey_missing.json', w.miss_), ('journey_large.json', w.large), ('journey_tried.json', w.tried)):
        for jid in sorted(d):
            if jid not in known: errs.append('%s: %s is not a journey id' % (name, jid))
    return errs
