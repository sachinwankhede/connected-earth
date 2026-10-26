#!/usr/bin/env python3
"""Build Connected Earth.

  python3 build/build.py --all            build index.html (main), pilot/index.html and sw.js
  python3 build/build.py --out FILE       build the main app to FILE
  python3 build/build.py --pilot --out F  build with the auto-generated places included

Source: src/app.html (one file, with placeholders), data/*.json (hand-built places),
data-auto/*.json (auto-generated places, pilot only), node_modules (d3, maplibre-gl).
"""
import json, re, sys, os, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)


def load_places(pilot):
    links = json.load(open(P('data', 'links.json')))
    order = list(links['order'])
    ecos = [json.load(open(P('data', i + '.json'))) for i in order]
    if pilot:
        for i in json.load(open(P('data-auto', 'order.json'))):
            ecos.append(json.load(open(P('data-auto', i + '.json'))))
    return links, ecos


def check(ecos, links, tpl, geo):
    cnames = {c['name']: c['cont'] for c in geo['countries']}
    snames = {s['name'] for s in geo['states']}
    icons = set(re.findall(r"^\s{4}(\w+): ['\"]?<|^\s{4}(\w+): (?:QUAD|WINGS|CANID)", tpl, re.M))
    icons = {a or b for a, b in icons}
    icons |= set(re.findall(r"^\s{4}(\w+): (?:QUAD|WINGS|CANID)", tpl, re.M))
    errs = []
    seen_ids = set()
    for e in ecos:
        if e['id'] in seen_ids: errs.append(e['id'] + ': duplicate place id')
        seen_ids.add(e['id'])
        e.setdefault('countries', [e['country']])
        if e['country'] not in e['countries']: e['countries'].insert(0, e['country'])
        for c in e['countries']:
            if c not in cnames: errs.append(e['id'] + ': unknown country ' + c)
        e['conts'] = sorted({cnames.get(c) for c in e['countries'] if cnames.get(c)})
        if cnames.get(e.get('country')) != e.get('cont'): errs.append(e['id'] + ': country/continent not found or mismatched')
        for s in e.get('states', []):
            if s not in snames: errs.append(e['id'] + ': unknown state ' + s)
        ids = [n['id'] for n in e['nodes']]
        if len(ids) != len(set(ids)): errs.append(e['id'] + ': duplicate ids')
        S = set(ids)
        for n in e['nodes']:
            if n['tl'] not in (0, 1, 2, 3, 4): errs.append('%s/%s bad tl' % (e['id'], n['id']))
            if not (0 <= n['xh'] <= 1): errs.append('%s/%s bad xh' % (e['id'], n['id']))
            if n.get('ic') not in icons: errs.append('%s/%s unknown icon %s' % (e['id'], n['id'], n.get('ic')))
        seen = set()
        for r in e['raw']:
            if r[0] not in S or r[1] not in S: errs.append('%s: edge %s' % (e['id'], r))
            k = tuple(r[:2]) + ((r[2],) if len(r) > 2 else ())
            if k in seen: errs.append('%s: dup edge %s' % (e['id'], r))
            seen.add(k)
        if not e.get('sources'): print('note: no sources for', e['id'])
    byid = {e['id']: {n['id'] for n in e['nodes']} for e in ecos}
    for c in links['cross']:
        ends = c.get('ends') or [x for x in (c.get('from'), c.get('to')) if x]
        for x in ends:
            if x['node'] not in byid.get(x['eco'], ()): errs.append('cross %s bad end %s' % (c['id'], x))
    return errs


def build(pilot, out_path):
    links, ecos = load_places(pilot)
    tpl = open(P('src', 'app.html')).read()
    land = open(P('src', 'land.json')).read().strip()
    geo = json.load(open(P('src', 'geo.json')))
    errs = check(ecos, links, tpl, geo)
    if errs:
        print('\n'.join(errs)); sys.exit(1)
    data = json.dumps({'ecos': ecos, 'couple': links['couple'], 'src': links['src'], 'cross': links['cross']},
                      separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    out = tpl.replace('__LAND__', land).replace('__GEO__', json.dumps(geo, separators=(',', ':'))).replace('__DATA__', data)
    ml = P('node_modules', 'maplibre-gl', 'dist')
    out = out.replace('/*__MLCSS__*/', open(os.path.join(ml, 'maplibre-gl.css')).read())
    out = out.replace('/*__MLJS__*/', open(os.path.join(ml, 'maplibre-gl.js')).read())
    tag = '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>'
    assert tag in out, 'd3 script tag not found in src/app.html'
    out = out.replace(tag, '<script>' + open(P('node_modules', 'd3', 'dist', 'd3.min.js')).read() + '</script>', 1)
    out = out.replace('__BUILD__', build_id(out))
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    open(out_path, 'w').write(out)
    print('built %s: %d bytes, %d places, %d nodes' % (os.path.relpath(out_path, ROOT), len(out), len(ecos), sum(len(e['nodes']) for e in ecos)))
    return out


def build_id(html):
    return hashlib.md5(html.encode()).hexdigest()[:8]


def stamp_sw(main_html):
    bid = re.search(r'data-build="([0-9a-f]{8})"', main_html).group(1)
    open(P('sw.js'), 'w').write(open(P('src', 'sw.template.js')).read().replace('__BUILD__', bid))
    print('sw.js stamped', bid)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--all' in a:
        main = build(False, P('index.html'))
        build(True, P('pilot', 'index.html'))
        stamp_sw(main)
    else:
        out = a[a.index('--out') + 1] if '--out' in a else P('dist', 'index.html')
        build('--pilot' in a, out)
