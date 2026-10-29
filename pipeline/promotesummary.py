#!/usr/bin/env python3
"""promotesummary.py promoted.json: markdown for the data-promote pull request.
A table of what moved and what was held (and why), then 10 random feeding links from the promoted parks for the spot check
in docs/PROMOTION.md rule 3 (the seed is fixed so the same batch always shows the same sample)."""
import json, os, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'build'))
import species
r = json.load(open(sys.argv[1]))
print('Moves passing state parks from the pilot (data-auto) to the main app (data). Not merged by the job: the owner merges after the spot check below.\n')
print('Promoted: %d parks. Held back: %d.\n' % (len(r['moved']), len(r['held'])))
if r['held']:
    print('<details><summary>Held back</summary>\n')
    for n, w in r['held']: print('- %s: %s' % (n, ', '.join(w)))
    print('\n</details>\n')
links = []
for i in r['moved']:
    e = species.load(os.path.join(ROOT, 'data', i + '.json')); nm = {n['id']: n for n in e['nodes']}
    for a, b, *k in e['raw']:
        if (k and k[0] != 's') or a not in nm or b not in nm: continue
        ev = (e.get('ev') or {}).get('%s>%s' % (a, b))
        if ev: links.append((e['name'], nm[b]['name'], nm[a]['name'], {'g': 'species-level', 'gg': 'genus-level', 'gf': 'family-level'}.get(ev[0], ev[0])))
random.Random(1).shuffle(links)
print('Spot check (rule 3): 10 random feeding links. More than one obviously wrong means the batch does not ship.\n')
print('| Park | Eater | Eaten | GloBI match | Verdict |\n|---|---|---|---|---|')
for p, eater, eaten, lvl in links[:10]: print('| %s | %s | %s | %s | |' % (p, eater, eaten, lvl))
