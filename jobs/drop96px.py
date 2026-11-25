#!/usr/bin/env python3
"""drop96px.py: the one-time data migration of #1188 (owner, 25 Nov): the 192 px picture becomes the stored picture of species and journeys, and the 96 px files go.
Usage: drop96px.py [--kind species|journeys|all] [--dry]   (run from the repository root; a data job runs it and opens the data pull request, never an agent by hand)

species   (lib/species_photos.py migrate_192): a species without a 192 px copy gets one shrunk from its 400 px copy (offline); photos/species/<f> is deleted when every species that shows it has its 192 px copy,
          else it stays. The credit rows, the `f` names and (apart from rows added for copies made from the 400 px file) photos/species_medium.json do not change.
journeys  (lib/journey_photos.py migrate_192): photos/journeys/<id>.webp, when it is still 96 px, is replaced under the same name by a 192 px copy shrunk from photos/journeys-lg/<id>.webp; a cover with no 400 px copy stays 96 px.
Everything is written through the two writers (files first, lists last), and the files are checked afterwards (exit 1 when they disagree). --dry prints the plan and writes nothing. Delete this file after the migration has run."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import species_photos, journey_photos


def main(argv=None, root=ROOT, out=print):
    a = list(sys.argv[1:] if argv is None else argv); kind = a[a.index('--kind') + 1] if '--kind' in a else 'all'; dry = '--dry' in a
    if kind not in ('species', 'journeys', 'all'): out('unknown kind', kind); return 1
    bad = []
    if kind in ('species', 'all'):
        w = species_photos.SpeciesPhotos(root); r = w.migrate_192(dry=dry)
        out('species: %d 96 px files %s, %d 192 px copies made from the 400 px copy, %d 96 px files stay' % (len(r['delete']), 'would be deleted' if dry else 'deleted', len(r['made']), len(r['kept'])))
        for f in r['delete'][:200 if dry else 5]: out('  delete', f)
        for sid in r['made'][:200 if dry else 5]: out('  192 px from 400 px', sid)
        for f, why in sorted(r['kept'].items())[:200 if dry else 5]: out('  keep', f, '-', why)
        if not dry: bad += species_photos.SpeciesPhotos(root).check()
    if kind in ('journeys', 'all'):
        w = journey_photos.JourneyPhotos(root); r = w.migrate_192(dry=dry)
        out('journeys: %d covers %s to 192 px, %d stay 96 px' % (len(r['made']), 'would be made' if dry else 'made', len(r['kept'])))
        for j in r['made']: out('  192 px from 400 px', j)
        for j, why in sorted(r['kept'].items()): out('  keep', j, '-', why)
        if not dry: bad += journey_photos.JourneyPhotos(root).check()
    if bad: out('CHECK FAILED:'); out('\n'.join(bad[:30])); return 1
    return 0


if __name__ == '__main__': sys.exit(main())
