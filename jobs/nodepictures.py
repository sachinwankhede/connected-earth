#!/usr/bin/env python3
"""nodepictures.py: the node strategy of the acquire job: finds a picture for each non-species food-web node concept that has none (sunlight, rain, soil, decomposers; #1183, #976).
Usage: nodepictures.py [--strategy all|wikipedia|commons|gbif|openverse|inaturalist] [--limit N] [--minutes N] [--max-mb N] [--repair-limit N] [--again] [--dry]   (run from the repository root)

Same pattern as jobs/journeypictures.py and nothing copied: the sources (lib/species_sources.py SOURCES), the order, the 30-day holds, the author rule (`vet`), the shrinking and the whole loop
(`speciespictures.acquire`) are the species job's. This file only (1) lists the node concepts as units {sid = node id, title = the node's `wiki` title, abiotic = True} and (2) hands the loop a writer.
A node id is the slug of the node's `wiki` title (lib/node_photos.py node_id), so the 1,500 places that show Sunlight share one unit. The units are the nodes that carry a category and a wiki title once
a place file is joined with the species and node rows, the way the build does it (build/build.py load_places), so a node the build shows is a node this job looks at.
Every node is abiotic: only wikipedia and commons are tried (a search finds a photo of the thing the word names; no GBIF, Openverse or iNaturalist), like a flow journey.
Store: photos/nodes/<hash>.webp (the 192 px file the app shows; there is no 96 px, medium or large copy of a node), photos/node_pictures.json, photos/node_missing.json, written only by lib/node_photos.py.
The acquire loop's first fetch is shrunk straight to 192 px (#1188) and stored as it is: no 96 px picture, no second download. Nodes in node_missing.json are retried by the same rule as everything else: wikipedia by the missing record's own expiry, every other source by the 30-day hold in the
ledger photos/node_tried.json {id: {source: date}} (lib/node_photos.py; the same shape as the species, place and journey ledgers; there is no copy step for a node).
Resume contract (#1183, lib/runbudget.py), the same as the other picture jobs: --minutes (default 120); prints `more: N` and exits 3 when N concepts are still due and untried; 0 when none; 2 when a source stopped the run
(do not chain); 1 for an unknown strategy or a failed check."""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import speciespictures as sj, node_photos as np, species_sources as ss, author_repair as ar

# the species strategies, except that the three that look for an animal (gbif, openverse, inaturalist) skip an abiotic title (every node is one)
STRATEGIES = [(n, f, a if n in ('wikipedia', 'commons') else ss._organism, d) for n, f, a, d in ss.SOURCES]


class Photos(np.NodePhotos):
    """The node writer as the acquire loop sees it: a node has one 192 px file, and since #1188 the loop's first fetch IS that file (no 96 px staging, no second download), so both copies always count as present."""
    def has_medium(self, nid): return True
    def has_large(self, nid): return True
    def put_medium(self, nid, webp): pass
    def put_large(self, nid, webp): pass


def load_units(root):
    """One dict per node concept in the place files, in id order: sid (the node id), title (its wiki title), name, latin, abiotic (always true)."""
    return [dict(sid=k, title=v, name=v, latin='', abiotic=True) for k, v in sorted(np.concepts(root).items())]


def main(argv=None, root=ROOT):
    a = list(sys.argv[1:] if argv is None else argv); opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    only = opt('--strategy', 'all'); limit = int(opt('--limit', 0)); max_mb = float(opt('--max-mb', 25)); minutes = float(opt('--minutes', 120)); dry = '--dry' in a
    if only not in ['all'] + [s[0] for s in STRATEGIES]: print('unknown strategy', only); return 1
    w = Photos(root); units = load_units(root)
    print('%d node concepts, %d without a picture (%d of them recorded as missing)' % (len(units), sum(1 for u in units if not w.has(u['sid'])), sum(1 for u in units if w.is_missing(u['sid']))))
    t0 = time.monotonic(); report = {}
    stats, stopped = sj.acquire(w, units, STRATEGIES, only=only, limit=limit, max_bytes=int(max_mb * 1_000_000), again='--again' in a, dry=dry, copies=None, minutes=minutes, report=report)
    return sj.finish(w, stats, stopped, report, 'node pictures', dry, int(opt('--repair-limit', 40)), t0, minutes, lambda: np.NodePhotos(root).check())


if __name__ == '__main__': sys.exit(main())
