#!/usr/bin/env python3
"""Build Connected Earth.

  python3 build/build.py --all            build index.html (main), pilot/index.html and sw.js
  python3 build/build.py --out FILE       build the main app to FILE
  python3 build/build.py --pilot --out F  build with the auto-generated places included

Source: src/app.html (one file, with placeholders), data/*.json (hand-built places),
data-auto/*.json (auto-generated places, pilot only), node_modules (d3, maplibre-gl).
"""
import json, re, sys, os, hashlib, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import species
P = lambda *a: os.path.join(ROOT, *a)


def load_places(pilot):
    links = json.load(open(P('data', 'links.json')))
    order = list(links['order'])
    ecos = [json.load(open(P('data', i + '.json'))) for i in order]
    if pilot:
        for i in json.load(open(P('data-auto', 'order.json'))):
            ecos.append(json.load(open(P('data-auto', i + '.json'))))
    tab = species.table()
    ecos = [species.join(e, tab) for e in ecos]
    sp = P('pipeline', 'summaries.json'); sums = json.load(open(sp)) if os.path.exists(sp) else {}
    for e in ecos:
        if e.get('park') and not e.get('story'):
            for src in e.get('sources', []):
                m = re.search(r'wikipedia\.org/wiki/([^#?]+)', src.get('url', '')) if src.get('title', '').startswith('Wikipedia:') else None
                if m:
                    t = sums.get(urllib.parse.unquote(m.group(1)).replace('_', ' '))
                    if t: e['summary'] = t
                    break
    return links, ecos


def cross_ends(links):
    """Every (place, node) that a cross-place link mentions."""
    out = {}
    def walk(x):
        if isinstance(x, dict):
            if 'eco' in x and 'node' in x: out.setdefault(x['eco'], set()).add(x['node'])
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(links['cross'])
    return out


# Text that only shows once a place is open (sources, notes, the web's opening tip): kept in webs/<id>.json, not in the page.
HEAVY = ('sources', 'notes', 'tip')


def split(ecos, links):
    """Light copy of each place for the page, plus the heavy part (nodes, links, evidence) for webs/<id>.json.
    The species of every place are listed as numbers into one shared table (spt: [latin, usual name]); a species that a place names differently
    is [number, that name]. The page expands them back to [latin, name] at start."""
    import collections
    ends = cross_ends(links); light = []; webs = {}
    seen = collections.defaultdict(collections.Counter)
    for e in ecos:
        for n in e['nodes']:
            if not n.get('cat') and n.get('latin'): seen[n['latin']][n['name']] += 1
    spt = [[l, c.most_common(1)[0][0]] for l, c in sorted(seen.items())]; at = {l: i for i, (l, _) in enumerate(spt)}
    for e in ecos:
        nodes = e['nodes']
        s = [at[n['latin']] if n['name'] == spt[at[n['latin']]][1] else [at[n['latin']], n['name']] for n in nodes if not n.get('cat') and n.get('latin')]
        idx = {'nr': len(e['raw']), 'ns': sum(1 for n in nodes if not n.get('cat')), 'nl': sum(1 for r in e['raw'] if len(r) == 2 or r[2] == 's'), 's': s,
               'q': ' '.join(n['name'] for n in nodes if n.get('cat')),
               'cx': {n['id']: n['name'] for n in nodes if n['id'] in ends.get(e['id'], ())}}
        webs[e['id']] = {'nodes': nodes, 'raw': e['raw'], 'ev': e.get('ev', {})} | {k: e[k] for k in HEAVY if k in e}
        light.append({k: v for k, v in e.items() if k not in ('nodes', 'raw', 'ev') + HEAVY} | {'idx': idx})
    return light, webs, spt


def write_webs(webs, about):
    d = P('webs'); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith('.json') and f[:-5] not in webs and f != 'about.json': os.remove(os.path.join(d, f))
    for i, w in webs.items():
        open(os.path.join(d, i + '.json'), 'w').write(json.dumps(w, separators=(',', ':'), ensure_ascii=False))
    open(os.path.join(d, 'about.json'), 'w').write(json.dumps(about, separators=(',', ':'), ensure_ascii=False))


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


def build(pilot, out_path, write=False):
    links, ecos = load_places(pilot)
    tpl = open(P('src', 'app.html')).read()
    land = open(P('src', 'land.json')).read().strip()
    geo = json.load(open(P('src', 'geo.json')))
    errs = check(ecos, links, tpl, geo)
    if errs:
        print('\n'.join(errs)); sys.exit(1)
    tab = species.table()
    used = {n['latin'].lower() for e in ecos for n in e['nodes'] if n.get('latin')}
    about = {k: tab[k]['about'] for k in sorted(used) if k in tab and tab[k].get('about')}
    light, webs, spt = split(ecos, links)
    if write: write_webs(webs, about)
    data = json.dumps({'ecos': light, 'spt': spt, 'couple': links['couple'], 'src': links['src'], 'cross': links['cross']},
                      separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    # big data goes in as JSON.parse("...") rather than a JavaScript object literal: the browser parses JSON text about twice as fast
    lit = lambda text: "JSON.parse('" + text.replace('\\', '\\\\').replace("'", "\\'").replace('\u2028', '\\u2028').replace('\u2029', '\\u2029') + "')"   # single quotes: the JSON has many double quotes, which would each need a backslash
    out = tpl.replace('__LAND__', land).replace('__GEO__', lit(json.dumps(geo, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/'))).replace('__DATA__', lit(data))
    ml = P('node_modules', 'maplibre-gl', 'dist')
    out = out.replace('/*__MLCSS__*/', open(os.path.join(ml, 'maplibre-gl.css')).read())
    out = out.replace('/*__MLJS__*/', open(os.path.join(ml, 'maplibre-gl.js')).read())
    tag = '<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>'
    assert tag in out, 'd3 script tag not found in src/app.html'
    out = out.replace(tag, '<script>' + open(P('node_modules', 'd3', 'dist', 'd3.min.js')).read() + '</script>', 1)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    open(out_path, 'w').write(out)
    print('built %s: %d bytes, %d places, %d nodes' % (os.path.relpath(out_path, ROOT), len(out), len(ecos), sum(len(e['nodes']) for e in ecos)))
    return out


def build_id(html):
    return hashlib.md5(html.encode()).hexdigest()[:8]


def stamp_sw(main_html):
    bid = build_id(main_html)
    open(P('sw.js'), 'w').write(open(P('src', 'sw.template.js')).read().replace('__BUILD__', bid))
    print('sw.js stamped', bid)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--all' in a:
        main = build(False, P('index.html'))
        build(True, P('pilot', 'index.html'), write=True)
        stamp_sw(main)
    else:
        out = a[a.index('--out') + 1] if '--out' in a else P('dist', 'index.html')
        build('--pilot' in a, out)
