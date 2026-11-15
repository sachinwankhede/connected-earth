#!/usr/bin/env python3
"""place_sources.py: the SOURCES of place pictures, in one module (docs/DATA-PLAN.md step 4; #887).
jobs/placepictures.py decides the order, the holds, the author rule and the writing; THIS module knows where a picture can come from. Each source is one function
`find_<name>(todo)` that takes the places to try and yields (place, Res), plus one line in SOURCES: (name, find, which places it applies to, retry days; None = the missing record's own expiry).
To add a source, write its function here and add its line to SOURCES (and a stub for its network in tests/jobs/place_sources_test.py, which holds every source to the same contract:
a found Res carries a row with author, licence, licence link and file page, and a downloaded picture; placepictures then refuses a CC BY / BY-SA row with no author, whatever the source).
The rules below were the five old jobs' own functions (jobs/photos.py, commonsplacephotos.py, commonsnearby.py, commonscategory.py, openverseplaces.py); they were MOVED here unchanged and those job
files import them back, so their own tests still hold. Network goes through lib/wm.py (hosts listed in lib/allowed_sources.json, enforced by lib/fetch.py); no host is added."""
import collections, datetime, glob, io, json, os, re, shutil, sys, tempfile, unicodedata, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import wm, photo_registry as pr
from photo_registry import ALLOWED_IMAGE_HOSTS, safe_https
import author_lookup as al, wikipedia_photo as ph, commons_api as cs, openverse_api as o   # nothing here imports from jobs/

RETRY_DAYS = 90   # every source but wikipedia: tried again this long after its date in photos/places_tried.json
Res = collections.namedtuple('Res', 'kind entry jpg why status note', defaults=(None, None, '', 'nophoto', ''))   # kind: found | miss | retry

def now_iso(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

# --- Commons: Wikidata image property (from commonsplacephotos.py)
# photos.py's not-a-photo name filter without its bare "arrowhead" (the National Park Service logo, which also says "logo" or is an .svg): a place such as Arrowhead State Park has a real photo with that word in its file name
NOTPHOTO = re.compile(ph.NOTPHOTO.pattern.replace('arrowhead|', '', 1), re.I)

def pick(names, info):
    """The first of the (at most two) candidate files that is an open-licence JPEG photo: (file name, licence, author, licence url, thumbnail url) or None."""
    for n in names[:2]:
        lic, author, lu, thumb, mime = info.get(n.replace(' ', '_'), ('', '', '', '', ''))
        if cs.is_photo_type(mime) and cs.open_licence(lic) and thumb and not NOTPHOTO.search(n) and safe_https(thumb.split('?')[0], ALLOWED_IMAGE_HOSTS):
            return n.replace(' ', '_'), lic, author, lu, thumb
    return None

def entry(place_id, page, found, now):
    """The places.json row photos.py writes; migrate adds the measured fields."""
    fn, lic, author, lu, _ = found
    return dict(f=place_id + '.jpg', a=author or 'Unknown author', l=lic or 'See file page', lu=lu,
                p='https://commons.wikimedia.org/wiki/File:' + urllib.parse.quote(fn),
                w='https://en.wikipedia.org/wiki/' + urllib.parse.quote(page.replace(' ', '_')), checkedAt=now, fetchedAt=now)


# --- Commons: files geotagged near the place (from commonsnearby.py)
RADIUS = 1500
# file names about a building, business, road, town or sign: a photo of a hotel, a highway or the next village near the place is not a photo of the place (whole words only)
BUILDING = re.compile(r'(?<![a-z])(hotel|motel|casino|resort|church|cathedral|restaurant|cafe|diner|school|hospital|mall|store|shop|supermarket|apartments?|museum|station|airport|office|factory|plant|bank|inn|interstate|route|highway|freeway|boulevard|avenue|road|street|village|temple|capitol|lodge|damage|sign)s?(?![a-z])', re.I)
GENERIC = set('national state park parks lake lakes river rivers mountain mountains mount forest preserve reserve refuge wildlife monument recreation area '
              'historic site seashore lakeshore island islands bay beach beaches creek canyon valley falls trail trails the of and de la los las del'.split())

def words(s):
    """Distinctive lower-case words (4+ letters, ASCII-folded, not generic) of a name or file name."""
    import unicodedata
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z]{4,}', s) if w not in GENERIC}

