#!/usr/bin/env python3
"""Build Connected Earth.

  python3 build/build.py --all            build index.html (main), pilot/index.html and sw.js
  python3 build/build.py --out FILE       build the main app to FILE
  python3 build/build.py --pilot --out F  build with the auto-generated places included

Source: src/app.html (one file, with placeholders), data/places/*.json (every place; those with "stage": "pilot" are auto-generated and only in the pilot build,
listed in data/order/ since #277, before that data/journeys/pilot-order.json), node_modules (d3, maplibre-gl).
"""
import json, re, sys, os, shutil, hashlib, urllib.parse, base64

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import species, journeydata, geoids
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib"))
from photo_registry import https_license
P = lambda *a: os.path.join(ROOT, *a)


def load_places(pilot):
    links = journeydata.links()
    order, pilot_order = journeydata.order()
    ecos = [json.load(open(P('data', 'places', i + '.json'))) for i in order]
    if pilot:
        for i in pilot_order:
            ecos.append(json.load(open(P('data', 'places', i + '.json'))))
    tab = species.table()
    bad = ['%s: %s' % (e['id'], ', '.join(map(repr, geoids.name_form(e)))) for e in ecos if geoids.name_form(e)]
    if bad: sys.exit('country and state must be ids from data/geo/geo.json (run python3 build/places_ids.py to rewrite names; an unknown name is a mistake):\n  ' + '\n  '.join(bad[:20]))
    ecos = [geoids.names(species.join(e, tab)) for e in ecos]
    sp = P('data', 'text', 'summaries.json'); sums = json.load(open(sp)) if os.path.exists(sp) else {}
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


# Text that only shows once a place is open (sources, notes, the web's opening tip): kept in api/<id>.json, not in the page.
HEAVY = ('sources', 'notes', 'tip', 'story', 'matters', 'summary')   # kept out of the page: they go to api/<id>.json and load when the place opens
UNUSED = ('link_ideas', 'stage')   # in the source data but never read by the app (stage only tells the build which places are pilot-only)


def split(ecos, links, phs=None, phm=None):
    """Light copy of each place for the page, plus the heavy part (nodes, links, evidence) for api/<id>.json.
    The species of every place are listed as numbers into one shared table (spt: [latin, usual name]); a species that a place names differently
    is [number, that name]. The page expands them back to [latin, name] at start."""
    import collections
    ends = cross_ends(links); light = []; webs = {}; sidx = {}; qs = {}
    seen = collections.defaultdict(collections.Counter)
    for e in ecos:
        for n in e['nodes']:
            if not n.get('cat') and n.get('latin'): seen[n['latin']][n['name']] += 1
    spt = [[l, c.most_common(1)[0][0]] for l, c in sorted(seen.items())]; at = {l: i for i, (l, _) in enumerate(spt)}
    for e in ecos:
        nodes = e['nodes']
        s = [at[n['latin']] if n['name'] == spt[at[n['latin']]][1] else [at[n['latin']], n['name']] for n in nodes if not n.get('cat') and n.get('latin')]
        idx = {'nr': len(e['raw']), 'ns': sum(1 for n in nodes if not n.get('cat')), 'nl': sum(1 for r in e['raw'] if len(r) == 2 or r[2] == 's'), 'cx': {n['id']: n['name'] for n in nodes if n['id'] in ends.get(e['id'], ())}}
        qs[e['id']] = ' '.join(n['name'] for n in nodes if n.get('cat'))   # words for search only, not in the page
        sidx[e['id']] = s   # the species lists are not in the page: the search index is built from them
        webs[e['id']] = {'nodes': nodes, 'raw': e['raw'], 'ev': e.get('ev', {})} | {k: e[k] for k in HEAVY if k in e}
        if phs is not None:   # the picture entries of this place's own species travel with the place, so opening it needs no list of every species
            keys = {k for n in nodes for k in (n.get('wiki'), n.get('canonicalWiki'), n.get('latin')) if k}
            webs[e['id']]['ph'] = {k: phs[k] for k in sorted(keys) if k in phs}
            webs[e['id']]['phm'] = {k: phm[k] for k in sorted(keys) if phm and k in phm}
        light.append({k: v for k, v in e.items() if k not in ('nodes', 'raw', 'ev') + HEAVY + UNUSED} | {'idx': idx})
    return light, webs, spt, sidx, qs


