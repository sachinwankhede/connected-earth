#!/usr/bin/env python3
"""A node's picture id and a species' id are worked out from a title or a Latin name by the app (src/photo-registry.js) and by the build (lib/node_photos.py, build/species.py).
They must give the same id for every title, or a picture is looked up under an id the build never wrote (#973). Pinned here on tricky titles and on every title of the shipped place files."""
import json, os, subprocess, sys, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import node_photos, species

titles = ['Sunbeam', ' Soil  (science) ', 'North American Monsoon', "Dall's sheep", 'Ovis dalli', 'Æsculus hippocastanum', 'Quercus × rosacea', '1,2-dioxane', '--x--', '', 'Café au lait', 'Çiçek', 'Saint-Émilion']
for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'places', '*.json'))):
    try: d = json.load(open(f))
    except Exception: continue
    for n in d.get('nodes') or []:
        for k in ('wiki', 'latin'):
            if n.get(k): titles.append(n[k])
titles = sorted(set(titles))
js = "const R=require(process.argv[1]);const t=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(t.map(x=>[R.nodeId(x),R.sidOf(x)])))"
out = subprocess.run(['node', '-e', js, os.path.join(ROOT, 'src', 'photo-registry.js')], input=json.dumps(titles), capture_output=True, text=True, check=True).stdout
got = json.loads(out)
bad = [(t, g, node_photos.node_id(t), species.slug(t)) for t, g in zip(titles, got) if g[0] != node_photos.node_id(t) or g[1] != species.slug(t)]
assert not bad, 'the app and the build disagree on an id: %r' % bad[:5]
print('ok (%d titles)' % len(titles))
