#!/usr/bin/env python3
"""placepictures.py: the ONE job that finds a picture for a place that has none (docs/DATA-PLAN.md, step 4; #887).
Usage: placepictures.py [--strategy all|wikipedia|commons|nearby|category|openverse|large] [--limit N] [--max-mb N] [--minutes N] [--repair-limit N] [--again] [--dry]   (run from the repository root)

It replaces the five acquire jobs for place pictures (jobs/photos.py, commonsplacephotos.py, commonsnearby.py, commonscategory.py, openverseplaces.py), which each wrote the files and lists in their own way. Here the five
SOURCES are strategies tried in this order, and a place stops at the first one that gives an accepted picture:
  wikipedia  the picture of the place's Wikipedia page (photos.one)
  commons    Wikidata's image property, then the file's licence on Commons (place_sources.pick)
  nearby     Commons files geotagged within 1.5 km whose name shares a distinctive word with the place (place_sources.match)
  category   the place's own Commons category (place_sources.good_category, choose: other-state and other-country files are refused, #891)
  openverse  US places only: an Openverse photograph that names the place and the state, with a named creator (place_sources.openverse_candidates)
The per-source rules live in lib/place_sources.py (one function per source, moved there from the old jobs unchanged): this file decides only the order, the holds, the author rule and the writing.

The larger copy (400 px WebP, the full-width hero of the place page, #727) is made HERE too, right after a picture is accepted and in the SAME commit (PlacePhotos.put, then put_large), so a picture never lands without its pair when
one can be made. Commons cannot thumbnail some originals (a TIFF or a very large file answers HTTP 400; Karavasta Lagoon, Wupatki National Monument, Leasburg Dam State Park): that picture is kept alone, the app shows the small one
(ground rule 10) and the log says so. A picture from another source than Commons has no larger copy to make. `--strategy large` makes the larger copy for the pictures that have none (no new pictures); `all` does that as its last step,
so a copy that failed once is tried again by the next run. This replaces jobs/largeplacephotos.py and its workflow.

Everything is keyed by PLACE ID and written only through lib/place_photos.py (PlacePhotos.put / miss / note_tried / commit: files first, then lists). It needs the id-keyed files the migration (jobs/rekeyplacephotos.py) makes.
A found row carries `wiki` = the place's imgwiki title, which is how the app finds a picture today; so a place whose title is shared with another place is skipped (the migration removed those pictures for the same reason) until the app looks pictures up by id.
Holds (when a source is tried again for a place that gave nothing): wikipedia, as photos.py did, while the missing record has not expired (photo_registry.negative_entry: 30 days for the permanent reasons); each other source RETRY_DAYS (30 days) after its date
in photos/places_tried.json {id: {source: date}}. A transient failure (a download that failed) is recorded nowhere and is tried again by the next run.
Author rule (#887, owner 15 Nov): a CC BY or CC BY-SA picture needs a named author. When the stored credit says unknown, Commons is asked once more (authorlookup.lookup: the Artist or Attribution field, or the uploader when the credit says own work);
no name found = the picture is refused and the place is recorded as 'notfree' for wikipedia, or as tried for the other sources, with the reason in the log.
Caps: --minutes of time (default 120: the run stops cleanly and keeps what it has; the workflow's 170-minute timeout would cancel it and lose the run), --max-mb of pictures kept (default 25), --limit places per strategy (default 0 = all left, #887); pictures are committed every 25 finds, so a stopped run resumes. A run that finds nothing and changes no ledger writes no file.
Resume contract (#1183, lib/runbudget.py): prints `more: N` and exits 3 when the time or size budget stopped it with N places still due and untried by this run; 0 when none; 2 when a source stopped it (do not chain).
--dry prints what would be kept and writes nothing (later strategies then see no new missing places). Exit 2 when a source stopped the run (throttled three times, or refused)."""
import collections, datetime, glob, hashlib, io, json, os, re, shutil, sys, tempfile, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
import runbudget, wm, place_photos as pp, photo_registry as pr
import author_lookup as al, author_repair as ar
from place_sources import Res, Vetted, now_iso, SOURCES, find_wikipedia, find_commons, find_nearby, find_category, find_openverse   # noqa: F401 (re-exported: the tests and callers use pj.Res, pj.Vetted, pj.find_*)