# The places the page lists, in two files (item #228, step 1). INDEX: what the map, the filters and the region lists read. CARDS: the rest (card and place-page text).
# A field not listed here goes to CARDS, unless it is listed in NOT_SHIPPED. The two files together hold the light place minus the not-shipped fields.
INDEX_FIELDS = ('id', 'short', 'lat', 'lon', 'kind', 'icon', 'level', 'auto', 'park', 'conts', 'countries', 'states')
# Fields the app never reads (item #313, step 1; checked by searching src/app.html): they stay in the source data, they are only left out of the files.
# tier, cont and country are the singular forms of what the app reads as conts and countries; side and ly are unused; idx.nl (the number of links of one kind) too.
NOT_SHIPPED = ('tier', 'cont', 'country', 'side', 'ly')
NOT_SHIPPED_IDX = ('nl',)


def shipped(e):
    """The light place as the files carry it: without the fields the app never reads."""
    return {k: ({a: b for a, b in v.items() if a not in NOT_SHIPPED_IDX} if k == 'idx' else v) for k, v in e.items() if k not in NOT_SHIPPED}


def split_places(light):
    """(index, cards): index is a list in page order; cards is {id: the other fields}. index[i] merged with cards[id] is shipped(the light place)."""
    light = [shipped(e) for e in light]
    index = [{k: e[k] for k in INDEX_FIELDS if k in e} for e in light]
    cards = {e['id']: {k: v for k, v in e.items() if k not in INDEX_FIELDS} for e in light}
    return index, cards


