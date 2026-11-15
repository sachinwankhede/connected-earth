#!/usr/bin/env python3
"""species_sources.py: the SOURCES of species pictures, in one module (docs/DATA-PLAN.md, "Species pictures"; #934, phase 4). The species twin of lib/place_sources.py.
jobs/speciespictures.py decides the order, the holds, the author rule and the writing; THIS module knows where a picture can come from. Each source is one function
`find_<name>(todo)` that takes the units to try and yields (unit, Res), plus one line in SOURCES: (name, find, which units it applies to, retry days; None = the missing record's own expiry).
A unit is one Wikipedia title of the species table: {sid, title, name, latin, abiotic}. A title shared by several species rows is ONE unit here (the job fetches it once and gives each sid its own entry).
A found Res carries the credit row ({a, l, lu, p, s?, wiki, page, u, src?}: u is the source path the larger copies are made from, as in species_pics.py) and `jpg`, the downloaded picture (any image format, the job shrinks it).
To add a source, write its function here and add its line to SOURCES.
The rules below were the old jobs' own functions (jobs/speciesphotos.py + hostphotos.py (Wikipedia), commonsphotos.py, gbifphotos.py, openversephotos.py, inaturalistphotos.py, largephotos.py for the copy addresses);
they were COPIED here with the same behaviour (the old job files stay until the new job has had one good run). Network goes through lib/wm.py (hosts listed in lib/allowed_sources.json, enforced by lib/fetch.py); no host is added."""
import io, ipaddress, os, re, sys, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import wm
from photo_registry import ALLOWED_IMAGE_HOSTS, safe_https
import commons_api as cs
from openverse_api import API as OV_API, licence_of as ov_licence_of, norm, unwanted, SHEET_WORDS
from place_sources import Res, Vetted   # the same result type and the same vetted Commons rows (author rule) as the place sources

RETRY_DAYS = 90   # every source but wikipedia: tried again this long after its date in photos/species_tried.json

# --- Wikipedia: the picture of the species' page (from speciesphotos.py for the link, hostphotos.py for the licence and the download)
NOTPHOTO = re.compile(r'logo|emblem|coat[_ ]of[_ ]arms|(^|[_ ])flag([_ .]|$)|\.svg|map\.(png|jpe?g|gif)$|(^|[_ -])maps?([_ .0-9-]|$)|locator|diagram|[_ -]chart', re.I)
THUMB_BASE = 'https://thumb.wikimedia.org/wikipedia/commons/thumb/'
BASE = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'   # hostphotos.BASE: where the 330 px thumbnails are downloaded and the larger copies' addresses start

def commons_file(u):
    """File name on Commons from a manifest path: relative 'a/ab/Name.jpg/330px-Name.jpg', or an absolute upload.wikimedia.org .../commons/ URL (full size or thumb). None for other wikis."""
    if not u.startswith('http'):
        parts = u.split('/'); return urllib.parse.unquote(parts[2]) if len(parts) >= 3 else None
    parts = u.split('/')
    if len(parts) < 8 or parts[2] != 'upload.wikimedia.org' or parts[3:5] != ['wikipedia', 'commons']: return None
    i = 7 if parts[5] != 'thumb' else 8
    return urllib.parse.unquote(parts[i]) if len(parts) > i else None

def thumb_path(u):
    """Path below BASE of the 330 px thumbnail."""
    if not u.startswith('http'): return u
    parts = u.split('/')[5:]
    if parts[0] == 'thumb': return '/'.join(parts[1:])
    return '%s/%s/%s/330px-%s' % (parts[0], parts[1], parts[2], parts[2])

def download(u):
    """The 330 px thumbnail. A full-size Commons link may belong to an original smaller than 330 px, which has no thumbnail: then the original itself is taken."""
    if not u.startswith('http') or '/thumb/' in u: return wm.get(BASE + thumb_path(u), raw=True)
    try: raw = wm.get(BASE + thumb_path(u), raw=True, tries=1)
    except RuntimeError: raw = None
    return raw or wm.get(u, raw=True)

