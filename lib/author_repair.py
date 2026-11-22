"""author_repair.py: give a picture credited to an unknown author its named author (#887; owner, 17 Nov: "a repair step goes into each existing weekly picture job, through one shared lib function").

repair(row) looks at the source page the row already records (`p`) and returns {'a': name, 'l': licence, 'lu': licence link} or None:
  Commons file page   -> the file's Artist / Attribution / "own work" uploader (lib/author_lookup.py) and its licence
  Openverse image     -> the record's creator and licence (lib/openverse_api.py)
  GBIF occurrence     -> the media's creator or rightsHolder and licence (GBIF allows CC0 and CC BY only)
  iNaturalist photo   -> not looked up (no single-photo address is known to be right); the row is left alone
A credit is returned only when the name survives lib/author_clean.py AND the licence is one lib/licences.py allows for that source (CC0, CC BY, CC BY-SA, Public domain). Otherwise None.
repair_step(w) is the small step at the end of a weekly picture job: it walks the writer's rows credited to 'unknown author' (any spelling author_clean treats as none), skips those tried
less than contracts.SOURCE_RETRY_DAYS ago (the ledger {id: {source: date}} the writers already keep, source 'author-repair'), writes a found credit through the writer's own set_credit, records a
miss with note_repair_tried, and stops at its lookup cap, at the job's time budget, or at the first throttle. Network through lib/wm.py (hosts already allowed); `get` is the test seam."""
import collections, datetime, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wm, licences, contracts, author_clean as ac, author_lookup as al, openverse_api as ov

SOURCE = 'author-repair'   # the ledger key
COMMONS = ('https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo|revisions&iiprop=extmetadata'
           '&iiextmetadatafilter=Artist|Credit|Attribution|LicenseShortName|LicenseUrl&rvprop=user&rvdir=newer&rvlimit=1&titles=')
GBIF_LICENCES = {'http://creativecommons.org/publicdomain/zero/1.0': ('CC0', 'https://creativecommons.org/publicdomain/zero/1.0'),
                 'http://creativecommons.org/licenses/by/4.0': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0')}


def is_unknown(row):
    """True for a row whose author is 'Unknown author', 'Unknown' or any text author_clean treats as no author (any case)."""
    return ac.clean_author((row or {}).get('a')) == ''


def _credit(name, lic, link, source):
    """The credit when the name is usable and the licence allowed for `source`, else None."""
    name = ac.clean_author(name)
    if not name or not lic or not licences.ok(source, lic): return None
    return {'a': name, 'l': lic, 'lu': link or ''}


def _commons(p, get):
    fn = al.file_of(p).replace('_', ' ')
    if not fn: return None
    j = get(COMMONS + urllib.parse.quote('File:' + fn)) or {}
    page = next(iter(((j.get('query') or {}).get('pages') or {}).values()), {})
    meta = ((page.get('imageinfo') or [{}])[0]).get('extmetadata') or {}
    uploader = ((page.get('revisions') or [{}])[0]).get('user') or ''
    v = lambda k: al.strip((meta.get(k) or {}).get('value'))
    cls, name = al.classify(meta, uploader)
    return _credit(name, v('LicenseShortName'), v('LicenseUrl'), 'Wikimedia')


def _openverse(p, get):
    m = re.search(r'/image/([0-9a-f-]{36})', p)
    if not m: return None
    r = get(ov.API + m.group(1) + '/') or {}; lic = ov.licence_of(r)
    return _credit(r.get('creator'), lic[0], lic[1], 'Openverse') if lic else None


def _gbif(p, get):
    m = re.search(r'/occurrence/(\d+)', p)
    if not m: return None
    rec = get('https://api.gbif.org/v1/occurrence/%s' % m.group(1)) or {}
    for media in rec.get('media') or []:
        lic = GBIF_LICENCES.get((media.get('license') or '').strip().rstrip('/').replace('https://', 'http://', 1))
        c = _credit(media.get('creator') or media.get('rightsHolder'), lic[0], lic[1], 'GBIF') if lic else None
        if c: return c
    return None


def repair(row, get=None):
    """The corrected credit {'a', 'l', 'lu'} for a row credited to an unknown author, or None (not unknown, no page, no named author, licence not allowed). May raise RuntimeError when wm.get gives up on a throttle."""
    if not is_unknown(row): return None
    get = get or wm.get; p = (row.get('p') or '').strip()
    try: u = urllib.parse.urlsplit(p)
    except ValueError: return None
    if u.scheme != 'https': return None
    if u.hostname == 'commons.wikimedia.org': return _commons(p, get)
    if u.hostname == 'openverse.org': return _openverse(p, get)
    if u.hostname == 'www.gbif.org': return _gbif(p, get)
    return None


def held(w, rid, today):
    """True while this row was looked up less than SOURCE_RETRY_DAYS ago (the same ledger and window the other sources use)."""
    return w.tried.get(rid, {}).get(SOURCE, '') > (today - datetime.timedelta(days=contracts.SOURCE_RETRY_DAYS)).isoformat()


def repair_step(w, today=None, limit=40, late=None, log=print, get=None, dry=False):
    """The step at the end of a weekly picture job. `w` is a writer with pics, tried, set_credit, note_repair_tried (PlacePhotos, SpeciesPhotos, JourneyPhotos). limit = lookups this run (0 = none);
    late() true = the job's time budget is spent. Returns (Counter, stopped). The caller commits."""
    today = today or datetime.datetime.now(datetime.timezone.utc).date(); s = collections.Counter(); stopped = False
    now = datetime.datetime.combine(today, datetime.time(), datetime.timezone.utc)
    for rid in sorted(w.pics):
        if not is_unknown(w.pics[rid]): continue
        s['unknown'] += 1
        if held(w, rid, today): s['held'] += 1; continue
        if dry: s['later'] += 1; continue
        if not limit or s['looked'] >= limit: s['later'] += 1; continue
        if late and late(): log('STOP author repair: the time budget is spent; the rest waits for the next run'); stopped = True; s['later'] += 1; break
        s['looked'] += 1
        try: c = repair(w.pics[rid], get)
        except RuntimeError as ex: log('STOP author repair: %s (nothing more is looked up this run)' % ex); stopped = True; s['looked'] -= 1; s['later'] += 1; break
        if c: w.set_credit(rid, c); s['fixed'] += 1; log('author %s -> %s (%s)' % (rid, c['a'], c['l']))
        else: w.note_repair_tried(rid, now=now); s['none'] += 1; log('author %s: no named author with an allowed licence; tried again in %d days' % (rid, contracts.SOURCE_RETRY_DAYS))
    return s, stopped


def summary(s):
    return 'author repair: %d unknown, %d held, %d looked up, %d fixed, %d without a named author or licence (held %d days), %d left for the next run' % (
        s['unknown'], s['held'], s['looked'], s['fixed'], s['none'], contracts.SOURCE_RETRY_DAYS, s['later'])