# Places by region (item #313, step 2): the same places as the split (index and cards), cut for loading one region at a time. The app does not read them yet.
# api/places/main/ (pilot: api/places/pilot/) holds: positions.json (what the world map draws: the places that are not "local"), positions-local.json,
# index-world.json + cards-world.json (those places in the two formats), index-<region>.json + cards-<region>.json (the local places of one region), counts.json.
# A local place's region is its US state, or its continent when it is not in a state of the US. A place is in exactly one file; a reader merges by id.
def slug(t):
    import unicodedata
    t = ''.join(c for c in unicodedata.normalize('NFKD', t.lower()) if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


def region_key(e):
    return slug(e['states'][0]) if 'United States of America' in e['countries'] and e.get('states') else slug(e['conts'][0])


def split_regions(light):
    """{file name: content} for api/places/<main|pilot>/. Counts are [not local, local] so the app can answer any combination of the local button, kind and parks."""
    index, cards = split_places(light)
    kinds = sorted({e['kind'] for e in index})
    loc = [e.get('level') == 'local' for e in index]
    files = {}
    # region membership: the distinct (continents, countries, states) of all places are a table g, and a row names its entry (the app answers inRegion from it);
    # the entry also holds the shard a local place lives in, so one lookup finds the file to fetch for its card
    mem = {}
    for e in index:
        mem.setdefault((tuple(e['conts']), tuple(e['countries']), tuple(e.get('states') or [])), len(mem))
    groups = [[list(c), list(k), list(st)] for c, k, st in mem]
    def pos(rows):
        return {'kinds': kinds, 'g': groups, 'p': [[e['id'], e['short'], e['lat'], e['lon'], kinds.index(e['kind']), (1 if e.get('auto') else 0) | (2 if e.get('park') else 0),
                                                    mem[(tuple(e['conts']), tuple(e['countries']), tuple(e.get('states') or []))], region_key(e) if e.get('level') == 'local' else 'world'] for e in rows]}
    world = [e for e, l in zip(index, loc) if not l]
    files['positions.json'] = pos(world)
    files['positions-local.json'] = pos([e for e, l in zip(index, loc) if l])
    files['index-world.json'] = world
    files['cards-world.json'] = {e['id']: cards[e['id']] for e in world}
    shards = {}
    for e, l in zip(index, loc):
        if l: shards.setdefault(region_key(e), []).append(e)
    for k, rows in sorted(shards.items()):
        files['index-%s.json' % k] = rows
        files['cards-%s.json' % k] = {e['id']: cards[e['id']] for e in rows}
    regions = {}
    def add(name, e, l):
        r = regions.setdefault(name, {'n': [0, 0], 'k': {}, 'p': [0, 0], 's': set()})
        r['n'][l] += 1; r['k'].setdefault(e['kind'], [0, 0])[l] += 1
        if e.get('park'): r['p'][l] += 1
        if l: r['s'].add(region_key(e))
    for e, l in zip(index, loc):
        l = int(l)
        add('w', e, l)
        for c in e['conts']: add('c:' + c, e, l)
        for c in e['countries']: add('k:' + c, e, l)
        for c in e.get('states') or []: add('s:' + c, e, l)
    for r in regions.values(): r['s'] = sorted(r['s'])
    locs = [e for e, l in zip(index, loc) if l]   # all the local places together: what the app fetches in one go when it needs them all (before it loads one region at a time)
    files['index-local.json'] = locs
    files['cards-local.json'] = {e['id']: cards[e['id']] for e in locs}
    files['counts.json'] = {'kinds': kinds, 'regions': regions}
    return files


def write_regions(light, pilot):
    d = os.path.join(P('api'), 'places', 'pilot' if pilot else 'main'); os.makedirs(d, exist_ok=True)
    files = split_regions(light)
    for f in os.listdir(d):
        if f not in files: os.remove(os.path.join(d, f))
    for f, obj in files.items():
        open(os.path.join(d, f), 'w').write(json.dumps(obj, separators=(',', ':'), ensure_ascii=False))


def write_journeys(data, pilot):
    """The journeys (and the couple and source settings) are their own file, fetched by the page's head with the world places (#377): api/journeys/main|pilot.json."""
    d = os.path.join(P('api'), 'journeys'); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'pilot.json' if pilot else 'main.json'), 'w').write(data)


def clear_old_places_files():
    """The first places files (api/places/index.json, cards.json and the -pilot pair) are not written any more: the app reads api/places/main|pilot/ (#313). Old copies are removed."""
    d = os.path.join(P('api'), 'places'); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if os.path.isfile(os.path.join(d, f)): os.remove(os.path.join(d, f))


# The search index (item #260, step 1): a ready-made word list, so a query is a lookup and not a scan of every place. The app does not read it yet.
# Place numbers are the places' positions in the page order of the same build. Words of a place: its name, place line, short name, kind, the common and Latin
# names of its species and its environment words (what the page's search string holds today). Accents and apostrophes are dropped; letters and digits only.
SEARCH_ROWS = 256   # places per rows file


def search_words(text):
    import unicodedata
    t = unicodedata.normalize('NFKD', text.lower().replace("'", '').replace('\u2019', ''))
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return {w for w in re.findall(r'[a-z0-9]+', t) if len(w) >= 2}


def search_bucket(word):
    return word[:2]   # words are letters and digits only, at least 2 long