def pageimages(batch):
    """(hit, known) for up to 50 titles, or None when the request failed. hit: {title: (image path below THUMB_BASE, quoted page name) or None}, None meaning the page has no usable picture; a title the answer
    does not mention is not in it. known: every title the answer redirected or normalised from. The batched pageimages query of speciesphotos.py."""
    q = 'https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&piprop=thumbnail&pithumbsize=330&redirects=1&format=json&titles=' + urllib.parse.quote('|'.join(batch))
    j = wm.get(q)
    if not j: return None
    qq = j.get('query', {}); back = {}
    for k in ('normalized', 'redirects'):
        for r in qq.get(k, []): back.setdefault(r['to'], []).append(r['from'])
    hit = {}
    for p in qq.get('pages', {}).values():
        names = [p.get('title')]
        for _ in range(2): names += [f for n in list(names) for f in back.get(n, [])]
        th = p.get('thumbnail'); src = th['source'].split('?')[0] if th else ''
        for n in set(names):
            if th and not safe_https(src, ALLOWED_IMAGE_HOSTS): continue
            if th and not NOTPHOTO.search(urllib.parse.unquote(src.split('/')[-2] if '/thumb/' in src else src)):
                hit[n] = (src.replace(THUMB_BASE, ''), urllib.parse.quote(p['title'].replace(' ', '_')))
            else: hit[n] = None
    return {t: hit[t] for t in batch if t in hit}, {x for v in back.values() for x in v}

def find_wikipedia(todo):
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]; got = pageimages([u['title'] for u in batch])
        if got is None:
            for u in batch: yield u, Res('retry', why='the batch request failed')
            continue
        hit, known = got; files = {}
        for u in batch:
            h = hit.get(u['title'])
            if h:
                f = commons_file(h[0])
                if f: files[u['title']] = f
        info = cs.commons_info(sorted({f.replace(' ', '_') for f in files.values()})) if files else {}
        for u in batch:
            t = u['title']; h = hit.get(t)
            if not h:
                if t in hit or t in known: yield u, Res('miss', why='Wikipedia has no usable picture for the page', status='nophoto')
                else: yield u, Res('retry', why='the title was not in the answer')
                continue
            f = files.get(t)
            if not f: yield u, Res('miss', why='not a Commons file', status='notcommons'); continue
            row = info.get(f.replace(' ', '_'))
            if not row: yield u, Res('retry', why='no licence found'); continue   # the old hostphotos tried such a file again every run
            lic, author, lu, _, _ = row
            if not cs.open_licence(lic): yield u, Res('miss', why='licence %r' % (lic or 'unknown'), status='notfree'); continue
            raw = download(h[0])
            if not raw: yield u, Res('retry', why='download failed'); continue
            e = dict(a=author or 'Unknown author', l=lic, lu=lu, p='https://commons.wikimedia.org/wiki/File:' + urllib.parse.quote(f), wiki=t, page=h[1], u=h[0])
            yield u, Res('found', e, raw, note=f)


# --- Commons: Wikidata image property (from commonsphotos.py)
def find_commons(todo):
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]; res = cs.resolve([u['title'].replace('_', ' ') for u in batch]); names = cs.wikidata_images(sorted(set(res.values())))
        files = sorted({n.replace(' ', '_') for v in names.values() for n in v[:2]}); info = Vetted(cs.commons_info(files) if files else {})
        for u in batch:
            t = u['title']; k = res.get(t.replace('_', ' '), t.replace('_', ' ')); entry = None; why = ''
            if k not in names: why = 'no Wikidata item for this page (after following redirects)'
            elif not names[k]: why = 'item has no usable P18'
            for n in names.get(k, [])[:2]:
                lic, author, lu, thumb, mime = info.get(n.replace(' ', '_'), ('', '', '', '', ''))
                why = 'file %s: licence %r, type %r, link %s' % (n, lic, mime, thumb[:220] or 'none')
                if cs.is_photo_type(mime) and cs.open_licence(lic):
                    me = cs.manifest_entry(thumb, t)
                    if me: entry = (n.replace(' ', '_'), lic, author, lu, thumb, me); break
            if not entry: yield u, Res('miss', why=why); continue
            n, lic, author, lu, thumb, me = entry; b = wm.get(thumb, raw=True)
            if not b: yield u, Res('retry', why='download failed'); continue
            e = dict(a=author or 'Unknown author', l=lic, lu=lu, p='https://commons.wikimedia.org/wiki/File:' + urllib.parse.quote(n), wiki=t, page=me[1], u=me[0], src='wikidata-p18')
            yield u, Res('found', e, b, note=n)


