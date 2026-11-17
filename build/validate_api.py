#!/usr/bin/env python3
"""validate_api.py [api-dir]: the shapes of the built api/ files the app reads (#725). The build writes them, the app reads them under fixed field names; a renamed or retyped field fails here, before merge,
with the file and the field in the message. Search: meta.json, rows-N.json, s-XX.json (suggestions); places: cards-<state>.json; species: <latin>.json. Usage: python3 build/validate_api.py [api]  (default ./api)"""
import glob, json, os, sys
from jsonschema import Draft202012Validator as V
S = lambda **kw: dict(type='string', **kw)
I = dict(type='integer')
SID = S(pattern='^[a-z0-9]+(-[a-z0-9]+)*$')   # a species id: species.slug of the Latin name
# One species row the app lists (#1008): [usual name, places, hosted picture file or 0, species id]
SROW = dict(type='array', minItems=4, maxItems=4, prefixItems=[S(), I, dict(type=['string', 'integer']), SID])
SROWS = dict(type='array', items=SROW)
SCHEMAS = {
    'search/meta.json': dict(type='object', required=['n', 'rows', 'buckets', 'sug'], properties=dict(n=I, rows=I, buckets=dict(type='array', items=S()), sug=dict(type='array', items=S()))),
    'search/rows-*.json': dict(type='array', items=S()),
    'search/s-*.json': dict(type='object', required=['p', 's'], properties=dict(
        p=dict(type='array', items=dict(type='array', minItems=2, maxItems=2, items=S())),
        s=dict(type='array', items=dict(type='array', minItems=5, maxItems=6, prefixItems=[S(), S(), I, dict(type=['string', 'integer']), S()], items=S())))),
    'places/main/cards-*.json': dict(type='object', additionalProperties=dict(type='object', required=['name', 'place', 'blurb', 'idx'], properties=dict(name=S(), place=S(), blurb=S(), idx=dict(type='object')), **{'not': dict(required=['imgwiki'])})),
    'species/*.json': dict(type='object', required=['l', 'n', 'tl', 'ic'], properties=dict(l=S(), n=S(), tl=I, ic=S(), ea=SROWS, eb=SROWS, rl=SROWS)),
    'species-tab/top.json': SROWS, 'species-tab/g-*.json': SROWS, 'species-tab-pilot/top.json': SROWS, 'species-tab-pilot/g-*.json': SROWS,
    'journeys/main.json': dict(type='object', required=['couple', 'src', 'cross'], properties=dict(couple=dict(type='number'), src=dict(type='object'), cross=dict(type='array', items=dict(type='object', required=['id', 'type', 'title', 'text'], properties=dict(id=S(), type=S(), title=S(), text=S()))))),
}
def nodes_missing_ids(d):
    """The ids of the nodes of one place file that lack their id: a species node (a Latin name, no cat) needs `sid`, a concept node (cat and a wiki title) needs `nid` (#1008). The app works out no id from a name, so a node without one has no picture or link."""
    bad = []
    for n in d.get('nodes') or []:
        if not isinstance(n, dict): continue
        if (n.get('latin') and not n.get('cat') and not n.get('sid')) or (n.get('cat') and n.get('wiki') and not n.get('nid')): bad.append(str(n.get('id')))
    return bad
def journey_ends_missing(root):
    """Journey ends whose `node` is not a node of that place's food web (#1013): the app finds the node by id and a missing one breaks the journey."""
    f = os.path.join(root, 'journeys', 'main.json'); bad = []; cache = {}
    if not os.path.exists(f): return bad
    for c in json.load(open(f, encoding='utf-8')).get('cross') or []:
        for en in list(c.get('ends') or []) + [c.get('from'), c.get('to')]:
            if not isinstance(en, dict): continue
            eco = en.get('eco'); p = os.path.join(root, '%s.json' % eco)
            if eco not in cache: cache[eco] = {n.get('id') for n in json.load(open(p, encoding='utf-8')).get('nodes', [])} if os.path.exists(p) else None
            if cache[eco] is None or en.get('node') not in cache[eco]: bad.append('%s: %s/%s' % (c.get('id'), eco, en.get('node')))
    return bad
def main(root):
    errs = []; files = 0
    bad = journey_ends_missing(root)
    if bad: errs.append('journeys/main.json: %d journey end(s) name a node that is not in that place: %s' % (len(bad), '; '.join(bad[:5])))
    for f in sorted(glob.glob(os.path.join(root, '*.json'))):
        try: d = json.load(open(f, encoding='utf-8'))
        except ValueError: continue   # not a place file; the schemas below report a bad file in their own folders
        if isinstance(d, dict) and isinstance(d.get('nodes'), list):
            files += 1; bad = nodes_missing_ids(d)
            if bad: errs.append('%s: %d node(s) without their sid/nid (#1008): %s' % (os.path.relpath(f, root), len(bad), ', '.join(bad[:5])))
    for pat, schema in SCHEMAS.items():
        v = V(schema)
        for f in sorted(glob.glob(os.path.join(root, pat))):
            files += 1
            try: d = json.load(open(f, encoding='utf-8'))
            except ValueError as e: errs.append('%s: not JSON (%s)' % (os.path.relpath(f, root), e)); continue
            for e in sorted(v.iter_errors(d), key=lambda e: list(e.absolute_path))[:3]:
                errs.append('%s: %s: %s' % (os.path.relpath(f, root), '/'.join(str(p) for p in e.absolute_path) or '(top)', e.message[:140]))
    if not files: errs.append('no api files under %s: build first' % root)
    if errs: print('\n'.join(errs[:40])); sys.exit(1)
    print('api shapes ok: %d files' % files)
if __name__ == '__main__': main(sys.argv[1] if len(sys.argv) > 1 else 'api')
