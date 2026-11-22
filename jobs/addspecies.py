#!/usr/bin/env python3
"""addspecies.py: add species whole or not at all (docs/ADD-SPECIES.md). It composes the existing sources and writers; lib/species_rows.py decides who a candidate is, whether it may be added, and records refusals.
Usage: addspecies.py (--candidates file.json | --titles "Title one|Title two" --kind taxon|group|resource) [--latin "Name"] [--tl N] [--dry] [--limit N] [--minutes N] [--out result.json]   (run from the repository root)

A candidate is {wiki, kind, latin?, name?, tl?, ic?, cat?, desc?, gbif?}: the Wikipedia article, the kind of row, and what a row needs that no source can give (the trophic level of a taxon, the icon, the category of a resource). It carries nothing about places.
For every new candidate the steps run in this order and every one is recorded, whatever the others found:
  picture       lib/species_sources.SOURCES in order, the first accepted picture (licences of #421, a named author); a taxon or group gets the 96, 192 and 400 px copies, a resource the 192 px picture of photos/nodes (lib/node_photos.py)
  taxonomy      GBIF, as jobs/taxonomy.py (a taxon only; a doubtful match counts as missing and is not written to the review file: the refusal ledger holds it)
  summary       the first sentences of the Wikipedia page, as jobs/about.py and species.clean (required for every kind)
  conservation  Wikidata, as jobs/conservation.py (a taxon only; optional: never a reason to refuse)
A candidate with a required step missing (contracts.SPECIES_REQUIRED) is refused and written to data/ledger/species.json with every step's result; nothing else is written. When all are found the files are written first and the row last.
--dry does every lookup and writes nothing. The result of each candidate is {kind, status: added|exists|refused, id, dry, steps, reason}. Exit 2 when a source stopped the run (throttled or refused)."""
import datetime, json, os, sys, time, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import contracts, species, species_rows, creation_ledger
from place_photos import _write_json
from node_photos import NodePhotos, node_id
from species_photos import SpeciesPhotos

ICON_BY_TL = {1: 'grass', 2: 'quad', 3: 'quad', 4: 'hawk'}   # a default only: a candidate names its own icon; the dry run shows it and the pull request spot check covers it


class Stopped(Exception):
    """A source refused or throttled the run: nothing more is tried from it."""


def _dayiso(now): return (now or datetime.date.today()).isoformat()


class Sources:
    """The real sources. Each method returns what it found and why not; none writes anything."""
    def __init__(self, picture_sources=None, get=None):
        import speciespictures as spp, species_sources as ss, wm
        self.spp = spp; self.ss = ss; self.wm = wm; self.get = get or wm.get; self.sources = picture_sources if picture_sources is not None else ss.SOURCES

    def picture(self, unit, kind):
        """({entry, small, copies, source}, trail) or (None, trail). trail = one line per source that was asked, for the ledger."""
        class W:   # a source asks `is_missing` to decide whether it applies to a species with no picture yet
            def is_missing(self, sid): return True
        trail = []
        for name, find, applies, _days in self.sources:
            if not applies(W(), unit): trail.append('%s: not for this kind' % name); continue
            try:
                for _u, r in find([unit]):
                    if r.kind == 'found':
                        entry, why = self.spp.vet(r.entry)
                        if entry is None: trail.append('%s: refused (%s)' % (name, why)); continue
                        small = self.spp.small(r.jpg)
                        if not small: trail.append('%s: the picture is not an image' % name); continue
                        entry = dict(entry, wiki=unit['title'])
                        need = ('medium',) if kind == 'resource' else ('medium', 'large')
                        copies, cwhy = self.spp.make_copies(entry, need, self.get)
                        return {'entry': entry, 'small': small, 'copies': copies, 'source': name, 'copy_note': cwhy}, trail + ['%s: found' % name]
                    trail.append('%s: %s' % (name, r.why))
            except RuntimeError as ex: raise Stopped('%s: %s' % (name, ex))
        return None, trail

    def taxonomy(self, cand):
        """(record, why). Pure GBIF: the same decision as jobs/taxonomy.py."""
        import taxonomy as tx
        row = {'latin': cand['latin'], 'tl': cand.get('tl', 0)}
        try:
            ok, rec = tx.classify(row, tx.lookup(row))
            if not ok and not rec['why'].startswith(('a producer matched an animal', 'a consumer matched', 'confidence')):
                ok2, rec2 = tx.pick(row, tx.by_name(row))
                if ok2: ok, rec = ok2, rec2
        except RuntimeError as ex: raise Stopped('GBIF: %s' % ex)
        return (rec, '') if ok else (None, rec['why'])

    def summary(self, title):
        """(clean text, raw extract, why): the first two sentences of the page after redirects, cleaned as species.about() does."""
        d = self.wm.get('https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&exsentences=2&redirects=1&format=json&titles=' + urllib.parse.quote(title))
        pages = ((d or {}).get('query') or {}).get('pages') or {}
        raw = next((p.get('extract', '') for p in pages.values() if 'missing' not in p), '')
        return summary_of(raw)

    def conservation(self, latin):
        """(entry, why) from Wikidata, as jobs/conservation.py."""
        import conservation as cv
        rows = cv.sparql(cv.query([latin]))
        if rows is None: return None, 'Wikidata did not answer'
        got = cv.parse(rows).get(latin.lower())
        return (got, '') if got else (None, 'no status on Wikidata')


