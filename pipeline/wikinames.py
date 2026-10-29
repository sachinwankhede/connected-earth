#!/usr/bin/env python3
"""wikinames.py: give each park of one state its real Wikipedia name.

  python3 pipeline/wikinames.py IL            fix names and Wikipedia source links for the IL parks in data-auto
  python3 pipeline/wikinames.py --selftest    check the matching rules without the web

The park list from PAD-US sometimes has typos ("Horshoe Lake", "Morraine Hills"), and the Wikipedia source link was built
from that name, so it could point at a page that does not exist. For each park this finds the Wikipedia article in the same
state, close in name and within 80 km of the park, then sets name, short and the Wikipedia source from that article's title.
No close match: the park is left as it is and listed in the report. Ids and file names never change.
Needs the web (Wikipedia), so it runs in a GitHub job. The report goes to names_report.md for the pull request."""
import difflib, json, math, os, re, sys, urllib.parse
here = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(here)
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, here)
wm = None
MAX_KM = 80; MIN_SIM = 0.88
TYPE = re.compile(r'\b(park|recreation area|historic site|historical site|natural area|conservation area|preserve|forest|fish and wildlife area|wildlife area|wildlife refuge|grassland)\b', re.I)

def base(title): return re.sub(r'\s*\([^)]*\)\s*$', '', title).strip()
def core(s):
    s = base(s).lower().replace('&', 'and').replace("'", '').replace('’', '')
    s = re.split(r'\b(?:state|national)\b', s)[0]
    s = re.sub(r'\b(park|recreation area|historic site|historical site|natural area)\b\s*$', '', s)
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()
def km(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))

def choose(cur, state, lat, lon, pages):
    """pages: [{title, extract, coords:[lat, lon] or None}] in search order. Returns (page, note) or (None, why).
    Only titles with a park word are accepted ("Cahokia", "Chain O'Lakes" alone are a site and a lake, not the park), and the name must be close.
"""
    best = None; near = None
    for pg in pages:
        t = base(pg['title']); c = pg.get('coords')
        if state.lower() not in (pg['title'] + ' ' + (pg.get('extract') or '')).lower(): continue
        if c and km(lat, lon, c[0], c[1]) > MAX_KM: continue
        if not TYPE.search(t): continue
        a, b = core(cur), core(t)
        sim = difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0
        if near is None or sim > near[0]: near = (sim, pg['title'])
        if sim >= MIN_SIM and (best is None or sim > best[0]): best = (sim, pg)
    if not best: return None, 'no close match in %s%s' % (state, (' (closest: %s, %.2f)' % (near[1], near[0])) if near else ' (no park pages found; search %s, list %s titles, list pages %s)' % (LAST.get('search'), LAST.get('listed'), LAST.get('listpages')))
    return best[1], ('title has a qualifier: ' + best[1]['title']) if base(best[1]['title']) != best[1]['title'] else ''

def _pages(q, redirects=False):
    d = wm.get('https://en.wikipedia.org/w/api.php?action=query&format=json%s&prop=extracts|coordinates&exintro=1&explaintext=1&exchars=400&exlimit=max&colimit=max&coprimary=primary&%s' % ('&redirects=1' if redirects else '', q))
    ps = sorted(((d or {}).get('query', {}).get('pages', {})).values(), key=lambda p: p.get('index', 99))
    return [dict(title=p['title'], extract=p.get('extract', ''), coords=[p['coordinates'][0]['lat'], p['coordinates'][0]['lon']] if p.get('coordinates') else None) for p in ps if 'missing' not in p]

_list = {}
def state_list(state):
    """Titles linked from Wikipedia's list of the state's parks (several spellings of that page's name are tried)."""
    if state in _list: return _list[state]
    out = []
    for t in ('List of %s state parks', 'List of state parks of %s', 'List of state parks in %s', 'List of %s state parks and recreation areas'):
        cont = ''
        while True:
            d = wm.get('https://en.wikipedia.org/w/api.php?action=query&format=json&prop=links&pllimit=max&plnamespace=0&titles=%s%s' % (urllib.parse.quote(t % state), cont))
            for pg in ((d or {}).get('query', {}).get('pages', {})).values(): out += [l['title'] for l in pg.get('links', [])]
            c = (d or {}).get('continue', {}).get('plcontinue')
            if not c: break
            cont = '&plcontinue=' + urllib.parse.quote(c)
    _list[state] = list(dict.fromkeys(out)); return _list[state]

LAST = {}
def lookup(name, state):
    pages = _pages('generator=search&gsrlimit=6&gsrsearch=%s' % urllib.parse.quote(name + ' ' + state))
    lst = state_list(state)
    near = sorted(lst, key=lambda t: -difflib.SequenceMatcher(None, core(name), core(t)).ratio())[:4]
    extra = _pages('titles=' + urllib.parse.quote('|'.join(near)), True) if near else []
    LAST.update(search=len(pages), listed=len(lst), listpages=len(extra))
    return pages + extra

