#!/usr/bin/env python3
"""Write tests/fixtures/data/: a small, frozen copy of the real data for the fixture build (#787).

  python3 tests/fixtures/make_data.py        (run by hand, rarely; the result is committed)

The browser tests open `python3 build/build.py --fixture`, which builds the app from this folder, so a change to the real data cannot reach them.
The layout mirrors the repository (tests/fixtures/data/data/..., tests/fixtures/data/photos/...) and is passed to the build as --data-root. The files are copied once from data/ and then frozen: nothing reads the real data afterwards, so they do not drift. Re-run this script only to change
which places are in the set, and review the diff. Never edit the files by hand.
"""
import json, os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import species
OUT = os.path.join(ROOT, 'tests', 'fixtures', 'data')
R = lambda *a: os.path.join(ROOT, *a)

# Main places (in page order). Habitat kinds: Forest, Lakes & wetlands, Polar & mountain, Coast & ocean, Desert, Grassland, Urban.
# Levels: detailed overview places and park overviews at world level, country level (x...), state and local level, national level.
MAIN = [
    'yellowstone', 'amazon', 'prairie', 'gulf', 'mississippi', 'stlurban',      # detailed places, one per kind where the real set has one
    'serengeti', 'wadden', 'whcamargue', 'whdonana', 'wharguin',                              # the ends of the journeys below
    'nparches', 'npglacierbay', 'npgrandteton',                                  # park overviews: Desert, Coast & ocean, Polar & mountain
    'xnicaragua', 'xafghan', 'xusks',                                            # country level: Forest, Lakes & wetlands, Grassland
    'ribeavertail', 'nccarverscreek', 'wisaukprairie',                           # local (automatic), Forest, Lakes & wetlands, Grassland
    'uschickasawnationalrecre', 'usgulfislandsnationalsea', 'usagassiznationalwildlif',   # national, Forest, Coast & ocean, Lakes & wetlands
    'npwindcave',                                                                # park overview, Grassland: shares elk with yellowstone (the place sheet's "Also found in" row)
    'npblackcanyon',                                                             # park overview, Polar & mountain: the third elk place; the place sheet test's mocked pictures leave one of the two other elk places with a picture and one without (it checks both)
    'paelk',                                                                     # local (automatic), Forest, "Elk State Park": a place search for "elk" lists a place by name (searchstates)
    'kelp', 'fleconfinariver', 'xfiji', 'vtnorthhero',                                                # five fish and five amphibian species (a group needs 5, TAB_MIN), so the Species tab has eight groups and a More pill (speciestab)
    'congo', 'reef', 'arctic', 'galapagos', 'boreal', 'baikal', 'himalaya', 'greatlakes',   # the other eight of the twelve first-view flagships (FLAGS in maplibre.js; worldview expects twelve)
    'nybearmountain',                                                            # "Bear Mountain": a place search for "bear" lists a place by name (searchtabs)
    'sahara',                                                                    # a place search for "sahara" finds a place and no species (searchtabs)
    'whbanff', 'whcalakmul', 'xbahamas',                                         # Canada, Mexico and the Bahamas: North America has several countries, so a species there gets country pills (searchheader); xbahamas has osprey
]
PILOT = ['usmontevistanationalwild', 'uslenoregamerange', 'usapachenationalforest', 'iaprairierose', 'akwoodtikchik', 'usapostleislandsnational']   # pilot: national and local, several kinds
JOURNEYS = ['osprey', 'knot', 'flamingo']   # their ends must be in MAIN


def load(p): return json.load(open(p, encoding='utf-8'))
def dump(o, p, **k):
    os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(o, open(p, 'w', encoding='utf-8'), ensure_ascii=False, **k)


