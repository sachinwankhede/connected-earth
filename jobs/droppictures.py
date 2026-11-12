#!/usr/bin/env python3
"""droppictures.py: remove hosted species pictures whose licence is outside the picture rule (#421).
Usage: droppictures.py [species|places] [--dry] [--title NAME ...]   (species is the default; --dry prints the counts and writes nothing; --title drops those species' pictures whatever their licence, e.g. a picture the owner rejected)
A picture is kept when lib/licences.py says its licence in photos/species_metadata.json is allowed for its source (GBIF pages: 'GBIF', Openverse pages: 'Openverse', all others: 'Wikimedia').
A dropped picture loses its thumbnail (photos/species/), its larger copy (photos/species-lg/), and its rows in species_hosted.json, species_metadata.json, species_large.json,
species.json and species_source.json. The title goes to species_missing.json as 'nophoto' with no tried date, so data-commonsphotos tries it again and may find a picture inside the rule.
No network. Prints one line per licence name and the total."""
import sys, os, json, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'lib')); import licences, photo_registry
P = {n: os.path.join('photos', n + '.json') for n in ('species_metadata', 'species_hosted', 'species_large', 'species', 'species_source', 'species_missing', 'species_commons_tried', 'species_gbif_tried', 'species_openverse_tried', 'species_inaturalist_tried')}
def source_of(meta):
    p = meta.get('p') or ''
    return 'GBIF' if 'gbif.org' in p else 'Openverse' if 'openverse.org' in p else 'iNaturalist' if 'inaturalist.org' in p else 'Wikimedia'
def outside(meta, hosted):
    """Titles with a hosted picture whose licence is outside the rule."""
    return sorted(t for t in hosted if not licences.ok(source_of(meta.get(t) or {}), (meta.get(t) or {}).get('l', '')))
def drop(root, dry=False, titles=None):
    load = lambda n: json.load(open(os.path.join(root, P[n]), encoding='utf-8')) if os.path.exists(os.path.join(root, P[n])) else {}
    d = {n: load(n) for n in P}
    bad = sorted(t for t in titles if t in d['species_hosted']) if titles else outside(d['species_metadata'], d['species_hosted'])   # a named title is dropped whatever its licence
    counts = collections.Counter((d['species_metadata'].get(t) or {}).get('l', '') or '(none)' for t in bad)
    if dry or not bad: return bad, counts
    today = datetime.date.today().isoformat()
    for t in bad:
        f = d['species_hosted'][t]; src_of = source_of(d['species_metadata'].get(t) or {})
        for sub in ('species', 'species-lg'):
            p = os.path.join(root, 'photos', sub, f)
            if os.path.exists(p): os.remove(p)
        for n in ('species_metadata', 'species_hosted', 'species_large', 'species', 'species_source', 'species_commons_tried', 'species_gbif_tried'): d[n].pop(t, None)
        d['species_missing'][t] = 'nophoto'
        if src_of == 'Openverse': d['species_openverse_tried'][t] = today   # jobs/openversephotos.py tries it again only after 90 days, not at once
        if src_of == 'iNaturalist': d['species_inaturalist_tried'][t] = today   # the same for jobs/inaturalistphotos.py
    for n in ('species_metadata', 'species_hosted', 'species_large', 'species', 'species_source', 'species_missing', 'species_commons_tried', 'species_gbif_tried', 'species_openverse_tried', 'species_inaturalist_tried'):
        p = os.path.join(root, P[n])
        if not (os.path.exists(p) or n == 'species_missing' or (n in ('species_openverse_tried', 'species_inaturalist_tried') and d[n])): continue
        if n in ('species_metadata', 'species_hosted', 'species_large'): json.dump(d[n], open(p, 'w', encoding='utf-8'), indent=0, sort_keys=True, ensure_ascii=False)   # the layout hostphotos.py and largephotos.py write
        else: json.dump(d[n], open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'), sort_keys=(n in ('species_source', 'species_commons_tried', 'species_gbif_tried', 'species_openverse_tried', 'species_inaturalist_tried')))   # the layout commonsphotos.py writes
    return bad, counts
def drop_places(root, dry=False):
    """The same for the place pictures (photos/places/places.json, one <id>.jpg each). A dropped place goes to photos/places/missing.json as 'notfree' (kept 180 days), so jobs/photos.py does not fetch it again."""
    pd = os.path.join(root, 'photos', 'places'); mp, ms = os.path.join(pd, 'places.json'), os.path.join(pd, 'missing.json')
    man = json.load(open(mp, encoding='utf-8')); miss = json.load(open(ms, encoding='utf-8')) if os.path.exists(ms) else {}
    bad = sorted(t for t, v in man.items() if not licences.ok('Wikimedia', v.get('l', '')))
    counts = collections.Counter(man[t].get('l', '') or '(none)' for t in bad)
    if dry or not bad: return bad, counts
    for t in bad:
        p = os.path.join(pd, man[t]['f'])
        if os.path.exists(p): os.remove(p)
        del man[t]; miss[t] = photo_registry.negative_entry('notfree')
    json.dump(man, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=0); json.dump(miss, open(ms, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    return bad, counts
if __name__ == '__main__':
    places = 'places' in sys.argv
    titles = [sys.argv[i + 1] for i, a in enumerate(sys.argv[:-1]) if a == '--title']
    bad, counts = drop_places(ROOT, '--dry' in sys.argv) if places else drop(ROOT, '--dry' in sys.argv, titles)
    for l, n in counts.most_common(): print('%4d  %s' % (n, l))
    print(len(bad), ('place' if places else 'species'), ('pictures named' if titles else 'pictures outside the rule') + ('' if '--dry' in sys.argv else ', removed'))