COMMIT_EVERY = 25
COMMONS_THUMBS = 'https://upload.wikimedia.org/wikipedia/commons/thumb/'; LARGE_SIZE = 400; LARGE_QUALITY = 70


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
    """(entry, '') when the picture may be kept, with the author filled in if Commons knows one; (None, why) for a picture with no author to be found (any licence)."""
    entry = dict(entry, a=al.clean(entry.get('a')) or entry.get('a'))   # the one stored form (lib/author_clean.py)
    if not al.unknown(entry.get('a')): return entry, ''   # every licence needs a named author (owner, 25 Nov, #887)
    fn = al.file_of(entry.get('p'))
    if fn:
        cls, name = al.lookup(fn)
        if cls != 'none' and name: return dict(entry, a=name), ''
    return None, 'any licence with no author'

def measure(entry, jpg):
    """The row with its measured fields (media type, size, sha256, review status), made by photo_registry.migrate_places on a scratch copy so nothing else in the repository is rewritten."""
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, 'places.json'), 'w', encoding='utf-8') as f: json.dump({'x': entry}, f)
        with open(os.path.join(d, entry['f']), 'wb') as f: f.write(jpg)
        pr.migrate_places(os.path.join(d, 'places.json'), d)
        with open(os.path.join(d, 'places.json'), encoding='utf-8') as f: return json.load(f)['x']
    finally: shutil.rmtree(d, ignore_errors=True)

# --- the five sources (wikipedia, commons, nearby, category, openverse) live in lib/place_sources.py; STRATEGIES is its SOURCES list, in the order they are tried
STRATEGIES = SOURCES

def held(w, pid, source, days, today, unit=None):
    """True while the source must not try this place again. With the place (`unit`), a miss recorded for another point, name or title no longer holds."""
    if days is None: return pr.cache_active(w.miss_.get(pid), inputs=pr.place_inputs(unit) if unit else None)
    return w.tried.get(pid, {}).get(source, '') > (today - datetime.timedelta(days=days)).isoformat()