def place_info(data_dir):
    """{imgwiki title: (id, name, lat, lon)} of the first place (by id) using each title."""
    out = {}
    for f in sorted(glob.glob(data_dir + '/*.json')):
        if f.endswith(('order.json', 'links.json')): continue
        e = json.load(open(f)); t = e.get('imgwiki')
        if t and t not in out and 'lat' in e and 'lon' in e: out[t] = (e['id'], e.get('name', t), e['lat'], e['lon'])
    return out

def nearby(lat, lon):
    """Commons file names (with underscores), nearest first, geotagged within RADIUS metres."""
    q = ('https://commons.wikimedia.org/w/api.php?action=query&list=geosearch&gsnamespace=6&gslimit=30&format=json&gsradius=%d&gscoord=%s%%7C%s'
         % (RADIUS, lat, lon))
    j = wm.get(q) or {}
    return [(g['title'][5:].replace(' ', '_'), g.get('dist', 0)) for g in (j.get('query') or {}).get('geosearch', [])]

def match(name, title, cands, info):
    """(pick tuple, distance) for the nearest candidate that passes the same checks as commonsplacephotos.pick and shares a distinctive word with the place name; else None."""
    want = words(name) | words(title); need = (len(want) + 1) // 2   # at least half of the place's distinctive words must appear in the file name
    for fn, dist in cands:
        if len(want & words(fn)) < need or BUILDING.search(fn): continue
        got = pick([fn], info)
        if got: return got, dist
    return None


# --- Commons: the place's own category (from commonscategory.py)
def categories(name):
    """Commons category titles (without the 'Category:' prefix), best search hit first."""
    q = ('https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=14&srlimit=5&format=json&srsearch=%s' % urllib.parse.quote(name))
    j = wm.get(q) or {}
    return [h['title'][9:] for h in (j.get('query') or {}).get('search', []) if h.get('title', '').startswith('Category:')]

def category_files(cat):
    """File names (with underscores) in a category, up to 50."""
    q = ('https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtype=file&cmlimit=50&format=json&cmtitle=%s' % urllib.parse.quote('Category:' + cat))
    j = wm.get(q) or {}
    return [m['title'][5:].replace(' ', '_') for m in (j.get('query') or {}).get('categorymembers', [])]

KIND = {'state', 'national', 'county', 'city', 'regional', 'provincial'}   # who runs the place: a state park is not a national preserve
# file names that are not a picture of the place: scientific figures, newspaper clippings, portraits
NOTPLACE = re.compile(r'(?<![a-z])(figure|fig|diagram|chart|poster|newspaper|courier|bulletin|portrait|congressman|senator|surname)s?(?![a-z])', re.I)

def toks(s):
    """Like words but from 3 letters up, so a short extra word such as 'Oak' in 'White Oak Lake' still counts as an extra word."""
    import unicodedata, re
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z]{3,}', s) if w not in GENERIC and w not in KIND}

