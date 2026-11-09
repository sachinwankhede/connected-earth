#!/usr/bin/env python3
"""droplinks.py: drop eating links that are plainly wrong for a fish-eating specialist (#456, owner chose option a on 9 Nov).
Usage: droplinks.py [--dry]   (--dry prints the links and writes nothing)
A link is dropped when the consumer belongs to one of FISH_FAMILIES (osprey, kingfishers, pelicans, cormorants, gannets, ...) and the prey is a mammal or a plant (taxonomy kingdom Plantae, class Mammalia).
Everything else those birds eat (fish, crustaceans, squid, lizards, ...) stays. The link goes from the eating-link table (data/diets/) and from every place file that has it (the row in `raw` and its `ev` entry).
A species with no taxonomy is never touched. No network. Prints one line per link and the number of place rows."""
import sys, os, json, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build')); import diets, species
FISH_FAMILIES = {'Pandionidae', 'Alcedinidae', 'Halcyonidae', 'Cerylidae', 'Pelecanidae', 'Phalacrocoracidae', 'Sulidae', 'Anhingidae', 'Gaviidae', 'Podicipedidae', 'Spheniscidae', 'Alcidae', 'Fregatidae', 'Phaethontidae'}
def wrong(cons_tx, prey_tx):
    """True for a fish specialist (by family) eating a mammal or a plant."""
    c, p = cons_tx or {}, prey_tx or {}
    return c.get('family') in FISH_FAMILIES and (p.get('class') == 'Mammalia' or p.get('kingdom') == 'Plantae')
def drop(root, dry=False):
    tx = json.load(open(os.path.join(root, 'data', 'species', 'taxonomy.json'), encoding='utf-8'))
    tab = diets.table(root); pairs = sorted((k[0], k[1]) for k in tab if wrong(tx.get(k[1]), tx.get(k[0])))   # (prey sid, consumer sid)
    want = set(pairs); rows = 0; files = 0
    st = species.table(root)
    for p in sorted(glob.glob(os.path.join(root, 'data', 'places', '*.json'))):
        d = json.load(open(p, encoding='utf-8')); nm = {n['id']: (st.get(n.get('sp')) or {}).get('sid') for n in d.get('nodes', [])}
        keep = [r for r in d.get('raw', []) if (nm.get(r[0]), nm.get(r[1])) not in want]
        if len(keep) == len(d.get('raw', [])): continue
        gone = [r for r in d['raw'] if r not in keep]; rows += len(gone); files += 1
        if dry: continue
        d['raw'] = keep
        for r in gone: (d.get('ev') or {}).pop(r[0] + '>' + r[1], None)
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False))
    if not dry:
        for prey, cons in pairs:
            f = diets.path_of(cons, root); o = json.load(open(f, encoding='utf-8')); o['prey'].pop(prey, None)
            if o['prey']: json.dump(o, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
            else: os.remove(f)   # a consumer left with no prey has no file (the schema wants at least one)
    return pairs, rows, files
if __name__ == '__main__':
    pairs, rows, files = drop(ROOT, '--dry' in sys.argv)
    for prey, cons in pairs: print('%s eats %s' % (cons, prey))
    print(len(pairs), 'links;', rows, 'place rows in', files, 'place files' + (' (dry run, nothing written)' if '--dry' in sys.argv else ' removed'))