# --- GBIF occurrence media (from gbifphotos.py)
MIN_SIDE = 200; MAX_BYTES = 12_000_000; TRY_FILES = 4
GBIF = 'https://api.gbif.org/v1/'
INAT_DATASET = '50c9509d-22c7-4a22-a47d-8c48425ef4a7'
GBIF_LICENCES = {'http://creativecommons.org/publicdomain/zero/1.0/': ('CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0'),
                 'http://creativecommons.org/licenses/by/4.0/': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'),
                 'http://creativecommons.org/licenses/by/3.0/': ('CC BY 3.0', 'https://creativecommons.org/licenses/by/3.0')}   # CC0 and CC BY only, never NC, ND or SA-only
BASIS_OK = {'HUMAN_OBSERVATION', 'MACHINE_OBSERVATION', 'LIVING_SPECIMEN', 'OBSERVATION'}

def gbif_licence_of(media):
    """(short name, https licence link) for a media record under CC0 or CC BY, else None. GBIF gives the licence as a link or as its enum name."""
    v = (media.get('license') or '').strip()
    if not v: return None
    v = {'CC0_1_0': 'http://creativecommons.org/publicdomain/zero/1.0/', 'CC_BY_4_0': 'http://creativecommons.org/licenses/by/4.0/'}.get(v, v)
    if not v.endswith('/'): v += '/'
    return GBIF_LICENCES.get(v.replace('https://', 'http://', 1))

def from_inaturalist(rec, media):
    """True for a record that came through iNaturalist: its dataset, institution code, or any link of the record."""
    blob = ' '.join(str(x) for x in (rec.get('institutionCode'), rec.get('collectionCode'), rec.get('references'), media.get('references'), media.get('identifier'), media.get('source'), media.get('publisher')) if x).lower()
    return rec.get('datasetKey') == INAT_DATASET or 'inaturalist' in blob

def from_collection(rec, media):
    """True for a herbarium sheet or museum object that GBIF labels as an observation (the Smithsonian NMNH and Meise records were)."""
    blob = ' '.join(str(x) for x in (rec.get('datasetName'), rec.get('collectionCode'), rec.get('collectionKey'), rec.get('typeStatus'), rec.get('preparations'), media.get('identifier'), media.get('references'), media.get('source')) if x).lower()
    return any(w in blob for w in SHEET_WORDS)

def safe_url(u):
    """https only, a named host (no address, no localhost), no credentials in the link."""
    try: p = urllib.parse.urlsplit(u or '')
    except ValueError: return False
    if p.scheme != 'https' or not p.hostname or p.username or p.password: return False
    h = p.hostname.lower()
    if h == 'localhost' or h.endswith('.local') or '.' not in h: return False
    try: ipaddress.ip_address(h); return False
    except ValueError: return True

def gbif_author_of(rec, media):
    a = ' '.join(str(media.get('creator') or media.get('rightsHolder') or rec.get('recordedBy') or '').split())
    return a if a and a.lower() not in ('unknown', 'anonymous', 'n/a', 'none') else ''

def gbif_candidates(results):
    """[(occurrence key, picture link, author, short licence, licence link)] from occurrence/search results, best first (the order GBIF gave), only what may be used."""
    out = []
    for rec in results or []:
        if rec.get('basisOfRecord') not in BASIS_OK or not rec.get('key'): continue
        for m in rec.get('media') or []:
            if m.get('type') != 'StillImage' or not safe_url(m.get('identifier')): continue
            lic = gbif_licence_of(m); au = gbif_author_of(rec, m)
            if not lic or not au or from_inaturalist(rec, m) or from_collection(rec, m): continue
            out.append((rec['key'], m['identifier'], au, lic[0], lic[1])); break   # one picture per occurrence
    return out

def gbif_match(name):
    """The GBIF taxon key when the name matches exactly (species or genus, accepted or synonym), else None."""
    j = wm.get(GBIF + 'species/match?verbose=false&name=' + urllib.parse.quote(name)) or {}
    if j.get('matchType') != 'EXACT' or not j.get('usageKey'): return None
    return j['usageKey']

def gbif_search(key):
    q = (GBIF + 'occurrence/search?mediaType=StillImage&occurrenceStatus=PRESENT&license=CC0_1_0&license=CC_BY_4_0&limit=40&taxonKey=%s' % key + ''.join('&basisOfRecord=' + b for b in sorted(BASIS_OK)))
    return (wm.get(q) or {}).get('results') or []

def fetch_raw(url, tries=2):
    """The downloaded bytes when the picture is not too big, decodes, and is at least 200 px on its short side (gbifphotos.fetch_small's checks), else None."""
    from PIL import Image
    raw = wm.get(url, raw=True, tries=tries)
    if not raw or len(raw) > MAX_BYTES: return None
    try:
        im = Image.open(io.BytesIO(raw)); im.load()
        return raw if min(im.size) >= MIN_SIDE else None
    except Exception: return None