def summary_of(raw):
    """(clean text, raw, why) from a Wikipedia extract; the same tests species.about() applies, so a summary this job accepts survives the next `species.py about`."""
    text = species.clean(raw)
    if not text: return None, raw, 'the page has no text'
    if len(text) <= 30: return None, raw, 'the text is too short'
    if species.NOT_ABOUT.search(text): return None, raw, 'the text is not about the species (a disambiguation page, a person or a place)'
    return text, raw, ''


def build_row(cand, sid, about, now=None):
    kind = cand['kind']
    row = {'latin': (cand.get('latin') or '') if kind != 'resource' else '', 'name': cand.get('name') or cand['wiki'], 'tl': cand.get('tl', 0 if kind == 'resource' else None),
           'wiki': cand['wiki'], 'desc': cand.get('desc', ''), 'ic': cand.get('ic'), 'sid': sid, 'sk': kind, 'about': about, 'src': 'addspecies', 'at': _dayiso(now)}
    if kind == 'resource':
        row['cat'] = cand.get('cat'); row['ic'] = row['ic'] or ({'decomp': 'decomp'}.get(cand.get('cat')))
    else: row['ic'] = row['ic'] or ICON_BY_TL.get(row['tl'])
    if cand.get('badge'): row['badge'] = cand['badge']
    return {k: v for k, v in row.items() if v is not None}


def make_gather(src, root, now=None):
    """The `gather(cand, sid)` lib/species_rows.SpeciesRows.ensure wants: runs every step but identity, writes nothing, returns (steps, row, commit)."""
    def gather(cand, sid):
        kind = cand['kind']; steps = {}; trail = []
        unit = dict(sid=sid, title=cand['wiki'], name=cand.get('name') or cand['wiki'], latin=cand.get('latin') or '', abiotic=cand.get('cat') == 'abiotic')
        pic, trail = src.picture(unit, kind)
        steps['picture'] = {'result': 'found', 'detail': '%s (%s, %s)' % (pic['source'], pic['entry'].get('l', ''), pic['entry'].get('a', ''))} if pic else {'result': 'missing', 'detail': 'no licensed picture; ' + '; '.join(trail)}
        if pic and pic['copy_note']: steps['picture']['detail'] += '; ' + pic['copy_note']
        tax = None
        if kind == 'taxon':
            tax, why = src.taxonomy(cand); steps['taxonomy'] = {'result': 'found', 'detail': '%s %s' % (tax.get('match'), tax.get('gname', ''))} if tax else {'result': 'missing', 'detail': why}
        else: steps['taxonomy'] = {'result': 'skipped', 'detail': 'taxon rows only'}
        text, raw, why = src.summary(cand['wiki']); steps['summary'] = {'result': 'found', 'detail': text[:80]} if text else {'result': 'missing', 'detail': why}
        cons = None
        if kind == 'taxon':
            cons, why = src.conservation(cand['latin']); steps['conservation'] = {'result': 'found', 'detail': cons['c']} if cons else {'result': 'missing', 'detail': why}
        else: steps['conservation'] = {'result': 'skipped', 'detail': 'taxon rows only'}
        row = build_row(cand, sid, text, now) if text else None

        def commit():
            """Files first (the row is written by the caller, last)."""
            if kind == 'resource':
                n = NodePhotos(root); n.put(node_id(cand['wiki']), pic['entry'], pic['copies'].get('medium') or pic['small']); n.commit()
            else:
                w = SpeciesPhotos(root); w.put(sid, pic['entry'], pic['small'])
                for which, data in sorted(pic['copies'].items()): (w.put_medium if which == 'medium' else w.put_large)(sid, data)
                w.commit()
            sp = os.path.join(root, 'data', 'species')
            if tax: _merge(os.path.join(sp, 'taxonomy.json'), sid, tax, indent=0)
            if cons: _merge(os.path.join(sp, 'conservation.json'), sid, cons, indent=1)
            _merge(os.path.join(sp, 'about.json'), cand['wiki'], raw, indent=None, sort=False)
        return steps, row, commit
    return gather


