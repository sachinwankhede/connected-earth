#!/usr/bin/env python3
"""species_rows.py: the one place a species row is looked up and created (docs/ADD-SPECIES.md, sections 2, 6.1 and 6.2). Nothing calls it yet.

identify() decides who a candidate is before anything is written, in a fixed order, and a doubt is a `conflict`, never a merge:
  1 the same Wikipedia article as a row of the same kind  -> that row
  2 the same GBIF key (taxon rows; from taxonomy.json)     -> that row
  3 the same row id (taxon and group rows only: their id is the slug of the Latin name, so the id is the identity; a resource row's id is only a free name and is never an identity) -> that row
  If two of these name different rows the answer is `conflict` with both named. A page is one row across kinds and never a place (docs/NODE-IDENTITY.md, I3 and I4): a candidate whose page is already the page of a row of ANOTHER kind, or the name or picture article of a place, is a `conflict` too, never a new row. Otherwise the candidate is new.
ensure() adds a species whole or not at all: it runs identify(), asks `gather` for the other steps (every one is run and recorded), refuses and records in the ledger when a required step (contracts.SPECIES_REQUIRED) is not found, and otherwise
writes the files and then the row, so a killed run leaves at worst files no row mentions. The result has the one shape every add call has: {kind, status: added|exists|refused, id, dry, steps, reason}.
A candidate carries nothing about places. `gather` is how the real sources are plugged in (jobs/addspecies.py); the tests pass fakes."""
import datetime, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'build'))
import contracts, species
from creation_ledger import Ledger
from place_photos import _write_json

KIND = 'species'
KINDS = ('taxon', 'group', 'resource')
ROW_FIELDS = ('latin', 'name', 'tl', 'wiki', 'desc', 'ic', 'sid', 'sk', 'cat', 'badge', 'about', 'src', 'at')
ID_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


def _norm(t): return re.sub(r'[\s_]+', ' ', str(t or '')).strip().lower()


