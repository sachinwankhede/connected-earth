#!/usr/bin/env python3
"""placepictures.py: the ONE job that finds a picture for a place that has none (docs/DATA-PLAN.md, step 4; #887).
Usage: placepictures.py [--strategy all|wikipedia|commons|nearby|category|openverse|large] [--limit N] [--max-mb N] [--again] [--dry]   (run from the repository root)

It replaces the five acquire jobs for place pictures (jobs/photos.py, commonsplacephotos.py, commonsnearby.py, commonscategory.py, openverseplaces.py), which each wrote the files and lists in their own way. Here the five
SOURCES are strategies tried in this order, and a place stops at the first one that gives an accepted picture:
  wikipedia  the picture of the place's Wikipedia page (photos.one)
  commons    Wikidata's image property, then the file's licence on Commons (commonsplacephotos.pick)
  nearby     Commons files geotagged within 1.5 km whose name shares a distinctive word with the place (commonsnearby.match)
  category   the place's own Commons category (commonscategory.good_category, choose: other-state and other-country files are refused, #891)
  openverse  US places only: an Openverse photograph that names the place and the state, with a named creator (openverseplaces.candidates)
The per-source rules are the old jobs' own functions, imported, not copied: this file decides only the order, the holds, the author rule and the writing.

The larger copy (400 px WebP, the full-width hero of the place page, #727) is made HERE too, right after a picture is accepted and in the SAME commit (PlacePhotos.put, then put_large), so a picture never lands without its pair when
one can be made. Commons cannot thumbnail some originals (a TIFF or a very large file answers HTTP 400; Karavasta Lagoon, Wupatki National Monument, Leasburg Dam State Park): that picture is kept alone, the app shows the small one
(ground rule 10) and the log says so. A picture from another source than Commons has no larger copy to make. `--strategy large` makes the larger copy for the pictures that have none (no new pictures); `all` does that as its last step,
so a copy that failed once is tried again by the next run. This replaces jobs/largeplacephotos.py and its workflow.

Everything is keyed by PLACE ID and written only through lib/place_photos.py (PlacePhotos.put / miss / note_tried / commit: files first, then lists). It needs the id-keyed files the migration (jobs/rekeyplacephotos.py) makes.
A found row carries `wiki` = the place's imgwiki title, which is how the app finds a picture today; so a place whose title is shared with another place is skipped (the migration removed those pictures for the same reason) until the app looks pictures up by id.
Holds (when a source is tried again for a place that gave nothing): wikipedia, as photos.py did, while the missing record has not expired (photo_registry.negative_entry: 180 days for the permanent reasons); each other source RETRY_DAYS (90 days) after its date
in photos/places_tried.json {id: {source: date}}. A transient failure (a download that failed) is recorded nowhere and is tried again by the next run.
Author rule (#887, owner 15 Nov): a CC BY or CC BY-SA picture needs a named author. When the stored credit says unknown, Commons is asked once more (authorlookup.lookup: the Artist or Attribution field, or the uploader when the credit says own work);
no name found = the picture is refused and the place is recorded as 'notfree' for wikipedia, or as tried for the other sources, with the reason in the log.
Caps: --limit places per strategy (default 120, 0 = all left), --max-mb of pictures kept (default 25); pictures are committed every 25 finds, so a stopped run resumes. A run that finds nothing and changes no ledger writes no file.
--dry prints what would be kept and writes nothing (later strategies then see no new missing places). Exit 2 when a source stopped the run (throttled three times, or refused)."""
import collections, datetime, glob, hashlib, io, json, os, re, shutil, sys, tempfile, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import wm, place_photos as pp, photo_registry as pr
import authorlookup as al, photos as ph, commonsplacephotos as cpp, commonsnearby as nb, commonscategory as cat, openverseplaces as ov
cs = cpp.cp   # commonsphotos: resolve, wikidata_images, commons_info

COMMIT_EVERY = 25
COMMONS_THUMBS = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'; LARGE_SIZE = 400; LARGE_QUALITY = 70
Res = collections.namedtuple('Res', 'kind entry jpg why status note', defaults=(None, None, '', 'nophoto', ''))   # kind: found | miss | retry