def _credit(u, au, lic, lu, page_url, source, u_path, src):
    return dict(a=au, l=lic, lu=lu, p=page_url, s=source, wiki=u['title'], page=urllib.parse.quote(u['title'].replace(' ', '_')), u=u_path, src=src)

def find_gbif(todo):
    for u in todo:
        name = u['title'].replace('_', ' '); hit = None
        try:
            key = gbif_match(name)
            if not key: yield u, Res('miss', why='no exact GBIF match'); continue
            cands = gbif_candidates(gbif_search(key)); why = '%d usable photos' % len(cands)
            for ok, url, au, lic, lu in cands[:TRY_FILES]:
                raw = fetch_raw(url)
                if not raw: why += '; %s too small or not an image' % ok; continue
                hit = (ok, au, lic, lu, raw); break
        except RuntimeError as ex: yield u, Res('retry', why='request failed: %s' % ex); continue   # a failed request is not a "no picture"
        if hit: yield u, Res('found', _credit(u, hit[1], hit[2], hit[3], 'https://www.gbif.org/occurrence/%s' % hit[0], 'GBIF', 'gbif/%s' % hit[0], 'gbif'), hit[4], note='https://www.gbif.org/occurrence/%s' % hit[0])
        else: yield u, Res('miss', why=why)


# --- Openverse (from openversephotos.py)
def names_species(r, name):
    """True when the Latin name is in the title or one of the tags."""
    n = norm(name)
    return bool(n) and (n in norm(r.get('title')) or any(n in norm(t.get('name')) for t in r.get('tags') or []))

def openverse_candidates(results, name):
    """[(id, thumbnail link, creator, short licence, licence link)] in Openverse's order, only what may be used."""
    out = []
    for r in results or []:
        rid = r.get('id') or ''
        if not re.fullmatch(r'[0-9a-f-]{36}', rid) or unwanted(r) or not names_species(r, name): continue
        lic = ov_licence_of(r); au = ' '.join(str(r.get('creator') or '').split())
        if not lic or not au or au.lower() in ('unknown', 'anonymous', 'n/a', 'none'): continue
        out.append((rid, OV_API + rid + '/thumb/', au, lic[0], lic[1]))
    return out

def openverse_search(name):
    q = OV_API + '?' + urllib.parse.urlencode({'q': '"%s"' % name, 'license': 'cc0,pdm,by,by-sa', 'category': 'photograph', 'excluded_source': 'inaturalist', 'page_size': 20})
    return (wm.get(q) or {}).get('results') or []

def find_openverse(todo):
    fails = 0
    for u in todo:
        name = u['title'].replace('_', ' '); hit = None
        try:
            cands = openverse_candidates(openverse_search(name), name); fails = 0; why = '%d usable photos' % len(cands)
            for rid, url, au, lic, lu in cands[:TRY_FILES]:
                raw = fetch_raw(url)
                if not raw: why += '; %s too small or not an image' % rid; continue
                hit = (rid, au, lic, lu, raw); break
        except RuntimeError as ex:
            fails += 1; yield u, Res('retry', why='request failed: %s' % ex)
            if fails >= 3: raise   # three in a row: a key is needed or the source throttles; the job stops this source and exits 2
            continue
        if hit: yield u, Res('found', _credit(u, hit[1], hit[2], hit[3], 'https://openverse.org/image/%s' % hit[0], 'Openverse', 'openverse/%s' % hit[0], 'openverse'), hit[4], note='https://openverse.org/image/' + hit[0])
        else: yield u, Res('miss', why=why)


# --- iNaturalist taxon photos (from inaturalistphotos.py)
INAT_API = 'https://api.inaturalist.org/v1/taxa'
INAT_BUCKET = 'https://inaturalist-open-data.s3.amazonaws.com/photos/'
RANKS = ('species', 'genus'); INAT_TRY = 3
INAT_LICENCES = {'cc0': ('CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0'), 'cc-by': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'),
                 'cc-by-sa': ('CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0')}   # iNaturalist shows its CC licences as version 4.0

def match_taxon(results, name):
    """Id of the active taxon whose scientific name is exactly `name` (any case) and whose rank is a species or genus, else None."""
    for r in results or []:
        if (r.get('name') or '').strip().lower() == name.strip().lower() and r.get('rank') in RANKS and r.get('is_active', True) and isinstance(r.get('id'), int): return r['id']
    return None

