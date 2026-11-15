#!/usr/bin/env python3
"""journeypictures.py: the journey strategy of the acquire job: finds a cover picture for each journey that has none (docs/DATA-PLAN.md, "Journey pictures: by journey id", phase 4; owner, 15 Nov: "Own").
Usage: journeypictures.py [--strategy all|wikipedia|commons|gbif|openverse|inaturalist|large] [--limit N] [--max-mb N] [--again] [--dry]   (run from the repository root)

Why a small job beside jobs/speciespictures.py and not a strategy inside it: that job is keyed by species id, reads the species rows and writes through SpeciesPhotos; a journey is keyed by journey id, its
titles come from data/journeys/<id>.json and it has a 400 px copy but no 192 px one. What is the same is reused, not copied: the sources (lib/species_sources.py find_* functions: one fetch per title, the
rules for licences, authors, JPEG only and maps/diagrams/logos refused), the order, the holds, the author rule (`vet`), the shrinking and the copies, and the whole loop (`speciespictures.acquire`). This file
only (1) lists the journeys as units {sid = journey id, title = its imgwiki, abiotic = a flow journey} and (2) hands the loop a writer with the journey id as key.
A species journey (type 'species') tries its imgwiki title through every source, in the species order (wikipedia, commons, gbif, openverse, inaturalist). A flow journey (type 'flow': "Saharan Air Layer",
"Gulf of Mexico dead zone") treats the title as a page title and tries only wikipedia and commons (a search finds a photo of the thing the word names, not of a flow: no GBIF, Openverse or iNaturalist, the
`abiotic` rule of the species job). A page whose picture is a map, diagram, logo or flag is refused and the log says which file was skipped ("skipped as not a photo"). Journeys that share a title
(osprey and chesosprey; greenturtleA and greenturtleB) are fetched once and each gets its own row and credit.
Everything is written only through lib/journey_photos.py (put / put_large / miss / note_tried / commit): the 96 px picture, its credit and the 400 px copy in the same commit; the author rule applies (a CC BY /
CC BY-SA picture with no author is refused, recorded as 'notfree' for wikipedia or as tried for the other sources). Holds, caps, --dry and --limit are those of speciespictures.py (--limit counts titles).
Exit 2 when a source stopped the run (throttled three times, or refused); exit 1 for a failed check or when the migration (jobs/rekeyjourneyphotos.py) has not made photos/journey_pictures.json."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import speciespictures as sj, journey_photos as jp, journey_pics, species_sources as ss

# the species strategies, except that the three that look for an animal (gbif, openverse, inaturalist) skip a flow journey
STRATEGIES = [(n, f, a if n in ('wikipedia', 'commons') else ss._organism, d) for n, f, a, d in ss.SOURCES]


class Photos(jp.JourneyPhotos):
    """The journey writer as the acquire loop sees it: a journey has no 192 px copy, so that copy always counts as present and is never made."""
    def has_medium(self, jid): return True
    def put_medium(self, jid, webp): pass


def copies(entry, need=('large',), get=None):
    """Only the 400 px copy of a journey cover (the same download and WebP settings as the species copies)."""
    return sj.make_copies(entry, tuple(k for k in need if k == 'large'), get)


def load_units(root):
    """One dict per journey that has an imgwiki title, in id order: sid (the journey id), title, name, latin, abiotic (true for a flow journey)."""
    import journeydata
    return [dict(sid=c['id'], title=c['imgwiki'], name=c.get('imgwiki') or '', latin='', abiotic=c.get('type') == 'flow')
            for c in sorted(journeydata.journeys(root), key=lambda c: c['id']) if c.get('imgwiki')]


def main(argv=None, root=ROOT):
    a = list(sys.argv[1:] if argv is None else argv); opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    only = opt('--strategy', 'all'); limit = int(opt('--limit', 0)); max_mb = float(opt('--max-mb', 25)); dry = '--dry' in a
    if only not in ['all', 'large'] + [s[0] for s in STRATEGIES]: print('unknown strategy', only); return 1
    if not journey_pics.new_shape(root): print('the journey pictures are not keyed by journey id yet: this job needs photos/journey_pictures.json (migration, jobs/rekeyjourneyphotos.py)'); return 1
    w = Photos(root); units = load_units(root)
    print('%d journeys with a title (%d flow journeys), %d without a cover' % (len(units), sum(1 for u in units if u['abiotic']), sum(1 for u in units if not w.has(u['sid']))))
    stats, stopped = sj.acquire(w, units, STRATEGIES, only=only, limit=limit, max_bytes=int(max_mb * 1_000_000), again='--again' in a, dry=dry, copies=copies)
    for name, s in stats.items():
        if name == 'copies': print('summary copies: tried %d, made %d, none possible %d' % (s['tried'], s['made'], s['none']))
        else: print('summary %s: tried %d, found %d, nothing %d, refused (no author) %d, tried again later %d, pictures with copies %d (none possible %d)' % (name, s['tried'], s['found'], s['miss'], s['refused'], s['retry'], s['copies'], s['nocopy']))
    print('added %d covers' % sum(s['found'] for s in stats.values()))
    if not dry:
        bad = jp.JourneyPhotos(root).check()
        if bad: print('CHECK FAILED:'); print('\n'.join(bad[:30])); return 1
    return 2 if stopped else 0


if __name__ == '__main__': sys.exit(main())
