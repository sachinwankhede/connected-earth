#!/usr/bin/env python3
"""speciespictures.py: the ONE job that finds a picture for a species that has none (docs/DATA-PLAN.md, "Species pictures"; #934, phase 4).
Usage: speciespictures.py [--strategy all|wikipedia|commons|gbif|openverse|inaturalist|medium|large] [--limit N] [--max-mb N] [--minutes N] [--again] [--dry]   (run from the repository root)

It replaces the old species jobs (speciesphotos.py + hostphotos.py, commonsphotos.py, gbifphotos.py, openversephotos.py, inaturalistphotos.py, largephotos.py), which each wrote the files and lists in their own way. The SOURCES
(lib/species_sources.py, one function each, the old rules copied with the same behaviour) are strategies tried in this order, and a species stops at the first one that gives an accepted picture:
  wikipedia    the picture of the species' Wikipedia page, with its licence and author from Commons
  commons      Wikidata's image property, then the file's licence on Commons
  gbif         GBIF occurrence photos (CC0 and CC BY, named author, not iNaturalist, not a specimen sheet)
  openverse    an Openverse photograph that names the species, with a named creator (not for abiotic rows)
  inaturalist  iNaturalist's taxon photos, CC0, CC BY and CC BY-SA with the photographer named (not for abiotic rows)
This file decides only the order, the holds, the author rule and the writing.

Everything is keyed by SPECIES ID (`sid`) and written only through lib/species_photos.py (SpeciesPhotos.put / put_medium / put_large / miss / note_tried / commit: files first, then lists); it needs the sid-keyed files the migration
(jobs/rekeyspeciesphotos.py) makes. A Wikipedia title shared by several species rows (151 titles, 618 rows, mostly non-organisms) is fetched ONCE: the first row stands for the title, and the same bytes are put for every sid that has it
(each with its own entry and credit, so each species is checked on its own; the file is shared because its name is the hash of the picture). --limit counts titles, not species.

The 192 px copy (species-md, the photo tiles, #669) and the 400 px copy (species-lg, the species page) are made HERE too, right after a picture is accepted and in the SAME commit (put, then put_medium and put_large), from one download of
the source's own larger thumbnail (lib/species_sources.source_urls: Commons 500 px, else 330 px; Openverse and iNaturalist their own size). A picture whose copies cannot be made (a Commons thumbnail that answers HTTP 400, a GBIF picture, which
has no larger source address) is kept alone and the log says so (ground rule 10). `--strategy medium` / `large` makes the missing 192 px / 400 px copies of pictures that have a source address (no new pictures); `all` does both as its last step,
so a copy that failed once is tried again by the next run. This replaces hostphotos.py's download and largephotos.py.
Holds (when a source is tried again for a species that gave nothing): wikipedia while the missing record has not expired (photo_registry.negative_entry: 30 days for the permanent reasons); each other source RETRY_DAYS (30 days) after its date
in photos/species_tried.json {sid: {source: date}}. A transient failure (a download that failed, a request that failed) is recorded nowhere and is tried again by the next run.
Author rule (#934, owner 15 Nov): a CC BY or CC BY-SA picture needs a named author. When the credit says unknown, Commons is asked once more (author_lookup.lookup: the Artist or Attribution field, or the uploader when the credit says own work);
no name found = the picture is refused and the species is recorded as 'notfree' for wikipedia, or as tried for the other sources, with the reason in the log. The writer refuses it too (put raises ValueError): that is recorded the same way.
Caps: --limit titles per strategy (default 0 = all left, #1183), --minutes of time (default 120: the run stops cleanly between two titles and keeps what it has), --max-mb of pictures kept (default 25); committed every 25 sids, so a stopped run resumes.
RESUME CONTRACT (#1183, shared in lib/runbudget.py): the job prints `more: N` (titles still due and not tried by this run) and exits 3 when the time or size budget stopped it with N > 0; 0 when nothing is left; 2 when a source stopped it (do not chain); 1 on error.
A chain simply runs the job again while it exits 3: every title tried is written to the per-source ledger (held 30 days), the order is fixed, so the next run starts at what is still untried and the chain ends. A run that finds nothing and changes no ledger writes no file.
--dry prints what would be kept and writes nothing (later strategies then see no new missing species). Exit 2 when a source stopped the run (throttled three times, or refused)."""
import collections, datetime, glob, io, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import runbudget, wm, species_photos as sp, species_pics, photo_registry as pr
import author_lookup as al, author_repair as ar
from species_sources import Res, Vetted, SOURCES, source_urls   # noqa: F401 (Res and Vetted re-exported for callers and tests)