def split_search(light, spt, sidx, qs):
    """(meta, buckets, rows). buckets: {two letters: {'w': sorted words, 'p': [place numbers, each list delta-coded]}}; rows: list of files, each a list of
    [id, name, place, lat, lon, continent, first state] for SEARCH_ROWS places in page order (enough to show a result and fly to it without any region loaded)."""
    posting = {}
    for n, e in enumerate(light):
        names = []
        for k in sidx[e['id']]:
            lat, common = (spt[k][0], spt[k][1]) if isinstance(k, int) else (spt[k[0]][0], k[1])
            names += [common, lat]
        for w in search_words(' '.join([e['name'], e['place'], e['short'], e.get('kind') or '', qs[e['id']]] + names)):
            posting.setdefault(w, []).append(n)
    buckets = {}
    for w in sorted(posting):
        b = buckets.setdefault(search_bucket(w), {'w': [], 'p': []})
        ns = posting[w]   # already ascending
        b['w'].append(w); b['p'].append([v - (ns[i - 1] if i else 0) for i, v in enumerate(ns)])
    flat = [[e['id'], e['name'], e['place'], round(e['lat'], 2), round(e['lon'], 2), e.get('cont') or '', (e.get('states') or [''])[0]] for e in light]
    rows = [flat[i:i + SEARCH_ROWS] for i in range(0, len(flat), SEARCH_ROWS)]
    meta = {'n': len(light), 'rows': SEARCH_ROWS, 'buckets': sorted(buckets)}
    return meta, buckets, rows


def write_search(light, spt, sidx, qs, pilot):
    """api/search/ (main) or api/search-pilot/: meta.json, w-<two letters>.json, rows-<n>.json. One build writes one folder; it replaces the folder's old files."""
    d = os.path.join(P('api'), 'search-pilot' if pilot else 'search'); os.makedirs(d, exist_ok=True)
    meta, buckets, rows = split_search(light, spt, sidx, qs)
    files = {'meta.json': meta} | {'w-%s.json' % k: v for k, v in buckets.items()} | {'rows-%d.json' % i: r for i, r in enumerate(rows)}
    for f in os.listdir(d):
        if f not in files: os.remove(os.path.join(d, f))
    for f, obj in files.items():
        open(os.path.join(d, f), 'w').write(json.dumps(obj, separators=(',', ':'), ensure_ascii=False))


# Species shared between places (items #252 and #253), worked out by the build so the app does not scan every place's species list.
# Same answers the app used to compute: RELATED (top 10 places by species in common, "Shares species with"), TIES (places that share a species found in
# 2 to 10 places, with the species names, for the map arcs) and SPECIES_PLACES (the places of each species found in 2 or more places, "Also found in").
RELATED_N = 10


def species_overlap(ecos):
    """-> (related, ties, species_places) for this set of places, in the order of the list. related[id] = [[id, species in common], ...] (at most 10, most first, ties in page order);
    ties[id] = [[other id, [species names]], ...] (most first, then by id); species_places[latin] = [place ids in page order]."""
    ids = [e['id'] for e in ecos]
    lists = {e['id']: [(n['latin'], n['name']) for n in e['nodes'] if not n.get('cat') and n.get('latin')] for e in ecos}
    by = {}
    for i in ids:
        for lat, name in lists[i]: by.setdefault(lat, []).append((i, name))
    related = {}
    for p in ids:
        c = {}
        for lat in {l for l, _ in lists[p]}:
            for o, _ in by[lat]:
                if o != p: c[o] = c.get(o, 0) + 1
        related[p] = [[o, c[o]] for o in sorted((o for o in ids if o in c), key=lambda o: -c[o])[:RELATED_N]]
    ties = {}
    for lat, g in by.items():
        if len(g) < 2 or len(g) > 10: continue
        for a, an in g:
            for b, _ in g:
                if a != b: ties.setdefault(a, {}).setdefault(b, []).append(an)
    ties = {a: [[b, t[b]] for b in sorted(t, key=lambda b: (-len(t[b]), b))] for a, t in ties.items()}
    sp = {}
    for lat, g in by.items():
        places = list(dict.fromkeys(i for i, _ in g))
        if len(places) >= 2: sp[lat] = places
    return related, ties, sp


