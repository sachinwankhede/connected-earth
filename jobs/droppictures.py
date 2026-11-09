#!/usr/bin/env python3
"""droppictures.py: remove hosted species pictures whose licence is outside the picture rule (#421).
Usage: droppictures.py [--dry]   (--dry prints the counts and writes nothing)
A picture is kept when lib/licences.py says its licence in photos/species_metadata.json is allowed for its source (GBIF pages: 'GBIF', all others: 'Wikimedia').
A dropped picture loses its thumbnail (photos/species/), its larger copy (photos/species-lg/), and its rows in species_hosted.json, species_metadata.json, species_large.json,
species.json and species_source.json. The title goes to species_missing.json as 'nophoto' with no tried date, so data-commonsphotos tries it again and may find a picture inside the rule.
No network. Prints one line per licence name and the total."""
import sys, os, json, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib')); import licences
P = {n: os.path.join('photos', n + '.json') for n in ('species_metadata', 'species_hosted', 'species_large', 'species', 'species_source', 'species_missing', 'species_commons_tried', 'species_gbif_tried')}
def source_of(meta):
    return 'GBIF' if 'gbif.org' in (meta.get('p') or '') else 'Wikimedia'
def outside(meta, hosted):
    """Titles with a hosted picture whose licence is outside the rule."""
    return sorted(t for t in hosted if not licences.ok(source_of(meta.get(t) or {}), (meta.get(t) or {}).get('l', '')))
def drop(root, dry=False):
    load = lambda n: json.load(open(os.path.join(root, P[n]), encoding='utf-8')) if os.path.exists(os.path.join(root, P[n])) else {}
    d = {n: load(n) for n in P}
    bad = outside(d['species_metadata'], d['species_hosted'])
    counts = collections.Counter((d['species_metadata'].get(t) or {}).get('l', '') or '(none)' for t in bad)
    if dry or not bad: return bad, counts
    for t in bad:
        f = d['species_hosted'][t]
        for sub in ('species', 'species-lg'):
            p = os.path.join(root, 'photos', sub, f)
            if os.path.exists(p): os.remove(p)
        for n in ('species_metadata', 'species_hosted', 'species_large', 'species', 'species_source', 'species_commons_tried', 'species_gbif_tried'): d[n].pop(t, None)
        d['species_missing'][t] = 'nophoto'
    for n in ('species_metadata', 'species_hosted', 'species_large', 'species', 'species_source', 'species_missing', 'species_commons_tried', 'species_gbif_tried'):
        p = os.path.join(root, P[n])
        if os.path.exists(p) or n in ('species_missing',): json.dump(d[n], open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=(n in ('species_source', 'species_commons_tried', 'species_gbif_tried')))
    return bad, counts
if __name__ == '__main__':
    bad, counts = drop(ROOT, '--dry' in sys.argv)
    for l, n in counts.most_common(): print('%4d  %s' % (n, l))
    print(len(bad), 'pictures outside the rule' + ('' if '--dry' in sys.argv else ', removed'))