COMMIT_EVERY = 25
SMALL_SIZE = 96; SMALL_QUALITY = 72; MEDIUM_SIZE = 192; LARGE_SIZE = 400; COPY_QUALITY = 70   # the sizes and WebP qualities hostphotos.py and largephotos.py used
STRATEGIES = SOURCES


def load_units(root):
    """One dict per species row that has a Wikipedia title (sid, title, name, latin, abiotic) in sid order. `abiotic` is true when ANY row with the same title is marked abiotic (soil, lake, water: a search finds the thing the word names, #511)."""
    rows = []
    for f in glob.glob(os.path.join(root, 'data', 'species', 'rows', '*', '*.json')):
        try:
            with open(f, encoding='utf-8') as h: r = json.load(h)
        except (OSError, ValueError): continue
        if isinstance(r, dict) and r.get('sid') and r.get('wiki'): rows.append(r)
    abiotic = {r['wiki'] for r in rows if r.get('cat') == 'abiotic'}
    return [dict(sid=r['sid'], title=r['wiki'], name=r.get('name') or '', latin=r.get('latin') or '', abiotic=r['wiki'] in abiotic) for r in sorted(rows, key=lambda r: r['sid'])]

# --- the pictures: 96 px, then the 192 px and 400 px copies
def resize(raw, size, quality):
    """(WebP bytes, (w, h)) of the image `raw` at most size px on its longer side, or (None, None) when it is not an image."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert('RGB'); im.thumbnail((size, size)); buf = io.BytesIO(); im.save(buf, 'WEBP', quality=quality, method=6)
        return buf.getvalue(), im.size
    except Exception: return None, None

def small(raw): return resize(raw, SMALL_SIZE, SMALL_QUALITY)[0]

def download_first(urls, get):
    """Bytes of the first address that downloads, or None. A thumbnail that Commons cannot make answers HTTP 400: skipped, not fatal."""
    for u in urls:
        try: raw = get(u, raw=True)
        except RuntimeError as e: print('skipped', u[-70:], '-', e, flush=True); continue
        if raw: return raw
    return None

def make_copies(entry, need=('medium', 'large'), get=None):
    """({'medium': bytes, 'large': bytes} for what was asked and could be made, why) from ONE download of the source's larger thumbnail; why says what is missing ('' when nothing is)."""
    urls = source_urls(entry.get('u'))
    if not urls: return {}, 'no larger source address (%s)' % (entry.get('src') or 'Wikipedia/Commons path missing')
    raw = download_first(urls, get or wm.get)
    if not raw: return {}, 'the source has no thumbnail for it'
    out = {}
    for which in need:
        data, _ = resize(raw, MEDIUM_SIZE if which == 'medium' else LARGE_SIZE, COPY_QUALITY)
        if data: out[which] = data
    return out, ('' if len(out) == len(need) else 'the thumbnail is not an image')

# --- the author rule (the same as placepictures.vet)
def vet(entry):
    """(entry, '') when the picture may be kept, with the author filled in if Commons knows one; (None, why) for a picture with no author to be found (any licence)."""
    entry = dict(entry, a=al.clean(entry.get('a')) or entry.get('a'))
    if not al.unknown(entry.get('a')): return entry, ''   # every licence needs a named author (owner, 25 Nov, #887)
    fn = al.file_of(entry.get('p'))
    if fn:
        cls, name = al.lookup(fn)
        if cls != 'none' and name: return dict(entry, a=name), ''
    return None, 'any licence with no author'