def _merge(path, key, value, indent, sort=True):
    d = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    d[key] = value
    os.makedirs(os.path.dirname(path), exist_ok=True); tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f: json.dump(d, f, ensure_ascii=False, indent=indent, sort_keys=sort); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def normalise(c):
    """A candidate from a file or the command line, with the defaults a title alone allows."""
    c = dict(c); c['wiki'] = (c.get('wiki') or '').strip(); k = c.get('kind')
    if not c['wiki']: raise ValueError('a candidate needs a wiki title')
    if k not in species_rows.KINDS: raise ValueError('%r: kind must be one of %s' % (c['wiki'], species_rows.KINDS))
    if k != 'resource' and not c.get('latin'): c['latin'] = c['wiki']   # a title that is the Latin name; for a common-name title pass `latin`
    if k == 'taxon' and 'tl' not in c: raise ValueError('%r: a taxon needs its trophic level (tl 1 to 4)' % c['wiki'])
    return c


def run(cands, src, root='.', dry=True, limit=0, deadline=None, now=None, log=print):
    """Runs every candidate through ensure(); returns (results, stopped). One candidate failing never blocks the others; a stopped source ends the run."""
    rows = species_rows.SpeciesRows(root); ledger = creation_ledger.Ledger('species', root); gather = make_gather(src, root, now); out = []; stopped = None
    for i, c in enumerate(cands):
        if limit and i >= limit: log('STOP: the limit of %d candidates' % limit); break
        if deadline and time.time() > deadline: log('STOP: the time budget; the rest waits for the next run'); break
        try: c = normalise(c)
        except ValueError as ex: out.append({'kind': 'species', 'status': 'refused', 'id': None, 'dry': dry, 'steps': {}, 'reason': 'bad candidate: %s' % ex}); log('refused %s' % ex); continue
        try: r = rows.ensure(c, gather, ledger, now, dry)
        except Stopped as ex: stopped = str(ex); log('STOP: %s (nothing more is tried; ask the owner)' % ex); break
        r['wiki'] = c['wiki']; out.append(r)
        log('%s %s%s%s' % (r['status'], c['wiki'], ' -> ' + r['id'] if r['id'] else '', ' (%s)' % r['reason'] if r['reason'] else ''))
    return out, stopped


def main(argv=None, root=ROOT, src=None):
    a = list(sys.argv[1:] if argv is None else argv); opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    dry = '--dry' in a; cands = []
    if opt('--candidates'): cands += json.load(open(opt('--candidates'), encoding='utf-8'))
    if opt('--titles'):
        base = {k: v for k, v in (('kind', opt('--kind')), ('latin', opt('--latin')), ('tl', int(opt('--tl')) if opt('--tl') else None)) if v is not None}
        cands += [dict(base, wiki=t) for t in opt('--titles').split('|') if t.strip()]
    if not cands: print(__doc__); return 1
    deadline = time.time() + 60 * float(opt('--minutes')) if opt('--minutes') else None
    res, stopped = run(cands, src or Sources(), root, dry, int(opt('--limit', 0)), deadline)
    n = lambda s: sum(1 for r in res if r['status'] == s)
    print('summary: added %d, already there %d, refused %d%s' % (n('added'), n('exists'), n('refused'), ' (dry run: nothing written)' if dry else ''))
    refused = {}
    for r in res:
        if r['status'] == 'refused': refused[r['reason']] = refused.get(r['reason'], 0) + 1
    if refused: print('refused by reason:', json.dumps(refused, sort_keys=True))
    if opt('--out'): json.dump(res, open(opt('--out'), 'w'), indent=1, ensure_ascii=False)
    if not dry and n('added'):
        bad = SpeciesPhotos(root).check()
        if bad: print('CHECK FAILED:'); print('\n'.join(bad[:30])); return 1
    return 2 if stopped else 0


if __name__ == '__main__': sys.exit(main())