def main():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    ids = MAIN + PILOT
    places = {i: load(R('data', 'places', i + '.json')) for i in ids}
    for i in PILOT: assert places[i].get('stage') == 'pilot', i
    for i in MAIN: assert places[i].get('stage') != 'pilot', i
    for i, p in places.items(): dump(p, os.path.join(OUT, 'data', 'places', i + '.json'), indent=1)
    dump(MAIN, os.path.join(OUT, 'data', 'order', '0000-main.json')); dump(PILOT, os.path.join(OUT, 'data', 'order', '0001-pilot.json'))
    for i in ids:
        o = R('data', 'outlines', i + '.json')
        if os.path.exists(o): os.makedirs(os.path.join(OUT, 'data', 'outlines'), exist_ok=True); shutil.copyfile(o, os.path.join(OUT, 'data', 'outlines', i + '.json'))
    # journeys: the files and the config; every end must be a place in the set
    jd = os.path.join(OUT, 'data', 'journeys'); os.makedirs(jd)
    shutil.copyfile(R('data', 'journeys', 'config.json'), os.path.join(jd, 'config.json'))
    for n, j in enumerate(JOURNEYS):
        d = load(R('data', 'journeys', j + '.json')); d['pos'] = n
        for e in d['ends']: assert e['eco'] in places, (j, e['eco'])
        dump(d, os.path.join(jd, j + '.json'), indent=1)
    # species: the rows the places use, and the lookup tables the build reads
    tab = species.table(ROOT); keep = {}
    for p in places.values():
        for n in p['nodes']:
            if 'sp' in n: keep[n['sp']] = tab[n['sp']]
    for k, r in keep.items(): species.write_row(r, os.path.join(OUT, 'data', 'species', 'rows'))
    sd = R('data', 'species'); od = os.path.join(OUT, 'data', 'species')
    for f in ('search_vocabulary.json', 'order_names.json', 'tab_groups.json'): shutil.copyfile(os.path.join(sd, f), os.path.join(od, f))
    sids = {r['sid'] for r in keep.values()}; lat = {k for k in keep}
    tax = load(os.path.join(sd, 'taxonomy.json')); dump({k: v for k, v in tax.items() if k in sids}, os.path.join(od, 'taxonomy.json'), indent=1)
    con = load(os.path.join(sd, 'conservation.json')); dump({k: v for k, v in con.items() if k in lat}, os.path.join(od, 'conservation.json'), indent=1)
    dump({}, os.path.join(od, 'about.json'))
    os.makedirs(os.path.join(OUT, 'data', 'geo')); shutil.copyfile(R('data', 'geo', 'geo.json'), os.path.join(OUT, 'data', 'geo', 'geo.json'))
    # place pictures (the app reads photos/places/places.json, keyed by the place's imgwiki title, and the image files next to it): eight places with a picture, the rest without
    pp = load(R('photos', 'places', 'places.json')); out = {}; pd = os.path.join(OUT, 'photos', 'places'); os.makedirs(pd)
    for i in MAIN:
        e = pp.get(places[i].get('imgwiki') or '')
        if e and len(out) < 8 and os.path.exists(R('photos', 'places', e['f'])):
            out[places[i]['imgwiki']] = e; shutil.copyfile(R('photos', 'places', e['f']), os.path.join(pd, e['f']))
    dump(out, os.path.join(pd, 'places.json'), indent=1)
    # species pictures (#421): the species page's wide photo and the tiles need hosted copies; up to 20 of the fixture's species that have one, white-tailed deer first (speciespage opens it)
    ph = {n: load(R('photos', n + '.json')) for n in ('species', 'species_hosted', 'species_large', 'species_metadata')}
    low = {k.lower() for k in keep}; names = sorted((k for k in ph['species_hosted'] if k.lower() in low and k in ph['species_large'] and k in ph['species']), key=lambda k: (k != 'Odocoileus virginianus', k))[:20]
    assert names and names[0] == 'Odocoileus virginianus', 'white-tailed deer needs a hosted picture in the fixture'
    for n in ('species', 'species_hosted', 'species_large', 'species_metadata'): dump({k: ph[n][k] for k in names if k in ph[n]}, os.path.join(OUT, 'photos', n + '.json'), indent=1)
    for sub, key in (('species-md', 'species_hosted'), ('species-lg', 'species_large')):
        os.makedirs(os.path.join(OUT, 'photos', sub), exist_ok=True)
        for k in names: shutil.copyfile(R('photos', sub, ph[key][k]), os.path.join(OUT, 'photos', sub, ph[key][k]))
    print('fixture data: %d places (%d pilot), %d species, %d journeys, %d place pictures, %d species pictures' % (len(ids), len(PILOT), len(keep), len(JOURNEYS), len(out), len(names)))


if __name__ == '__main__': main()