def short(n): return re.sub(r' (State )?(Park|Recreation Area)$', '', n)[:20]
def wurl(t): return 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(t.replace(' ', '_'), safe="_(),'")

def selftest():
    P = lambda t, e='In Illinois.', c=None: dict(title=t, extract=e, coords=c)
    ok = []
    def t(label, got, want): ok.append((label, got == want)); print(('ok  ' if got == want else 'FAIL'), label, '' if got == want else (got, want))
    pg, _ = choose('Horshoe Lake State Park', 'Illinois', 38.7, -90.0, [P('Horseshoe Lake State Park (Madison County, Illinois)', c=[38.7, -90.0])]); t('typo fixed', pg and base(pg['title']), 'Horseshoe Lake State Park')
    pg, _ = choose('Horshoe Lake State Park', 'Illinois', 37.1, -89.3, [P('Horseshoe Lake State Park (Madison County, Illinois)', c=[38.7, -90.0])]); t('wrong county rejected by distance', pg, None)
    pg, _ = choose('Morraine Hills State Park', 'Illinois', 42.3, -88.2, [P('Moraine Hills State Park')]); t('Morraine', pg and pg['title'], 'Moraine Hills State Park')
    pg, _ = choose('Illini State Park', 'Illinois', 41.3, -88.9, [P('Illini'), P('Illini State Park')]); t('tribe page skipped', pg and pg['title'], 'Illini State Park')
    pg, _ = choose('Rock Cut State Park', 'Illinois', 42.3, -89.0, [P('Rock Cut State Park, Wisconsin', e='In Wisconsin.')]); t('other state rejected', pg, None)
    pg, _ = choose('Silver Springs', 'Illinois', 41.6, -88.4, [P('Silver Springs State Fish and Wildlife Area')]); t('short name', pg and pg['title'], 'Silver Springs State Fish and Wildlife Area')
    pg, _ = choose('Pool No. 26 - Stump Lake', 'Illinois', 39.0, -90.6, [P('Stump Lake Park')]); t('no close match left alone', pg, None)
    pg, _ = choose('Cahokia Mounds State Historical Site', 'Illinois', 38.65, -90.06, [P('Cahokia Mounds State Historic Site')]); t('historical vs historic', pg and pg['title'], 'Cahokia Mounds State Historic Site')
    pg, _ = choose('Cahokia Mounds State Historical Site', 'Illinois', 38.65, -90.06, [P('Cahokia', c=[38.65, -90.06])]); t('a site named in part is not the park', pg, None)
    pg, _ = choose("Chain O'Lakes State Park", 'Illinois', 42.4, -88.2, [P("Chain O'Lakes", c=[42.4, -88.2]), P("Chain O'Lakes State Park (Illinois)", c=[42.4, -88.2])]); t('the lake is not the park', pg and pg['title'], "Chain O'Lakes State Park (Illinois)")
    pg, _ = choose('Lincolns New Salem State Park', 'Illinois', 40.02, -89.84, [P("Lincoln's New Salem State Historic Site", c=[40.02, -89.84])]); t('apostrophe', pg and pg['title'], "Lincoln's New Salem State Historic Site")
    pg, note = choose('Pool No. 26 - Stump Lake', 'Illinois', 39.0, -90.6, [P('Stump Lake Park')]); t('report names the closest page', 'closest: Stump Lake Park' in note, True)
    if not all(x[1] for x in ok): sys.exit(1)

if __name__ == '__main__':
    if '--selftest' in sys.argv: selftest(); sys.exit(0)
    import state, wm
    st = sys.argv[1].upper(); full = state.STATES[st]; d = os.path.join(ROOT, 'data-auto'); rows = []; changed = 0
    for f in sorted(os.listdir(d)):
        if not (f.startswith(st.lower()) and f.endswith('.json')) or f == 'order.json': continue
        e = json.load(open(os.path.join(d, f)))
        if not e.get('park') or not e.get('nodes'): continue
        pg, note = choose(e['name'], full, e['lat'], e['lon'], lookup(e['name'], full))
        if not pg: rows.append('| %s | (unchanged) | %s |' % (e['name'], note)); continue
        new = base(pg['title']); src = 'Wikipedia: ' + new; url = wurl(pg['title']); old = e['name']; dirty = False
        if new != old: e['name'] = new; e['short'] = short(new); dirty = True
        for s in e.get('sources', []):
            if s.get('title', '').startswith('Wikipedia:') and (s['title'] != src or s.get('url') != url): s['title'] = src; s['url'] = url; dirty = True
        if dirty:
            json.dump(e, open(os.path.join(d, f), 'w'), ensure_ascii=False); changed += 1
            rows.append('| %s | %s | %s |' % (old, new if new != old else '(same name, source link fixed)', note))
        else: rows.append('| %s | (already right) | |' % old)
    rep = ['# Park names for %s: %d changed' % (full, changed), '', '| Was | Now | Note |', '|---|---|---|'] + rows
    open(os.path.join(ROOT, 'names_report.md'), 'w').write('\n'.join(rep) + '\n'); print('\n'.join(rep))