def inat_candidates(taxon, limit=INAT_TRY):
    """[(photo id, medium picture link, photographer, short licence, licence link)] in iNaturalist's order, only what may be used."""
    out = []
    for tp in (taxon or {}).get('taxon_photos') or []:
        p = tp.get('photo') or {}; lic = INAT_LICENCES.get((p.get('license_code') or '').lower().strip()); pid = p.get('id')
        au = ' '.join(str(p.get('attribution_name') or '').split()); url = p.get('medium_url') or ''
        if not lic or not isinstance(pid, int) or p.get('flags') or not au or au.lower() in ('unknown', 'anonymous', 'n/a', 'none'): continue
        if url != '%s%d/medium.jpg' % (INAT_BUCKET, pid): continue   # only the bucket of openly licensed photos, only the picture of this id
        out.append((pid, url, au, lic[0], lic[1]))
        if len(out) >= limit: break
    return out

def inat_name(u):
    """The name to look up: the Latin name of the species row when the title is its common name and the Latin name is a species or genus (one or two words; a subspecies would show the species' photos), else the title."""
    t = u['title'].replace('_', ' '); l = (u.get('latin') or '').strip()
    return l if u.get('name') == t and l and l != t and len(l.split()) <= 2 else t

def inat_lookup(name):
    tid = match_taxon((wm.get(INAT_API + '?' + urllib.parse.urlencode({'q': name, 'per_page': 10})) or {}).get('results'), name)
    if tid is None: return None
    return ((wm.get('%s/%d' % (INAT_API, tid)) or {}).get('results') or [None])[0]

def find_inaturalist(todo):
    fails = 0
    for u in todo:
        name = inat_name(u); hit = None
        try:
            taxon = inat_lookup(name); fails = 0; cands = inat_candidates(taxon) if taxon else []
            why = 'no taxon of that name' if not taxon else '%d usable photos' % len(cands)
            for pid, url, au, lic, lu in cands:
                raw = fetch_raw(url)
                if not raw: why += '; %d too small or not an image' % pid; continue
                hit = (pid, au, lic, lu, raw); break
        except RuntimeError as ex:
            fails += 1; yield u, Res('retry', why='request failed: %s' % ex)
            if fails >= 3: raise
            continue
        if hit: yield u, Res('found', _credit(u, hit[1], hit[2], hit[3], 'https://www.inaturalist.org/photos/%d' % hit[0], 'iNaturalist', 'inaturalist/%d' % hit[0], 'inaturalist'), hit[4], note='https://www.inaturalist.org/photos/%d' % hit[0])
        else: yield u, Res('miss', why=why)


# --- where the 192 px and 400 px copies come from (largephotos.py)
OPENVERSE_THUMB = 'https://api.openverse.org/v1/images/%s/thumb/'; INAT_MEDIUM = 'https://inaturalist-open-data.s3.amazonaws.com/photos/%s/medium.jpg'

def width_path(u, w):
    """Path below BASE of the thumbnail of the manifest picture u at w px wide (Commons serves 330, 500, 960 ... only)."""
    p = thumb_path(u).split('/'); p[-1] = re.sub(r'^\d+px-', '%dpx-' % w, p[-1]); return '/'.join(p)

def source_urls(u):
    """Download links, best first, for the picture's source path u: Openverse and iNaturalist serve their own size (about 500 px wide), Commons a 500 px thumbnail (330 px when the original is smaller); a GBIF picture has none to offer."""
    if not u: return []
    src, _, rest = u.partition('/')
    if src == 'openverse': return [OPENVERSE_THUMB % rest]
    if src == 'inaturalist': return [INAT_MEDIUM % rest]
    if src == 'gbif': return []
    return [BASE + width_path(u, 500), BASE + thumb_path(u)]


def _missing(w, u): return w.is_missing(u['sid'])
def _organism(w, u): return _missing(w, u) and not u.get('abiotic')   # a title of a soil, a lake, water: a search finds a photo of the thing the word names, not of a species (#511)
# (name, source, which units it applies to, retry days; None = the missing record's own expiry). The order is the order they are tried in.
SOURCES = [('wikipedia', find_wikipedia, lambda w, u: True, None),
           ('commons', find_commons, _missing, RETRY_DAYS),
           ('gbif', find_gbif, _missing, RETRY_DAYS),
           ('openverse', find_openverse, _organism, RETRY_DAYS),
           ('inaturalist', find_inaturalist, _organism, RETRY_DAYS)]