TIES_N, TIES_NAMED = 16, 5   # places kept per place; the first TIES_NAMED also carry up to 3 species names (the map card lists 5, the arcs use up to 8 of those inside the view)


def split_ties(light, ties):
    """{file name: {place id: [[other id, species in common, [first 3 names]] x5, then other ids]}}: one file per region, the grouping of the region place files (world, a US state, another continent).
    A tap on a place asks for the file of its region once. Only the first TIES_NAMED entries carry the count and names; the others are the bare id, in order."""
    files = {}
    for e in light:
        t = ties.get(e['id'])
        if not t: continue
        k = region_key(e) if e.get('level') == 'local' else 'world'
        files.setdefault('%s.json' % k, {})[e['id']] = [[b, len(names), names[:3]] if i < TIES_NAMED else b for i, (b, names) in enumerate(t[:TIES_N])]
    return dict(sorted(files.items()))


def write_ties(light, ties, pilot):
    """api/ties/ (main) or api/ties-pilot/: one file per region. One build writes one folder."""
    d = os.path.join(P('api'), 'ties-pilot' if pilot else 'ties'); os.makedirs(d, exist_ok=True)
    files = split_ties(light, ties)
    for f in os.listdir(d):
        if f not in files: os.remove(os.path.join(d, f))
    for f, obj in files.items():
        open(os.path.join(d, f), 'w').write(json.dumps(obj, separators=(',', ':'), ensure_ascii=False))


def species_bucket(latin):
    """The file a species is in: its first two letters or digits (the Latin name lower-cased, anything else dropped), padded with _."""
    return (re.sub(r'[^a-z0-9]', '', latin.lower()) + '__')[:2]


def split_species_places(sp):
    files = {}
    for lat in sorted(sp): files.setdefault(species_bucket(lat), {})[lat] = sp[lat]
    return {'%s.json' % k: v for k, v in sorted(files.items())}


def write_species_places(sp, pilot):
    """api/species-places/ (main) or api/species-places-pilot/: one file per two-letter bucket. One build writes one folder."""
    d = os.path.join(P('api'), 'species-places-pilot' if pilot else 'species-places'); os.makedirs(d, exist_ok=True)
    files = split_species_places(sp)
    for f in os.listdir(d):
        if f not in files: os.remove(os.path.join(d, f))
    for f, obj in files.items():
        open(os.path.join(d, f), 'w').write(json.dumps(obj, separators=(',', ':'), ensure_ascii=False))


def add_overlap(webs, ecos, main_ids):
    """Put the related places into each place's own file. The files are shared by the main and the pilot page, so a main place keeps the main-set answer in 'rel'
    and, when the pilot set gives another answer or the place is pilot-only, the pilot one in 'relp'. (The ties are not here: a map tap needs them before the place
    file is open, so they are in api/ties/, see write_ties.)"""
    mrel, _, _ = species_overlap([e for e in ecos if e['id'] in main_ids])
    prel, _, _ = species_overlap(ecos)
    for e in ecos:
        i, w = e['id'], webs[e['id']]
        mine, theirs = mrel.get(i, []), prel.get(i, [])
        if i in main_ids and mine: w['rel'] = mine
        if i not in main_ids or mine != theirs:
            if theirs: w['relp'] = theirs
            elif i in main_ids: w['relp'] = []