def now_iso(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def load_units(data_dir):
    """(units, shared): one dict per place with an imgwiki title (id, title, name, short, lat, lon, place, region) in id order; `shared` are the places whose title another place uses too, which no strategy tries."""
    raw = {}
    for f in sorted(glob.glob(data_dir + '/*.json')):
        if f.endswith(('order.json', 'links.json')): continue
        try:
            with open(f, encoding='utf-8') as fh: e = json.load(fh)
        except (OSError, ValueError): continue
        if isinstance(e, dict) and e.get('id') and e.get('imgwiki'): raw[e['id']] = e
    count = collections.Counter(e['imgwiki'] for e in raw.values()); units, shared = [], []
    for pid, e in sorted(raw.items()):
        u = dict(id=pid, title=e['imgwiki'], name=e.get('name') or e['imgwiki'], short=e.get('short') or '', lat=e.get('lat'), lon=e.get('lon'), place=e.get('place') or '', region=e.get('place') or e.get('country') or '')
        (shared if count[e['imgwiki']] > 1 else units).append(u)
    return units, shared

# --- the larger copy (400 px WebP), moved here from jobs/largeplacephotos.py
def commons_file_name(page):
    """File name (underscores) from a Commons file page address, or None for any other address."""
    if not page or 'commons.wikimedia.org/wiki/File:' not in page: return None
    n = urllib.parse.unquote(page.split('File:', 1)[1].split('#')[0].split('?')[0]).replace(' ', '_')
    return n or None

def commons_thumb_url(name, width):
    """Thumbnail address of a Commons file at width px (Commons serves 330, 500, 960 ...). The folder is the first characters of the md5 of the name."""
    h = hashlib.md5(name.encode()).hexdigest(); q = urllib.parse.quote(name)
    return '%s%s/%s/%s/%dpx-%s' % (COMMONS_THUMBS, h[0], h[:2], q, width, q)

def large_urls(page):
    """Download links, best first: the 500 px thumbnail, then the 330 px one (the original may be smaller). Empty for a picture that is not a Commons file."""
    n = commons_file_name(page)
    return [commons_thumb_url(n, 500), commons_thumb_url(n, 330)] if n else []

def download_thumb(urls, get):
    """Bytes of the first address that downloads, or None. A thumbnail that Commons cannot make (a TIFF or a very large original answers HTTP 400) is skipped, not fatal: that place keeps its small picture."""
    for u in urls:
        try: raw = get(u, raw=True)
        except RuntimeError as e: print('skipped', u[-70:], '-', e, flush=True); continue
        if raw: return raw
    return None

def shrink(im, size=LARGE_SIZE):
    """(WebP bytes, (w, h)) of a copy of im at most size px on its longer side."""
    im = im.copy(); im.thumbnail((size, size)); buf = io.BytesIO(); im.save(buf, 'WEBP', quality=LARGE_QUALITY, method=6)
    return buf.getvalue(), im.size

def make_large(entry, get=None):
    """(WebP bytes, '') for a stored picture row, or (None, why) when no larger copy can be made: not a Commons file, no thumbnail downloads, or the download is not an image."""
    urls = large_urls(entry.get('p'))
    if not urls: return None, 'not a Commons file'
    raw = download_thumb(urls, get or wm.get)
    if not raw: return None, 'Commons has no thumbnail for it'
    try:
        from PIL import Image
        return shrink(Image.open(io.BytesIO(raw)).convert('RGB'))[0], ''
    except Exception: return None, 'the thumbnail is not an image'

# --- the author rule
def vet(entry):
    """(entry, '') when the picture may be kept, with the author filled in if Commons knows one; (None, why) for a CC BY / CC BY-SA picture with no author to be found."""
    if not (al.by_licence(entry.get('l')) and al.unknown(entry.get('a'))): return entry, ''
    fn = al.file_of(entry.get('p'))
    if fn:
        cls, name = al.lookup(fn)
        if cls != 'none' and name: return dict(entry, a=name), ''
    return None, 'CC BY / BY-SA with no author'

class Vetted:
    """The rows of cs.commons_info, vetted when a strategy first reads one (only a CC BY / BY-SA row with an unknown author costs the extra Commons request): a row with no author to be found loses its licence, so
    commonsplacephotos.pick (which the strategies use unchanged) passes over it and may take the next file."""
    def __init__(self, info): self.info = info; self.done = {}
    def get(self, key, default=None):
        if key in self.done: return self.done[key]
        row = self.info.get(key)
        if row is None: return default
        lic, au, lu, thumb, mime = row
        if al.by_licence(lic) and al.unknown(au):
            cls, name = al.lookup(key)
            if cls != 'none' and name: au = name
            else: lic = ''
        self.done[key] = (lic, au, lu, thumb, mime); return self.done[key]

def measure(entry, jpg):
    """The row with its measured fields (media type, size, sha256, review status), made by photo_registry.migrate_places on a scratch copy so nothing else in the repository is rewritten."""
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, 'places.json'), 'w', encoding='utf-8') as f: json.dump({'x': entry}, f)
        with open(os.path.join(d, entry['f']), 'wb') as f: f.write(jpg)
        pr.migrate_places(os.path.join(d, 'places.json'), d)
        with open(os.path.join(d, 'places.json'), encoding='utf-8') as f: return json.load(f)['x']
    finally: shutil.rmtree(d, ignore_errors=True)

