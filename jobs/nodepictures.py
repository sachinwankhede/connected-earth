#!/usr/bin/env python3
"""nodepictures.py: the node strategy of the acquire job: finds a picture for each non-species food-web node concept that has none (sunlight, rain, soil, decomposers; #1183, #976).
Usage: nodepictures.py [--strategy all|wikipedia|commons|gbif|openverse|inaturalist] [--limit N] [--max-mb N] [--again] [--dry]   (run from the repository root)

Same pattern as jobs/journeypictures.py and nothing copied: the sources (lib/species_sources.py SOURCES), the order, the 30-day holds, the author rule (`vet`), the shrinking and the whole loop
(`speciespictures.acquire`) are the species job's. This file only (1) lists the node concepts as units {sid = node id, title = the node's `wiki` title, abiotic = True} and (2) hands the loop a writer.
A node id is the slug of the node's `wiki` title (lib/node_photos.py node_id), so the 1,500 places that show Sunlight share one unit. The units are the nodes that carry a category and a wiki title once
a place file is joined with the species and node rows, the way the build does it (build/build.py load_places), so a node the build shows is a node this job looks at.
Every node is abiotic: only wikipedia and commons are tried (a search finds a photo of the thing the word names; no GBIF, Openverse or iNaturalist), like a flow journey.
Store: photos/nodes/<hash>.webp (the 192 px file the app shows; there is no 96 px, medium or large copy of a node), photos/node_pictures.json, photos/node_missing.json, written only by lib/node_photos.py.
The acquire loop downloads a 96 px picture first; this writer keeps it only until the 192 px copy (made from the same source in the same run) replaces it, and falls back to it when that copy cannot be made
(the app tolerates a small picture). Nodes in node_missing.json are retried by the same rule as everything else: wikipedia by the missing record's own expiry, commons by the 30-day hold. The node store
has no ledger of which source tried, so the hold is read from the missing record's date (the same run tries both sources), and a source that found nothing is not remembered beyond that record.
Exit 2 when a source stopped the run (throttled three times, or refused); exit 1 for an unknown strategy or a failed check."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import speciespictures as sj, node_photos as np, species_sources as ss, author_repair as ar

# the species strategies, except that the three that look for an animal (gbif, openverse, inaturalist) skip an abiotic title (every node is one)
STRATEGIES = [(n, f, a if n in ('wikipedia', 'commons') else ss._organism, d) for n, f, a, d in ss.SOURCES]


class Photos(np.NodePhotos):
    """The node writer as the acquire loop sees it: a node has one 192 px file, so the loop's small picture is staged and replaced by the 192 px copy (put_medium); the other copies count as present."""
    def __init__(self, root='.'):
        super().__init__(root); self.tried = {}; self._small = {}
        for nid, e in self.miss_.items():   # the hold of a source is read from the missing record's date
            d = str(e.get('checkedAt', ''))[:10]
            if d: self.tried[nid] = {'wikipedia': d, 'commons': d}

    def has_medium(self, nid): return nid not in self._small
    def has_large(self, nid): return True
    def put_large(self, nid, webp): pass

    def put(self, nid, entry, webp, now=None):
        super().put(nid, entry, webp, now); self._small[nid] = webp   # the file name is the hash of what is stored, so put_medium replaces it

    def put_medium(self, nid, webp):
        if nid not in self._small: return
        entry = dict(self.pics[nid]); self._write.pop(self._path(entry['f']), None); self._small.pop(nid)   # the staged small file is never written
        super().put(nid, {k: v for k, v in entry.items() if k != 'f'}, webp)   # (its delete entry names a file that does not exist: harmless)

    def miss(self, nid, status, source='', attempts=None, now=None):
        super().miss(nid, status, attempts, now)
        if source: self.tried.setdefault(nid, {})[source] = self.miss_[nid]['checkedAt'][:10]

    def note_tried(self, nid, source, now=None):
        """A source that found nothing: kept for this run only (node_missing.json is not touched, a later source may still try)."""
        if nid in self.pics: raise ValueError('%r has a stored picture: nothing to note' % nid)
        self.tried.setdefault(nid, {})[source] = (now or np.pr._utcnow()).isoformat()[:10]

    def commit(self):
        self._small.clear(); super().commit()   # a node whose 192 px copy was not made keeps the small picture

    def set_credit(self, nid, credit): self.pics[nid].update(credit)   # author repair (lib/author_repair.py)
    def note_repair_tried(self, nid, now=None): self.tried.setdefault(nid, {})['repair'] = (now or np.pr._utcnow()).isoformat()[:10]


def copies(entry, need=('medium',), get=None):
    """Only the 192 px copy (the same download and WebP settings as the species copies)."""
    return sj.make_copies(entry, tuple(k for k in need if k == 'medium'), get)


def load_units(root):
    """One dict per node concept in the place files, in id order: sid (the node id), title (its wiki title), name, latin, abiotic (always true)."""
    import species
    tab = species.table(root); units = {}
    for f in sorted(glob.glob(os.path.join(root, 'data', 'places', '*.json'))):
        with open(f, encoding='utf-8') as fh: eco = json.load(fh)
        for n in species.join(eco, tab)['nodes']:
            if n.get('cat') and n.get('wiki'): units.setdefault(np.node_id(n['wiki']), n['wiki'])
    return [dict(sid=k, title=v, name=v, latin='', abiotic=True) for k, v in sorted(units.items())]


def main(argv=None, root=ROOT):
    a = list(sys.argv[1:] if argv is None else argv); opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    only = opt('--strategy', 'all'); limit = int(opt('--limit', 0)); max_mb = float(opt('--max-mb', 25)); dry = '--dry' in a
    if only not in ['all'] + [s[0] for s in STRATEGIES]: print('unknown strategy', only); return 1
    w = Photos(root); units = load_units(root)
    print('%d node concepts, %d without a picture (%d of them recorded as missing)' % (len(units), sum(1 for u in units if not w.has(u['sid'])), sum(1 for u in units if w.is_missing(u['sid']))))
    rl = int(opt('--repair-limit', 40))
    stats, stopped = sj.acquire(w, units, STRATEGIES, only=only, limit=limit, max_bytes=int(max_mb * 1_000_000), again='--again' in a, dry=dry, copies=copies)
    for name, s in stats.items():
        if name == 'copies': print('summary copies: tried %d, made %d, none possible %d' % (s['tried'], s['made'], s['none']))
        else: print('summary %s: tried %d, found %d, nothing %d, refused (no author) %d, tried again later %d, pictures with copies %d (none possible %d)' % (name, s['tried'], s['found'], s['miss'], s['refused'], s['retry'], s['copies'], s['nocopy']))
    print('added %d node pictures' % sum(s['found'] for s in stats.values()))
    if rl:   # the author repair step (#887): after the sources, only when none of them stopped
        if stopped: print('author repair skipped: a source stopped this run')
        else:
            rs, _ = ar.repair_step(w, limit=rl, dry=dry); print(ar.summary(rs))
            if not dry and (rs['fixed'] or rs['none']): w.commit()
    if not dry:
        bad = np.NodePhotos(root).check()
        if bad: print('CHECK FAILED:'); print('\n'.join(bad[:30])); return 1
    return 2 if stopped else 0


if __name__ == '__main__': sys.exit(main())