def held(w, sid, source, days, today):
    """True while the source must not try this species again."""
    if days is None: return pr.cache_active(w.miss_.get(sid))
    return w.tried.get(sid, {}).get(source, '') > (today - datetime.timedelta(days=days)).isoformat()

def by_title(units):
    """{title: [units]} in order of first appearance: one fetch per title."""
    out = collections.OrderedDict()
    for u in units: out.setdefault(u['title'], []).append(u)
    return out

def copy_files(w, wanted):
    """[(file, [(sid, needed copies)])] in sorted sid order: one download per picture file (species that show the same picture share it)."""
    has = {'medium': w.has_medium, 'large': w.has_large}; by_file = collections.OrderedDict()
    for sid in sorted(w.pics):
        e = w.pics[sid]; need = tuple(k for k in wanted if not has[k](sid))
        if need and e.get('f') and source_urls(e.get('u')): by_file.setdefault(e['f'], []).append((sid, need))
    return list(by_file.items())

def acquire(w, units, strategies=None, only='all', limit=0, max_bytes=25_000_000, again=False, dry=False, today=None, log=print, copies=None, minutes=None, clock=None, report=None):
    """Runs the strategies in order over the species that have no picture (one fetch per title), then (strategy medium, large or all) makes the missing copies. Returns (stats, stopped): per-strategy counts and the strategies a source stopped.
    copies: make_copies, or None to make no copies (the tests of the sources do not download).
    minutes: the time budget (lib/runbudget.py). report: a dict that gets 'more' = the titles (and copy files) still due and not tried by this run when a budget (time or size) stopped it, else 0."""
    today = today or datetime.date.today(); strategies = STRATEGIES if strategies is None else strategies
    stats = collections.OrderedDict(); stopped = []; spent = 0; pending = 0
    late = runbudget.Budget(minutes, clock or time.monotonic).late; halted = False
    tried_now = collections.defaultdict(set)   # strategy -> titles this run tried (never counted as still due)
    def due(name, applies, days): return by_title([u for u in units if not w.has(u['sid']) and applies(w, u) and (again or not held(w, u['sid'], name, days, today))])
    for name, find, applies, days in strategies:
        if only not in ('all', name): continue
        s = stats[name] = collections.Counter()
        groups = due(name, applies, days)
        reps = [g[0] for g in groups.values()]
        if limit: reps = reps[:limit]
        log('strategy %s: %d titles to try (%d species)' % (name, len(reps), sum(len(groups[r['title']]) for r in reps)))
        try:
            for u, r in find(reps):
                sids = [x['sid'] for x in groups[u['title']]]; t = u['title']; s['tried'] += 1; tried_now[name].add(t); label = '%s (%s)' % (','.join(sids), t)
                note = lambda why, status=None: [(w.miss(sid, status or 'notfree', 'wikipedia') if name == 'wikipedia' else w.note_tried(sid, name)) for sid in sids]
                if r.kind == 'found':
                    entry, why = vet(r.entry)
                    if entry is None:
                        s['refused'] += len(sids); log('refused %s %s - %s' % (name, label, why))
                        if not dry: note(why); pending += len(sids)
                        continue
                    webp = small(r.jpg)
                    if not webp: s['retry'] += 1; log('retry %s %s - the picture is not an image' % (name, label)); continue
                    entry = dict(entry, wiki=t); s['found'] += len(sids); spent += len(webp)
                    log('yes %s %s -> %s | %s | %s' % (name, label, r.note or entry.get('p', ''), entry.get('l', ''), entry.get('a', '')))
                    if dry: continue
                    kept = []
                    for sid in sids:
                        try: w.put(sid, entry, webp); kept.append(sid)
                        except ValueError as ex:   # the writer's own author rule: recorded like a refusal
                            s['refused'] += 1; s['found'] -= 1; log('refused %s %s - %s' % (name, sid, ex)); w.note_tried(sid, name)
                        pending += 1
                    if kept and copies is not None:   # the copies go into the same commit as the picture; one download for the title
                        got, cwhy = copies(entry)
                        for sid in kept:
                            if 'medium' in got: w.put_medium(sid, got['medium'])
                            if 'large' in got: w.put_large(sid, got['large'])
                        spent += sum(len(b) for b in got.values()); s['copies'] += len(got) and 1
                        if got: log('copies %s %s %s' % (name, label, ', '.join('%s %d KB' % (k, round(len(b) / 1024)) for k, b in sorted(got.items()))))
                        if cwhy: s['nocopy'] += 1; log('no %s copy %s %s - %s; the small picture stays' % ('larger' if got else 'larger or 192 px', name, label, cwhy))
                elif r.kind == 'miss':
                    s['miss'] += len(sids); s['refused_licence'] += len(sids) * (r.status == 'notfree'); log('no %s %s - %s' % (name, label, r.why))
                    if not dry:
                        for sid in sids: (w.miss(sid, r.status, 'wikipedia') if name == 'wikipedia' else w.note_tried(sid, name))
                        pending += len(sids)
                else: s['retry'] += 1; log('retry %s %s - %s' % (name, label, r.why))
                if pending >= COMMIT_EVERY and not dry: w.commit(); pending = 0
                if spent >= max_bytes: log('STOP: %d KB of pictures kept (the cap); the rest waits for the next run' % (spent // 1024)); halted = True; break
                if late(): log('STOP: the time budget of %s minutes is spent; the rest waits for the next run' % minutes); halted = True; break
        except RuntimeError as ex:
            stopped.append(name); log('STOP %s: %s (nothing more is tried from this source; ask the owner)' % (name, ex))
        if pending and not dry: w.commit(); pending = 0   # a run that changed nothing writes nothing
        if halted or spent >= max_bytes or late(): halted = True; break
    wanted = [k for k in ('medium', 'large') if only in ('all', k)]
    tried_files = set(); copy_todo = lambda: [(f, m) for f, m in copy_files(w, wanted) if f not in tried_files]
    if wanted and copies is not None and not halted:
        s = stats['copies'] = collections.Counter()
        todo = copy_todo()
        if limit: todo = todo[:limit]
        log('strategy %s: %d pictures without a copy' % ('+'.join(wanted), len(todo)))
        for f, members in todo:
            s['tried'] += 1; tried_files.add(f); sids = [m[0] for m in members]; need = tuple(sorted({k for m in members for k in m[1]}))
            if dry: log('would try copies for %s' % ','.join(sids)); continue
            got, cwhy = copies(w.pics[sids[0]], need)
            for sid, n in members:
                if 'medium' in got and 'medium' in n: w.put_medium(sid, got['medium'])
                if 'large' in got and 'large' in n: w.put_large(sid, got['large'])
            if got: s['made'] += 1; spent += sum(len(b) for b in got.values()); pending += len(sids); log('copies %s %s' % (','.join(sids), ', '.join('%s %d KB' % (k, round(len(b) / 1024)) for k, b in sorted(got.items()))))
            if cwhy: s['none'] += 1; log('no copy %s - %s; the small picture stays' % (','.join(sids), cwhy))
            if pending >= COMMIT_EVERY: w.commit(); pending = 0
            if spent >= max_bytes: log('STOP: %d KB kept (the cap); the rest waits for the next run' % (spent // 1024)); halted = True; break
            if late(): log('STOP: the time budget of %s minutes is spent; the rest waits for the next run' % minutes); halted = True; break
        if pending and not dry: w.commit(); pending = 0
    more = 0
    if halted and not stopped:   # what is still due and was not tried by this run (a transient failure counts once, not again)
        for name, find, applies, days in strategies:
            if only in ('all', name): more += sum(1 for t in due(name, applies, days) if t not in tried_now[name])
        if wanted and copies is not None: more += len(copy_todo())
    if report is not None: report['more'] = more
    return stats, stopped

def stats_block(w, counters, dry=False):
    """The end-of-run stats as a compact Markdown block (pure). counters = {'species': total rows, 'strategies': the per-strategy Counters acquire returns}."""
    st = counters.get('strategies', {}); total = counters.get('species', 0)
    g = lambda k: sum(s[k] for s in st.values()); added = g('found'); lic = g('refused_licence'); noauth = g('refused'); other = g('miss') - lic
    have = len(w.pics) + (added if dry else 0)
    lines = ['### speciespictures stats' + (' (dry run: nothing written)' if dry else ''), '',
             '- species: %d total, %d with a picture, %d still without, %d added this run' % (total, have, max(total - have, 0), added),
             '- refusals: no author %d, licence not allowed %d, other (nothing usable) %d' % (noauth, lic, other),
             '- added per source: ' + (', '.join('%s %d' % (n, s['found']) for n, s in st.items() if n != 'copies') or 'none'),
             '- pictures with copies made: %d' % (g('copies') + g('made'))]
    return '\n'.join(lines) + '\n'

def main(argv=None, root=ROOT):
    a = list(sys.argv[1:] if argv is None else argv); opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    only = opt('--strategy', 'all'); limit = int(opt('--limit', 0)); max_mb = float(opt('--max-mb', 25)); minutes = float(opt('--minutes', 120))
    if only not in ['all', 'medium', 'large'] + [s[0] for s in STRATEGIES]: print('unknown strategy', only); return 1
    if not species_pics.new_shape(root): print('the species pictures are not keyed by species id yet: this job needs the sid-keyed files (migration #934, jobs/rekeyspeciesphotos.py)'); return 1
    w = sp.SpeciesPhotos(root); units = load_units(root)
    shared = collections.Counter(u['title'] for u in units)
    print('%d species rows with a title, %d titles, %d titles shared by %d rows (each fetched once)' % (len(units), len(shared), sum(1 for c in shared.values() if c > 1), sum(c for c in shared.values() if c > 1)))
    rl = int(opt('--repair-limit', 40)); dry = '--dry' in a
    t0 = time.monotonic(); report = {}
    stats, stopped = acquire(w, units, only=only, limit=limit, max_bytes=int(max_mb * 1_000_000), again='--again' in a, dry='--dry' in a, copies=make_copies, minutes=minutes, report=report)
    for name, s in stats.items():
        if name == 'copies': print('summary copies: tried %d, made %d, none possible %d' % (s['tried'], s['made'], s['none']))
        else: print('summary %s: tried %d, found %d, nothing %d, refused (no author) %d, tried again later %d, pictures with copies %d (none possible %d)' % (name, s['tried'], s['found'], s['miss'], s['refused'], s['retry'], s['copies'], s['nocopy']))
    print('added %d pictures' % sum(s['found'] for s in stats.values()))
    if rl:   # the author repair step (#887, lib/author_repair.py): after the sources, only when none of them stopped, inside the same time budget
        if stopped: print('author repair skipped: a source stopped this run')
        else:
            rs, _ = ar.repair_step(w, limit=rl, dry=dry, late=(lambda: time.monotonic() - t0 >= minutes * 60) if minutes else None); print(ar.summary(rs))
            if not dry and (rs['fixed'] or rs['none']): w.commit()
    more = report.get('more', 0); print(runbudget.more_line(more))
    block = stats_block(w, dict(species=len(units), strategies=stats), dry='--dry' in a); print(block)
    try:
        with open('speciespictures_stats.md', 'w', encoding='utf-8') as f: f.write(block)   # not committed: the workflow may put it in the PR body
    except OSError as ex: print('could not write speciespictures_stats.md:', ex)
    if '--dry' not in a:
        bad = sp.SpeciesPhotos(root).check()
        if bad: print('CHECK FAILED:'); print('\n'.join(bad[:30])); return 1
    return runbudget.exit_code(stopped, more)

if __name__ == '__main__': sys.exit(main())