# --- the five strategies: each takes the places to try and yields (place, Res)
def where_of(u):
    return u['place'].split(',')[0].strip() if u['place'].endswith(', USA') else ''

def find_wikipedia(todo):
    tmp = tempfile.mkdtemp()
    try:
        for u in todo:
            man = {}
            try: r = ph.one(u['id'], u['title'], tmp, man, where_of(u))   # writes tmp/<id>.jpg and man[title]; photos.py's own rules, untouched
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
            got = cpp.pick(names[page], info)
            if not got: yield u, Res('miss', why='no usable picture among %s' % names[page][:2]); continue
            b = wm.get(got[4], raw=True)
            if not b: yield u, Res('retry', why='download failed'); continue
            yield u, Res('found', cpp.entry(u['id'], page, got, now_iso()), b, note=got[0])

def find_nearby(todo):
    for u in todo:
        cands = nb.nearby(u['lat'], u['lon']); want = nb.words(u['name']) | nb.words(u['title'])
        files = [fn for fn, _ in cands if want & nb.words(fn) and not nb.BUILDING.search(fn)]
        m = nb.match(u['name'], u['title'], cands, Vetted(cs.commons_info(files[:50]) if files else {}))
        if not m: yield u, Res('miss', why='%d files nearby, %d with a matching name word' % (len(cands), len(files))); continue
        got, dist = m; b = wm.get(got[4], raw=True)
        if not b: yield u, Res('retry', why='download failed'); continue
        yield u, Res('found', cpp.entry(u['id'], u['title'], got, now_iso()), b, note='%s (%d m)' % (got[0], dist))

def find_category(todo):
    for u in todo:
        name = u['name']; want = nb.words(name) | nb.words(u['title']); region = u['region']
        c = cat.good_category(cat.categories(name), name, region); files = cat.category_files(c) if c else []
        kind = {w for w in re.findall(r'[a-z]+', name.lower()) if w in cat.KIND}
        got = cat.choose(files, want, Vetted(cs.commons_info(files[:50])), kind, region) if files else None
        if not got: yield u, Res('miss', why=('category %s has no usable file' % c) if c else 'no matching category'); continue
        b = wm.get(got[4], raw=True)
        if not b: yield u, Res('retry', why='download failed'); continue
        yield u, Res('found', cpp.entry(u['id'], u['title'], got, now_iso()), b, note='%s (category %s)' % (got[0], c))

def find_openverse(todo):
    fails = 0
    for u in todo:
        name = u['short'] or u['name']; state = ov.where_of(u['place'])
        try:
            res = ov.search(name, state); cands = ov.candidates(res, name, state); fails = 0; hit = None
            for rid, url, au, lic, lu in cands[:ov.TRY_FILES]:
                jpg = ov.to_jpeg(wm.get(url, raw=True, tries=2))
                if jpg: hit = (rid, au, lic, lu, jpg); break
        except RuntimeError as ex:
            fails += 1; yield u, Res('retry', why='request failed: %s' % ex)
            if fails >= 3: raise
            continue
        if hit: yield u, Res('found', ov.entry(u['id'], hit[1], hit[2], hit[3], hit[0], now_iso()), hit[4], note='https://openverse.org/image/' + hit[0])
        else: yield u, Res('miss', why='%d usable photos of %d results' % (len(cands), len(res)))