def good_category(cats, name, region=''):
    """The first category that is the place itself, else None. After dropping a bracketed note such as "(California)", the category title must
    (1) add no distinctive word the place name lacks ("Baker River, Washington State" is not "Baker Creek State Park"),
    (2) share at least half of the place's distinctive words,
    (3) name no building or business,
    (4) agree on who runs the place (state, national, county ...), and
    (5) when the place name has no word like Park, Lake or Reserve of its own (a bare "Riverside" or "Pickett"), contain one,
    (6) keep the words they share with the place name in the same order ("Lake White" is not "White Lake"), and
    (7) when the category has a bracketed note ("(California)", "(Black Sand Basin, Yellowstone National Park)"), every word of it must appear in the place's own
        region text from the data ("Rhode Island, USA"), so the Santa Barbara East Beach is not the Rhode Island one."""
    import re
    want = words(name)
    if not want: return None
    kind = {w for w in re.findall(r'[a-z]+', name.lower()) if w in KIND}; has_type = any(w in GENERIC and w not in KIND for w in re.findall(r'[a-z]+', name.lower()))
    for cat in cats:
        base = re.sub(r'\s*\([^)]*\)', '', cat); got = words(base)
        notes = ' '.join(re.findall(r'\(([^)]*)\)', cat)); reg = set(re.findall(r'[a-z]{3,}', region.lower()))
        low = re.findall(r'[a-z]+', base.lower())
        if not got or toks(base) - toks(name) or len(got) * 2 < len(want) or BUILDING.search(cat): continue
        if kind and kind != {w for w in low if w in KIND}: continue
        if notes and not set(re.findall(r'[a-z]{3,}', notes.lower())) <= reg: continue
        mine = [w for w in re.findall(r'[a-z]{3,}', name.lower())]; theirs = [w for w in re.findall(r'[a-z]{3,}', base.lower())]
        if [w for w in theirs if w in mine] != [w for w in mine if w in theirs]: continue
        if not has_type and not any(w in GENERIC and w not in KIND for w in low): continue
        return cat
    return None

US_STATES = {'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA', 'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
             'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA', 'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
             'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO', 'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH',
             'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH', 'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA',
             'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT', 'virginia': 'VA', 'washington': 'WA',
             'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY'}
OTHER_COUNTRIES = ('canada', 'mexico', 'australia', 'england', 'scotland', 'wales', 'ireland', 'france', 'germany', 'india')

def names_another_place(fn, region):
    """True when a file name names a US state (written out, or as a capital two-letter code) or a country other than the place's own region ("Alabama, USA"),
    for example Cedar_Key_FL_Shell_Mound_Park for an Alabama place or US-Canada_border_at_Crawford_State_Park for a Kansas one. An empty region checks nothing."""
    import re
    if not region: return False
    text = ' '.join(re.findall(r'[A-Za-z]+', fn)).lower(); own = region.lower()
    mine = {s for s in US_STATES if re.search(r'(?<![a-z])%s(?![a-z])' % s, own)}
    for s, ab in US_STATES.items():
        if s in mine: continue
        if re.search(r'(?<![a-z])%s(?![a-z])' % s, text) or re.search(r'(?<![A-Za-z])%s(?![A-Za-z])' % ab, ' '.join(re.findall(r'[A-Za-z]+', fn))): return True
    return any(re.search(r'(?<![a-z])%s(?![a-z])' % w, text) and w not in own for w in OTHER_COUNTRIES)

def choose(files, want, info, kind=(), region=''):
    """The first acceptable file, files naming a distinctive word of the place first; None if no file passes."""
    ordered = [f for f in files if want & words(f)] + [f for f in files if not want & words(f)]
    for fn in ordered:
        if BUILDING.search(fn) or NOTPLACE.search(fn) or names_another_place(fn, region): continue
        fk = {w for w in re.findall(r'[a-z]+', fn.lower()) if w in KIND}
        if kind and fk and fk != set(kind): continue   # a file about a county park is not a picture of a state park
        got = pick([fn], info)
        if got: return got
    return None


# --- Openverse (from openverseplaces.py)
TRY_FILES = 4; MIN_SIDE = 200; WIDTH = 330; MAX_BYTES = 8_000_000
def state_of_place(place):
    """The US state name of a place whose `place` field is "<State>, USA", else ''."""
    p = (place or '').strip()
    return p.split(',')[0].strip() if p.endswith(', USA') else ''
def names_place(r, name, state):
    """True when the result's title or tags contain the whole place name and the state name."""
    n, s = o.norm(name), o.norm(state)
    if not n or not s: return False
    blob = [o.norm(r.get('title'))] + [o.norm(t.get('name')) for t in r.get('tags') or []]
    return any(n in b for b in blob) and any(s in b for b in blob)