def write_webs(webs, about, pictures=None):
    d = P('api'); os.makedirs(d, exist_ok=True)
    if os.path.isdir(P('webs')): shutil.rmtree(P('webs'))   # the folder used to be webs/ (#305): drop a stale copy so nothing serves the old path
    for f in os.listdir(d):
        if f.endswith('.json') and f[:-5] not in webs and f != 'species-pictures.json': os.remove(os.path.join(d, f))
    if pictures is not None:   # every hosted picture's entry and credit, for the journey and related-place views
        open(os.path.join(d, 'species-pictures.json'), 'w').write(json.dumps(pictures, separators=(',', ':'), ensure_ascii=False))
    for i, w in webs.items():
        open(os.path.join(d, i + '.json'), 'w').write(json.dumps(w, separators=(',', ':'), ensure_ascii=False))
    # one small file per species with a description, named by the species id (the app asks for api/species/<id>.json when its sheet opens)
    sd = os.path.join(d, 'species'); os.makedirs(sd, exist_ok=True); keep = set()
    for sid, text in about.items():
        open(os.path.join(sd, sid + '.json'), 'w').write(json.dumps({'t': text}, separators=(',', ':'), ensure_ascii=False)); keep.add(sid + '.json')
    for f in os.listdir(sd):
        if f not in keep: os.remove(os.path.join(sd, f))


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


def app_source():
    """src/app.html with each line `__INCLUDE:app/<file>__` replaced by that file under src/ (item #257: the app is kept as several
    files, joined here before anything else, so the built page is the same single file as before). One level only; the pieces are cut on line boundaries."""
    return re.sub(r'^__INCLUDE:([\w./-]+)__\n', lambda m: open(P('src', m.group(1))).read(), open(P('src', 'app.html')).read(), flags=re.M)