def _missing(w, u): return w.is_missing(u['id'])
# (name, strategy, which places it applies to, retry days; None = the missing record's own expiry)
STRATEGIES = [('wikipedia', find_wikipedia, lambda w, u: True, None),
              ('commons', find_commons, _missing, cpp.RETRY_DAYS),
              ('nearby', find_nearby, lambda w, u: _missing(w, u) and u['lat'] is not None and u['lon'] is not None, nb.RETRY_DAYS),
              ('category', find_category, _missing, cat.RETRY_DAYS),
              ('openverse', find_openverse, lambda w, u: _missing(w, u) and bool(ov.where_of(u['place'])), ov.RETRY_DAYS)]

def held(w, pid, source, days, today):
    """True while the source must not try this place again."""
    if days is None: return pr.cache_active(w.miss_.get(pid))
    return w.tried.get(pid, {}).get(source, '') > (today - datetime.timedelta(days=days)).isoformat()

def acquire(w, units, strategies=None, only='all', limit=120, max_bytes=25_000_000, again=False, dry=False, today=None, log=print, large=None):
    """Runs the strategies in order over the places that have no picture, then (strategy large, or all) makes the missing larger copies. Returns (stats, stopped): per-strategy counts and the strategies a source stopped.
    large: make_large, or None to make no larger copies (the tests of the sources do not download)."""
    today = today or datetime.date.today(); strategies = STRATEGIES if strategies is None else strategies
    stats = collections.OrderedDict(); stopped = []; spent = 0; pending = 0
    for name, find, applies, days in strategies:
        if only not in ('all', name): continue
        s = stats[name] = collections.Counter()
        todo = [u for u in units if not w.has(u['id']) and applies(w, u) and (again or not held(w, u['id'], name, days, today))]
        if limit: todo = todo[:limit]
        log('strategy %s: %d places to try' % (name, len(todo)))
        try:
            for u, r in find(todo):
                pid = u['id']; s['tried'] += 1
                if r.kind == 'found':
                    entry, why = vet(r.entry)
                    if entry is None:
                        s['refused'] += 1; log('refused %s %s (%s) - %s' % (name, pid, u['title'], why))
                        if not dry: (w.miss(pid, 'notfree', 'wikipedia') if name == 'wikipedia' else w.note_tried(pid, name)); pending += 1
                        continue
                    try: row = measure(dict(entry, wiki=u['title']), r.jpg)
                    except ValueError as ex: s['retry'] += 1; log('retry %s %s - unusable image data: %s' % (name, pid, ex)); continue
                    s['found'] += 1; spent += len(r.jpg)
                    log('yes %s %s (%s) -> %s | %s | %s' % (name, pid, u['title'], r.note or row.get('p', ''), row.get('l', ''), row.get('a', '')))
                    if not dry:
                        w.put(pid, row, r.jpg); pending += 1
                        if large is not None:   # the pair goes into the same commit as the picture
                            webp, lwhy = large(row)
                            if webp: w.put_large(pid, webp); s['large'] += 1; spent += len(webp); log('larger copy %s %s %d KB' % (name, pid, round(len(webp) / 1024)))
                            else: s['nolarge'] += 1; log('no larger copy %s %s (%s) - %s; the small picture stays' % (name, pid, u['title'], lwhy))
                elif r.kind == 'miss':
                    s['miss'] += 1; s['refused_licence'] += (r.status == 'notfree'); log('no %s %s (%s) - %s' % (name, pid, u['title'], r.why))
                    if not dry: (w.miss(pid, r.status, 'wikipedia') if name == 'wikipedia' else w.note_tried(pid, name)); pending += 1
                else: s['retry'] += 1; log('retry %s %s (%s) - %s' % (name, pid, u['title'], r.why))
                if pending >= COMMIT_EVERY and not dry: w.commit(); pending = 0
                if spent >= max_bytes: log('STOP: %d KB of pictures kept (the cap); the rest waits for the next run' % (spent // 1024)); break
        except RuntimeError as ex:
            stopped.append(name); log('STOP %s: %s (nothing more is tried from this source; ask the owner)' % (name, ex))
        if pending and not dry: w.commit(); pending = 0   # a run that changed nothing writes nothing
        if spent >= max_bytes: break
    if only in ('all', 'large') and large is not None and spent < max_bytes:
        s = stats['large'] = collections.Counter()
        todo = sorted(pid for pid, e in w.pics.items() if e.get('f') and not w.has_large(pid) and commons_file_name(e.get('p')))
        if limit: todo = todo[:limit]
        log('strategy large: %d pictures without a larger copy' % len(todo))
        for pid in todo:
            s['tried'] += 1
            if dry: log('would try a larger copy for %s' % pid); continue
            webp, lwhy = large(w.pics[pid])
            if webp: w.put_large(pid, webp); s['made'] += 1; spent += len(webp); pending += 1; log('larger copy large %s %d KB' % (pid, round(len(webp) / 1024)))
            else: s['none'] += 1; log('no larger copy large %s (%s) - %s; the small picture stays' % (pid, w.pics[pid].get('wiki', ''), lwhy))
            if pending >= COMMIT_EVERY: w.commit(); pending = 0
            if spent >= max_bytes: log('STOP: %d KB kept (the cap); the rest waits for the next run' % (spent // 1024)); break
        if pending and not dry: w.commit(); pending = 0   # a run that changed nothing writes nothing
    return stats, stopped

def stats_block(w, counters, dry=False):
    """The end-of-run stats as a compact Markdown block (pure). counters = {'places': total places, 'strategies': the per-strategy Counters acquire returns}. `w` is read for the pictures now on disk.
    Refusals by reason: no author (the author rule), licence not allowed (a source answered 'notfree'), other (the source had no usable picture). Under --dry nothing was written, so the picture count adds what would be kept."""
    st = counters.get('strategies', {}); total = counters.get('places', 0)
    g = lambda k: sum(s[k] for s in st.values()); added = g('found'); large = g('large') + g('made')
    have = len(w.pics) + (added if dry else 0); lic = g('refused_licence'); noauth = g('refused'); other = g('miss') - lic
    lines = ['### placepictures stats' + (' (dry run: nothing written)' if dry else ''), '',
             '- places: %d total, %d with a picture, %d still missing, %d added this run' % (total, have, max(total - have, 0), added),
             '- refusals: no author %d, licence not allowed %d, other (nothing usable) %d' % (noauth, lic, other),
             '- added per source: ' + (', '.join('%s %d' % (n, s['found']) for n, s in st.items() if n != 'large') or 'none'),
             '- larger copies made: %d' % large]
    return '\n'.join(lines) + '\n'

def main(argv=None, root=ROOT):
    a = list(sys.argv[1:] if argv is None else argv); opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    only = opt('--strategy', 'all'); limit = int(opt('--limit', 120)); max_mb = float(opt('--max-mb', 25))
    if only not in ['all', 'large'] + [s[0] for s in STRATEGIES]: print('unknown strategy', only); return 1
    w = pp.PlacePhotos(root); units, shared = load_units(os.path.join(root, 'data', 'places'))
    if w.pics and any('wiki' not in r for r in w.pics.values()): print('places.json is keyed by title, not by place id: this job needs the id-keyed files (migration #906)'); return 1
    print('%d places with a title, %d skipped because another place has the same title: %s' % (len(units), len(shared), ', '.join(sorted(u['id'] for u in shared)) or 'none'))
    stats, stopped = acquire(w, units, only=only, limit=limit, max_bytes=int(max_mb * 1_000_000), again='--again' in a, dry='--dry' in a, large=make_large)
    for name, s in stats.items():
        if name == 'large': print('summary large: tried %d, made %d, none possible %d' % (s['tried'], s['made'], s['none']))
        else: print('summary %s: tried %d, found %d, nothing %d, refused (no author) %d, tried again later %d, larger copies %d (none possible %d)' % (name, s['tried'], s['found'], s['miss'], s['refused'], s['retry'], s['large'], s['nolarge']))
    print('added %d pictures, %d larger copies' % (sum(s['found'] for s in stats.values()), sum(s['large'] + s['made'] for s in stats.values())))
    block = stats_block(w, dict(places=len(units) + len(shared), strategies=stats), dry='--dry' in a); print(block)
    try:
        with open('placepictures_stats.md', 'w', encoding='utf-8') as f: f.write(block)   # not committed: the workflow may put it in the PR body
    except OSError as ex: print('could not write placepictures_stats.md:', ex)
    if '--dry' not in a:
        bad = pp.PlacePhotos(root).check()
        if bad: print('CHECK FAILED:'); print('\n'.join(bad[:30])); return 1
    return 2 if stopped else 0

if __name__ == '__main__': sys.exit(main())