def openverse_candidates(results, name, state):
    """[(id, thumbnail link, creator, short licence, licence link)] in Openverse's order, only what may be used for this place."""
    out = []
    for r in results or []:
        rid = r.get('id') or ''
        if not re.fullmatch(r'[0-9a-f-]{36}', rid) or o.unwanted(r) or NOTPHOTO.search(r.get('title') or '') or not names_place(r, name, state): continue
        lic = o.licence_of(r); au = ' '.join(str(r.get('creator') or '').split())
        if not lic or not au or au.lower() in ('unknown', 'anonymous', 'n/a', 'none'): continue
        out.append((rid, o.API + rid + '/thumb/', au, lic[0], lic[1]))
    return out
def reject_reasons(results, name, state):
    """{reason: count} for the results candidates() refuses, plus up to 3 example titles that failed only on the place or state words, so a dry run shows why a place found nothing."""
    out = {}; ex = []
    for r in results or []:
        if o.unwanted(r) or NOTPHOTO.search(r.get('title') or ''): k = 'not a photo or unwanted source'
        elif not o.licence_of(r): k = 'licence'
        elif not ' '.join(str(r.get('creator') or '').split()): k = 'no creator'
        elif not names_place(r, name, state):
            k = 'place or state not in title or tags'
            if len(ex) < 3: ex.append(r.get('title') or '')
        else: continue
        out[k] = out.get(k, 0) + 1
    return out, ex
def openverse_search(name, state=''):
    """Openverse results for the exact place name. The state is NOT in the query (a phrase plus an extra word returned no result at all for 19 of 20 places in the first dry runs, #768): names_place() checks the state afterwards."""
    q = o.API + '?' + urllib.parse.urlencode({'q': '"%s"' % name, 'license': 'cc0,pdm,by,by-sa', 'category': 'photograph', 'excluded_source': 'inaturalist', 'page_size': 20})
    return (wm.get(q) or {}).get('results') or []
def to_jpeg(raw):
    """A 330 px wide JPEG (bytes), or None when it is too big, not an image, or under 200 px on its short side."""
    from PIL import Image
    if not raw or len(raw) > MAX_BYTES: return None
    try:
        im = Image.open(io.BytesIO(raw)); im.load()
        if min(im.size) < MIN_SIDE: return None
        im = im.convert('RGB')
        if im.size[0] > WIDTH: im = im.resize((WIDTH, max(1, round(im.size[1] * WIDTH / im.size[0]))))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=82); return b.getvalue()
    except Exception: return None
def openverse_entry(pid, creator, lic, lu, rid, now):
    page = 'https://openverse.org/image/%s' % rid
    return dict(f=pid + '.jpg', a=creator, l=lic, lu=lu, p=page, w=page, s='Openverse', checkedAt=now, fetchedAt=now)

# --- the vetted Commons rows (the author rule applied as a source reads them)
class Vetted:
    """The rows of cs.commons_info, vetted when a strategy first reads one (only a CC BY / BY-SA row with an unknown author costs the extra Commons request): a row with no author to be found loses its licence, so
    pick (which the sources use unchanged) passes over it and may take the next file."""
    def __init__(self, info): self.info = info; self.done = {}
    def get(self, key, default=None):
        if key in self.done: return self.done[key]
        row = self.info.get(key)
        if row is None: return default
        lic, au, lu, thumb, mime = row
        au = al.clean(au) or au   # the one stored form (lib/author_clean.py)
        if al.by_licence(lic) and al.unknown(au):
            cls, name = al.lookup(key)
            if cls != 'none' and name: au = name
            else: lic = ''
        self.done[key] = (lic, au, lu, thumb, mime); return self.done[key]


# --- the five sources: each takes the places to try and yields (place, Res)
def us_state_of(u):
    return u['place'].split(',')[0].strip() if u['place'].endswith(', USA') else ''

def find_wikipedia(todo):
    tmp = tempfile.mkdtemp()
    try:
        for u in todo:
            man = {}
            try: r = ph.one(u['id'], u['title'], tmp, man, us_state_of(u))   # writes tmp/<id>.jpg and man[title]; photos.py's own rules, untouched
            except Exception as ex: r = 'err ' + str(ex)[:50]
            if r == 'ok':
                path = os.path.join(tmp, u['id'] + '.jpg')
                with open(path, 'rb') as f: jpg = f.read()
                os.remove(path); yield u, Res('found', man[u['title']], jpg)
            elif pr.failure_class(r) == 'permanent': yield u, Res('miss', why=r, status=r)
            else: yield u, Res('retry', why=r)
    finally: shutil.rmtree(tmp, ignore_errors=True)