class SpeciesRows:
    def __init__(self, root='.'):
        self.root = root; self.tab = species.table(root)
        tx = os.path.join(root, 'data', 'species', 'taxonomy.json')
        self.taxonomy = json.load(open(tx)) if os.path.exists(tx) else {}
        self._index()

    def _index(self):
        self.by_wiki = {}; self.by_gbif = {}; self.by_page = {}; self._place_pages = None
        for sid, r in self.tab.items():
            if r.get('wiki'):
                self.by_wiki.setdefault((r.get('sk'), _norm(r['wiki'])), []).append(sid)
                self.by_page.setdefault(_norm(r['wiki']), []).append(sid)
        for sid, t in self.taxonomy.items():
            if sid in self.tab and t.get('key') is not None: self.by_gbif.setdefault(t['key'], []).append(sid)

    def place_pages(self):
        """{normalised page: [place ids]}: the name and the picture article of every place (a place is never a row; read once, when first asked)."""
        if self._place_pages is None:
            self._place_pages = {}; d = os.path.join(self.root, 'data', 'places')
            for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
                if not f.endswith('.json') or f in ('links.json', 'order.json', 'species.json', 'bounds.json'): continue
                try: e = json.load(open(os.path.join(d, f)))
                except (OSError, ValueError): continue
                if not isinstance(e, dict): continue
                for k in ('name', 'imgwiki'):
                    if e.get(k): self._place_pages.setdefault(_norm(e[k]), set()).add(e.get('id') or f[:-5])
        return self._place_pages

    def new_sid(self, kind, latin, name):
        """The id a new row gets. Taxon and group: the slug of the Latin name (it is the identity). Resource: the slug of the name, or the next free `-2`, `-3` when another concept already holds it."""
        base = self.sid_for(latin, name)
        if kind != 'resource' or base not in self.tab: return base
        n = 2
        while '%s-%d' % (base, n) in self.tab: n += 1
        return '%s-%d' % (base, n)

    def sid_for(self, latin, name):
        """The id a new row would get: the slug of the Latin name (the name when there is none), as the build and the validator expect for a taxon or a group."""
        return species.slug(latin or name or '') or 'x'

    def identify(self, wiki, kind, latin=None, name=None, gbif=None):
        """{'status': 'new'|'exists'|'conflict', 'sid': sid or None, 'sids': [...], 'by': which test hit}."""
        if kind not in KINDS: raise ValueError('kind %r is not one of %s' % (kind, KINDS))
        hits = {}
        for sid in self.by_wiki.get((kind, _norm(wiki)), []): hits.setdefault(sid, 'wiki')
        if kind == 'taxon' and gbif is not None:
            for sid in self.by_gbif.get(gbif, []): hits.setdefault(sid, 'gbif')
        cand = self.sid_for(latin, name or wiki)
        if kind != 'resource' and cand in self.tab: hits.setdefault(cand, 'id')
        if not hits:
            other = sorted(x for x in self.by_page.get(_norm(wiki), []) if self.tab[x].get('sk') != kind)
            if other: return {'status': 'conflict', 'sid': None, 'sids': other, 'by': 'page of another kind (%s)' % ', '.join(sorted({self.tab[x].get('sk') for x in other}))}
            pl = sorted(self.place_pages().get(_norm(wiki), ()))
            if pl: return {'status': 'conflict', 'sid': None, 'sids': [], 'by': 'place: the page is the article of %s' % ', '.join(pl)}
            return {'status': 'new', 'sid': None, 'sids': [], 'by': None}
        if len(hits) > 1: return {'status': 'conflict', 'sid': None, 'sids': sorted(hits), 'by': ','.join(sorted(set(hits.values())))}
        sid, by = next(iter(hits.items())); return {'status': 'exists', 'sid': sid, 'sids': [sid], 'by': by}

    def check_row(self, row):
        """Problems with a row that is about to be written (empty = ok): the shape of species-row.schema.json and the model rules of section 6.2."""
        errs = []
        for f in ('latin', 'name', 'tl', 'wiki', 'desc', 'ic', 'sid', 'sk'):
            if f not in row: errs.append('no %s' % f)
        if row.get('sk') not in KINDS: errs.append('sk %r' % row.get('sk'))
        if not ID_RE.match(row.get('sid') or ''): errs.append('sid %r is not an id' % row.get('sid'))
        if row.get('sid') in self.tab: errs.append('sid %r is already a row' % row.get('sid'))
        if row.get('sk') == 'resource' and row.get('cat') not in ('abiotic', 'decomp'): errs.append('a resource row needs cat abiotic or decomp')
        if row.get('sk') in ('taxon', 'group') and (row.get('cat') or not row.get('latin')): errs.append('a taxon or group row needs a Latin name and no cat')
        if row.get('sk') in ('taxon', 'group') and row.get('sid') != species.slug(row.get('latin') or ''): errs.append('sid %r is not the slug of the Latin name' % row.get('sid'))
        if not row.get('about'): errs.append('no summary (about)')
        if self.by_wiki.get((row.get('sk'), _norm(row.get('wiki')))): errs.append('another row of this kind already has the page %r' % row.get('wiki'))
        extra = set(row) - set(ROW_FIELDS)
        if extra: errs.append('fields the row schema refuses: %s' % ', '.join(sorted(extra)))
        return errs

    def create(self, row):
        """Write one row file atomically (the last step of an add: the files it needs are already written). Refuses a row that check_row() does not pass."""
        errs = self.check_row(row)
        if errs: raise ValueError('row %r refused: %s' % (row.get('sid'), '; '.join(errs)))
        rows = os.path.join(self.root, 'data', 'nodes' if row['sk'] == 'resource' else 'species', 'rows')
        _write_json(species.row_path(row['sid'], rows), row, indent=1)
        self.tab[row['sid']] = row; self._index()
        return row['sid']

    def ensure(self, cand, gather, ledger=None, now=None, dry=False):
        """Add a species whole or not at all. `cand` = {wiki, kind, latin?, name?, gbif?}. `gather(cand, sid)` runs every step but identity without writing anything and returns
        (steps, row, commit): steps {step: {result, detail}}, the row to add (None when it could not be made), and commit(), which writes the files that belong to it (picture, taxonomy, summary).
        Returns {kind, status, id, dry, steps, reason}."""
        kind = cand['kind']; key = cand['wiki']; day = now or datetime.date.today()
        ident = self.identify(cand['wiki'], kind, cand.get('latin'), cand.get('name'), cand.get('gbif'))
        out = lambda status, sid=None, steps=None, reason=None: {'kind': KIND, 'status': status, 'id': sid, 'dry': dry, 'steps': steps or {}, 'reason': reason}
        if ident['status'] == 'exists':
            return out('exists', ident['sid'], {'identity': {'result': 'found', 'detail': 'row %s (same %s)' % (ident['sid'], ident['by'])}})
        if ident['status'] == 'conflict':
            steps = {'identity': {'result': 'missing', 'detail': 'conflict: %s (matched by %s)' % (', '.join(ident['sids']) or 'no row', ident['by'])}}
            reason = 'place' if ident['by'].startswith('place') else 'conflict'
            self._refuse(ledger, key, steps, reason, day, dry)
            return out('refused', None, steps, reason)
        sid = self.new_sid(kind, cand.get('latin'), cand.get('name') or cand['wiki'])
        steps, row, commit = gather(cand, sid)
        steps = {'identity': {'result': 'found', 'detail': 'new'}, **steps}
        needed = contracts.SPECIES_REQUIRED[kind]
        failed = [s for s in needed if steps.get(s, {}).get('result') != 'found']
        if failed:
            self._refuse(ledger, key, steps, failed[0], day, dry)
            return out('refused', None, steps, failed[0])
        errs = self.check_row(row or {})
        if errs:
            steps['row'] = {'result': 'missing', 'detail': '; '.join(errs)}
            self._refuse(ledger, key, steps, 'row', day, dry)
            return out('refused', None, steps, 'row')
        if not dry:
            commit(); self.create(row)
            if ledger is not None: ledger.clear(key); ledger.commit()
        return out('added', row['sid'], steps)

    @staticmethod
    def _refuse(ledger, key, steps, reason, day, dry):
        if ledger is not None and not dry: ledger.record(key, steps, reason, day); ledger.commit()
