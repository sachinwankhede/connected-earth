#!/usr/bin/env python3
"""nodesrows_move.py: one-time move of the rows of non-species nodes out of the species rows (#976 last step; docs/DATA-PLAN.md; owner, 16 Nov: Antarctic Convergence, Little Missouri River and Fomes fomentarius are concepts, not species).

Usage: nodesrows_move.py [dry]
Every row of data/species/rows with `sk: resource` (551: sunlight, rain, soil, rivers, currents, deadwood fungi...) moves, unchanged, to data/nodes/rows/<first two letters of sid>/<sid>.json. Place files keep pointing at them with `sp`
(build/species.py reads both folders). Whatever the species picture lists hold for those ids (picture, larger copies, missing entry, ledger line) is dropped through lib/species_photos.py: their pictures are filed by node id
(photos/node_pictures.json, #976), so a species list never holds a node. Refuses when data/nodes/rows already exists. `dry` writes nothing. Deleted after the move has run."""
import glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import species_photos


def resource_files(root):
    """{sid: path} of the species rows of kind resource."""
    out = {}
    for f in sorted(glob.glob(os.path.join(root, 'data', 'species', 'rows', '*', '*.json'))):
        with open(f) as h: r = json.load(h)
        if r.get('sk') == 'resource': out[r['sid']] = f
    return out


def move(root, dry=False):
    dest = os.path.join(root, 'data', 'nodes', 'rows')
    if os.path.exists(dest): raise SystemExit('data/nodes/rows exists: the node rows are already moved')
    files = resource_files(root); spw = species_photos.SpeciesPhotos(root)
    held = sorted(s for s in files if s in spw.pics or s in spw.medium or s in spw.large or s in spw.miss_ or s in spw.tried)
    if dry: return {'rows': len(files), 'pictured': len([s for s in held if s in spw.pics]), 'listed': len(held)}
    for sid, f in files.items():
        to = os.path.join(dest, sid[:2], sid + '.json'); os.makedirs(os.path.dirname(to), exist_ok=True); os.rename(f, to)
        d = os.path.dirname(f)
        if not os.listdir(d): os.rmdir(d)
    for sid in held: spw.forget(sid)
    spw.commit()
    return {'rows': len(files), 'pictured': 0, 'listed': len(held)}


if __name__ == '__main__':
    r = move(ROOT, dry=sys.argv[1:] == ['dry']); print('%d node rows moved; %d ids dropped from the species picture lists' % (r['rows'], r['listed']))