def find_commons(todo):
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]; res = cs.resolve([u['title'] for u in batch]); names = cs.wikidata_images(sorted(set(res.values())))
        files = sorted({n.replace(' ', '_') for v in names.values() for n in v[:2]}); info = Vetted(cs.commons_info(files) if files else {})
        for u in batch:
            page = res.get(u['title'], u['title'])
            if page not in names: yield u, Res('miss', why='no Wikidata item for this page (after following redirects)'); continue
            got = pick(names[page], info)
            if not got: yield u, Res('miss', why='no usable picture among %s' % names[page][:2]); continue
            b = wm.get(got[4], raw=True)
            if not b: yield u, Res('retry', why='download failed'); continue
            yield u, Res('found', entry(u['id'], page, got, now_iso()), b, note=got[0])

def find_nearby(todo):
    for u in todo:
        cands = nearby(u['lat'], u['lon']); want = words(u['name']) | words(u['title'])
        files = [fn for fn, _ in cands if want & words(fn) and not BUILDING.search(fn)]
        m = match(u['name'], u['title'], cands, Vetted(cs.commons_info(files[:50]) if files else {}))
        if not m: yield u, Res('miss', why='%d files nearby, %d with a matching name word' % (len(cands), len(files))); continue
        got, dist = m; b = wm.get(got[4], raw=True)
        if not b: yield u, Res('retry', why='download failed'); continue
        yield u, Res('found', entry(u['id'], u['title'], got, now_iso()), b, note='%s (%d m)' % (got[0], dist))

def find_category(todo):
    for u in todo:
        name = u['name']; want = words(name) | words(u['title']); region = u['region']
        c = good_category(categories(name), name, region); files = category_files(c) if c else []
        kind = {w for w in re.findall(r'[a-z]+', name.lower()) if w in KIND}
        got = choose(files, want, Vetted(cs.commons_info(files[:50])), kind, region) if files else None
        if not got: yield u, Res('miss', why=('category %s has no usable file' % c) if c else 'no matching category'); continue
        b = wm.get(got[4], raw=True)
        if not b: yield u, Res('retry', why='download failed'); continue
        yield u, Res('found', entry(u['id'], u['title'], got, now_iso()), b, note='%s (category %s)' % (got[0], c))

def find_openverse(todo):
    fails = 0
    for u in todo:
        name = u['short'] or u['name']; state = state_of_place(u['place'])
        try:
            res = openverse_search(name, state); cands = openverse_candidates(res, name, state); fails = 0; hit = None
            for rid, url, au, lic, lu in cands[:TRY_FILES]:
                jpg = to_jpeg(wm.get(url, raw=True, tries=2))
                if jpg: hit = (rid, au, lic, lu, jpg); break
        except RuntimeError as ex:
            fails += 1; yield u, Res('retry', why='request failed: %s' % ex)
            if fails >= 3: raise
            continue
        if hit: yield u, Res('found', openverse_entry(u['id'], hit[1], hit[2], hit[3], hit[0], now_iso()), hit[4], note='https://openverse.org/image/' + hit[0])
        else: yield u, Res('miss', why='%d usable photos of %d results' % (len(cands), len(res)))

def _missing(w, u): return w.is_missing(u['id'])
# (name, source, which places it applies to, retry days; None = the missing record's own expiry). The order is the order they are tried in.
SOURCES = [('wikipedia', find_wikipedia, lambda w, u: True, None),
           ('commons', find_commons, _missing, RETRY_DAYS),
           ('nearby', find_nearby, lambda w, u: _missing(w, u) and u['lat'] is not None and u['lon'] is not None, RETRY_DAYS),
           ('category', find_category, _missing, RETRY_DAYS),
           ('openverse', find_openverse, lambda w, u: _missing(w, u) and bool(state_of_place(u['place'])), RETRY_DAYS)]