def build(pilot, out_path, write=False, places=False):
    links, ecos = load_places(pilot)
    tpl = app_source()
    land = open(P('data', 'geo', 'land.json')).read().strip()
    geo = json.load(open(P('data', 'geo', 'geo.json')))
    errs = check(ecos, links, tpl, geo)
    if errs:
        print('\n'.join(errs)); sys.exit(1)
    tab = species.table()
    used = {n['latin'].lower() for e in ecos for n in e['nodes'] if n.get('latin')}
    about = {tab[k]['sid']: tab[k]['about'] for k in sorted(used) if k in tab and tab[k].get('about')}
    for k in used:   # the app builds the file name from the Latin name, so an id that is not that name's slug must not carry a description
        if k in tab and tab[k].get('about') and tab[k]['sid'] != species.slug(k): raise SystemExit('species %r has a description but its id %r is not the slug of its name' % (k, tab[k]['sid']))
    phf, phmf = P('photos', 'species.json'), P('photos', 'species_metadata.json')
    src_ph = json.load(open(phf)) if os.path.exists(phf) else {}
    phm_all = json.load(open(phmf)) if os.path.exists(phmf) else {}
    for _c in phm_all.values():
        if isinstance(_c, dict) and _c.get('lu'): _c['lu'] = https_license(_c['lu'])   # credit links are always https
    hf = P('photos', 'species_hosted.json'); hosted = json.load(open(hf)) if os.path.exists(hf) else {}
    # the app reads our own hosted copies only: an entry is [hosted file name, Wikipedia page], and a species without a hosted copy has no entry (the placeholder shows)
    phs = {t: [hosted[t], src_ph[t][1]] for t in sorted(hosted) if t in src_ph}
    phm = {t: phm_all[t] for t in phs if t in phm_all}
    light, webs, spt, sidx, qs = split(ecos, links, phs, phm)
    # the journey views need the pictures of the journeys themselves (their cover species and the species at their ends); every place brings its own
    byid = {e['id']: {n['id']: n for n in e['nodes']} for e in ecos}; jt = set()
    for c in links['cross']:
        if c.get('imgwiki'): jt.add(c['imgwiki'])
    for eco_id, node_ids in cross_ends(links).items():
        for nid in node_ids:
            n = byid.get(eco_id, {}).get(nid)
            if n: jt |= {k for k in (n.get('wiki'), n.get('canonicalWiki'), n.get('latin')) if k}
    jp = {t: phs[t] for t in sorted(jt) if t in phs}
    if write: add_overlap(webs, ecos, set(links['order']))
    if write: write_webs(webs, about, {'ph': jp, 'phm': {t: phm[t] for t in jp if t in phm}})
    if places: clear_old_places_files(); write_regions(light, pilot); write_search(light, spt, sidx, qs, pilot); ov = species_overlap(ecos); write_species_places(ov[2], pilot); write_ties(light, ov[1], pilot)
    data = json.dumps({'couple': links['couple'], 'src': links['src'], 'cross': links['cross']},
                      separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
    if places: write_journeys(data, pilot)
    # big data goes in as JSON.parse("...") rather than a JavaScript object literal: the browser parses JSON text about twice as fast
    lit = lambda text: "JSON.parse('" + text.replace('\\', '\\\\').replace("'", "\\'").replace('\u2028', '\\u2028').replace('\u2029', '\\u2029') + "')"   # single quotes: the JSON has many double quotes, which would each need a backslash
    tpl = tpl.replace('__PLACES_SFX__', '-pilot' if pilot else '')
    tpl = tpl.replace('__PLACES_DIR__', 'pilot' if pilot else 'main').replace('__NLOCAL__', str(sum(1 for e in light if e.get('level') == 'local')))
    out = tpl.replace('<!--__BOOT__-->', boot_html(land)).replace('__LAND__', land).replace('__GEO__', lit(json.dumps({'countries': geo['countries']}, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')))
    out = out.replace('__PHOTO_REGISTRY__', open(P('src', 'photo-registry.js')).read())
    ml = P('node_modules', 'maplibre-gl', 'dist')
    out = out.replace('/*__MLCSS__*/', open(os.path.join(ml, 'maplibre-gl.css')).read())
    mlver = ml_version()
    open(P('geo-states.json'), 'w').write(json.dumps(geo['states'], separators=(',', ':'), ensure_ascii=False))   # US state outlines: their own file, fetched after the map
    shutil.copyfile(os.path.join(ml, 'maplibre-gl.js'), P('maplibre-gl-%s.js' % mlver))   # the map library is its own file (not part of the page): see the loader in src/app.html
    out = out.replace('__MLVER__', mlver)
    d3ver = json.load(open(P('node_modules', 'd3', 'package.json')))['version']
    shutil.copyfile(P('node_modules', 'd3', 'dist', 'd3.min.js'), P('d3-%s.js' % d3ver))   # the diagram library is its own file, loaded when a food web or journey map is first needed
    out = out.replace('__D3VER__', d3ver)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    open(out_path, 'w').write(out)
    print('built %s: %d bytes, %d places, %d nodes' % (os.path.relpath(out_path, ROOT), len(out), len(ecos), sum(len(e['nodes']) for e in ecos)))
    return out


def boot_html(land_json=None):
    """The start screen shown while the page's scripts and the map download: the app logo, big, and the name. Removed (fade) when the map has drawn."""
    icon = base64.b64encode(open(P('icon-192.png'), 'rb').read()).decode()
    return ('<div id="boot" aria-hidden="true"><div class="bt"><img src="data:image/png;base64,' + icon + '" alt="" width="160" height="160">'
            '<b>Connected Earth</b><span>See how nature is connected</span><i class="bar"></i></div></div>')


def ml_version():
    return json.load(open(P('node_modules', 'maplibre-gl', 'package.json')))['version']


def build_id(html):
    return hashlib.md5(html.encode()).hexdigest()[:8]


def stamp_sw(main_html):
    bid = build_id(main_html)
    open(P('sw.js'), 'w').write(open(P('src', 'sw.template.js')).read().replace('__BUILD__', bid).replace('__MLVER__', ml_version()))
    print('sw.js stamped', bid)


if __name__ == '__main__':
    a = sys.argv[1:]
    if '--all' in a:
        main = build(False, P('index.html'), places=True)
        build(True, P('pilot', 'index.html'), write=True, places=True)
        stamp_sw(main)
    else:
        out = a[a.index('--out') + 1] if '--out' in a else P('dist', 'index.html')
        build('--pilot' in a, out)