def acquire(w, units, strategies=None, only='all', limit=0, max_bytes=25_000_000, again=False, dry=False, today=None, log=print, large=None, minutes=None, clock=time.monotonic, report=None):
    """Runs the strategies in order over the places that have no picture, then (strategy large, or all) makes the missing larger copies. Returns (stats, stopped): per-strategy counts and the strategies a source stopped.
    large: make_large, or None to make no larger copies (the tests of the sources do not download)."""
    today = today or datetime.date.today(); strategies = STRATEGIES if strategies is None else strategies
    stats = collections.OrderedDict(); stopped = []; spent = 0; pending = 0
    late = runbudget.Budget(minutes, clock).late; halted = False   # the time budget (lib/runbudget.py): the run ends cleanly and keeps what it has (the workflow's own timeout would cancel it and lose the run)
    tried_now = collections.defaultdict(set)   # strategy -> place ids this run tried (never counted as still due)
    def due(name, applies, days, unit_held=True): return [u for u in units if not w.has(u['id']) and applies(w, u) and (again or not held(w, u['id'], name, days, today, u))]
    for name, find, applies, days in strategies:
        if only not in ('all', name): continue
        s = stats[name] = collections.Counter()
        todo = due(name, applies, days)
        if limit: todo = todo[:limit]
        log('strategy %s: %d places to try' % (name, len(todo)))
        try:
            for u, r in find(todo):
                pid = u['id']; s['tried'] += 1; tried_now[name].add(pid)
                if r.kind == 'found':
                    entry, why = vet(r.entry)
                    if entry is None:
                        s['refused'] += 1; log('refused %s %s (%s) - %s' % (name, pid, u['title'], why))
                        if not dry: (w.miss(pid, 'notfree', 'wikipedia', inputs=pr.place_inputs(u)) if name == 'wikipedia' else w.note_tried(pid, name)); pending += 1
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
                    if not dry: (w.miss(pid, r.status, 'wikipedia', inputs=pr.place_inputs(u)) if name == 'wikipedia' else w.note_tried(pid, name)); pending += 1
                else: s['retry'] += 1; log('retry %s %s (%s) - %s' % (name, pid, u['title'], r.why))
                if pending >= COMMIT_EVERY and not dry: w.commit(); pending = 0
                if spent >= max_bytes: log('STOP: %d KB of pictures kept (the cap); the rest waits for the next run' % (spent // 1024)); halted = True; break
                if late(): log('STOP: the time budget of %s minutes is spent; the rest waits for the next run' % minutes); halted = True; break
        except RuntimeError as ex:
            stopped.append(name); log('STOP %s: %s (nothing more is tried from this source; ask the owner)' % (name, ex))
        if pending and not dry: w.commit(); pending = 0   # a run that changed nothing writes nothing
        if halted or spent >= max_bytes or late(): halted = True; break
    large_left = lambda: sorted(pid for pid, e in w.pics.items() if e.get('f') and not w.has_large(pid) and commons_file_name(e.get('p')) and pid not in tried_large)
    tried_large = set()
    if only in ('all', 'large') and large is not None and not halted:
        s = stats['large'] = collections.Counter()
        todo = large_left()
        if limit: todo = todo[:limit]
        log('strategy large: %d pictures without a larger copy' % len(todo))
        for pid in todo:
            s['tried'] += 1; tried_large.add(pid)
            if dry: log('would try a larger copy for %s' % pid); continue
            webp, lwhy = large(w.pics[pid])
            if webp: w.put_large(pid, webp); s['made'] += 1; spent += len(webp); pending += 1; log('larger copy large %s %d KB' % (pid, round(len(webp) / 1024)))
            else: s['none'] += 1; log('no larger copy large %s (%s) - %s; the small picture stays' % (pid, w.pics[pid].get('wiki', ''), lwhy))
            if pending >= COMMIT_EVERY: w.commit(); pending = 0
            if spent >= max_bytes: log('STOP: %d KB kept (the cap); the rest waits for the next run' % (spent // 1024)); halted = True; break
            if late(): log('STOP: the time budget of %s minutes is spent; the rest waits for the next run' % minutes); halted = True; break
        if pending and not dry: w.commit(); pending = 0   # a run that changed nothing writes nothing
    more = 0
    if halted and not stopped:   # still due and not tried by this run (the resume contract, lib/runbudget.py)
        for name, find, applies, days in strategies:
            if only in ('all', name): more += sum(1 for u in due(name, applies, days) if u['id'] not in tried_now[name])
        if only in ('all', 'large') and large is not None: more += len(large_left())
    if report is not None: report['more'] = more
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

def main(argv=None, root=ROOT, strategies=None, large=make_large):
    """strategies and large are what the tests give in place of the real sources and the Commons download (#1028); None and make_large are the real ones."""
    a = list(sys.argv[1:] if argv is None else argv); opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    only = opt('--strategy', 'all'); limit = int(opt('--limit', 0)); max_mb = float(opt('--max-mb', 25)); minutes = float(opt('--minutes', 120))
    if only not in ['all', 'large'] + [s[0] for s in STRATEGIES]: print('unknown strategy', only); return 1
    w = pp.PlacePhotos(root); units, shared = load_units(os.path.join(root, 'data', 'places'))
    if w.pics and any('wiki' not in r for r in w.pics.values()): print('places.json is keyed by title, not by place id: this job needs the id-keyed files (migration #906)'); return 1
    print('%d places with a title, %d skipped because another place has the same title: %s' % (len(units), len(shared), ', '.join(sorted(u['id'] for u in shared)) or 'none'))
    rl = int(opt('--repair-limit', 40)); dry = '--dry' in a; t0 = time.monotonic()
    report = {}; stats, stopped = acquire(w, units, strategies, only=only, limit=limit, max_bytes=int(max_mb * 1_000_000), again='--again' in a, dry='--dry' in a, large=large, minutes=minutes, report=report)
    for name, s in stats.items():
        if name == 'large': print('summary large: tried %d, made %d, none possible %d' % (s['tried'], s['made'], s['none']))
        else: print('summary %s: tried %d, found %d, nothing %d, refused (no author) %d, tried again later %d, larger copies %d (none possible %d)' % (name, s['tried'], s['found'], s['miss'], s['refused'], s['retry'], s['large'], s['nolarge']))
    print('added %d pictures, %d larger copies' % (sum(s['found'] for s in stats.values()), sum(s['large'] + s['made'] for s in stats.values())))
    if rl:   # the author repair step (#887, lib/author_repair.py): after the sources, only when none of them stopped, inside the same time budget
        if stopped: print('author repair skipped: a source stopped this run')
        else:
            rs, _ = ar.repair_step(w, limit=rl, dry=dry, late=(lambda: time.monotonic() - t0 >= minutes * 60) if minutes else None); print(ar.summary(rs))
            if not dry and (rs['fixed'] or rs['none']): w.commit()
    more = report.get('more', 0); print(runbudget.more_line(more))
    block = stats_block(w, dict(places=len(units) + len(shared), strategies=stats), dry='--dry' in a); print(block)
    try:
        with open('placepictures_stats.md', 'w', encoding='utf-8') as f: f.write(block)   # not committed: the workflow may put it in the PR body
    except OSError as ex: print('could not write placepictures_stats.md:', ex)
    if '--dry' not in a:
        bad = pp.PlacePhotos(root).check()
        if bad: print('CHECK FAILED:'); print('\n'.join(bad[:30])); return 1
    return runbudget.exit_code(stopped, more)

if __name__ == '__main__': sys.exit(main())
