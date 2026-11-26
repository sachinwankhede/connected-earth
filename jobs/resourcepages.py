#!/usr/bin/env python3
"""resourcepages.py (#1142, owner 26 Nov: "complete all bad data items"): remove resource rows (abiotic/decomposer boxes) whose Wikipedia page is a named place or the wrong kind of thing,
e.g. "Rivers" on the page of the Limpopo River, "Poor acidic soils" on Oxisol. No data is better than bad data (owner, 23 Nov). Uses jobs/strictrows.apply (a row a journey ends at, or the last
abiotic/decomposer row of a place, is kept and listed). Rows whose page is the right concept (Stream, Tide, Fog, Dune...) stay.
  python3 jobs/resourcepages.py [--apply]"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in ('build', 'lib', 'jobs'): sys.path.insert(0, os.path.join(ROOT, d))
import strictrows
PLACE = 'its page is a named place, not the thing the row names'
KIND = 'its page is a different kind of thing from the row'
SIDS = {s: PLACE for s in '''badland-and-clay-soils canal-freshwater cool-water-temperature deep-cold-lakes deep-oxygenated-water delta-silt-and-nutrients equatorial-glaciers fifth-season
floodwater hot-salty-shallow-water lakes-and-clear-water lakes-and-rivers lakes-ponds-wetlands long-snowy-winters meandering-rivers mountain-streams-and-pools mountain-streams-and-rivers
oasis-springs-and-wadi ocean-passages rain-and-rivers rain-meltwater rainwater-depressions-rawdat red-sand-and-limestone-country river-sediment-and-nutrients rivers seasonal-flood
seasonal-flood-pulse seasonal-flooding seasonal-floodwater shallow-lagoons shallow-saline-lakes snowmelt-and-medano-creek thin-soil-on-ancient-rock timane-river-and-waterholes
travertine-lake-water veredas-rio-preto-streams warm-clear-ocean-water warm-clear-water warm-shallow-sheltered-bay westerly-rain winter-snow-and-ice'''.split()}
SIDS.update({s: KIND for s in '''muddy-tidal-flats poor-acidic-soils poor-wet-soils reef-water lagoon-water warm-lagoon-water cool-mountain-air rain-and-snowmelt groundwater sunlight'''.split()})

def plan(root=ROOT):
    import species
    have = {r['sid'] for r in species.table(root).values() if r.get('sid') and r.get('sk') == 'resource'}
    return {s: w for s, w in SIDS.items() if s in have}

# A row kept because it is its place's only abiotic node gets a page that is the concept instead (the name and text stay).
REPAGE = {'deep-cold-lakes': 'Lake', 'lagoon-water': 'Lagoon', 'lakes-and-rivers': 'Lake', 'mountain-streams-and-pools': 'Stream', 'oasis-springs-and-wadi': 'Oasis',
          'poor-acidic-soils': 'Soil pH', 'reef-water': 'Seawater', 'rain-and-snowmelt': 'Snowmelt', 'rainwater-depressions-rawdat': 'Rain', 'seasonal-floodwater': 'Flood', 'sunlight': 'Sunlight'}

def repage(root, sids, dry=True):
    import glob, json
    done = []
    for f in glob.glob(os.path.join(root, 'data', '*', 'rows', '**', '*.json'), recursive=True):
        s = os.path.basename(f)[:-5]
        if s in sids and s in REPAGE:
            def fn(o, s=s):
                if o.get('wiki') == REPAGE[s]: return False
                o['wiki'] = REPAGE[s]; return True
            if dry:
                import json as j; 
                if j.load(open(f, encoding='utf-8')).get('wiki') != REPAGE[s]: done.append(s)
            elif strictrows.edit(f, fn): done.append(s)
    return sorted(done)

def run(root=ROOT, dry=True):
    todo = plan(root)
    removed, kept = strictrows.apply(root, set(todo), dry, todo)
    if not dry and removed: strictrows.record(root, 'resourcepages', removed, todo, kept)
    run.repaged = repage(root, set(kept), dry)
    return todo, removed, kept

if __name__ == '__main__':
    t, r, k = run(ROOT, '--apply' not in sys.argv)
    print('%d listed, %d removed, %d kept, %d given a concept page' % (len(t), len(r), len(k), len(run.repaged)))
    for s, w in sorted(k.items()): print('kept', s, w)
