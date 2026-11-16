#!/usr/bin/env python3
"""#973 phase 3: api/species-pictures.json (read by the journey views) lists the species at a journey end under their species id as well as under their title,
with the credit of the same picture. Runs on the built site; skipped when the build has not run."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
f = os.path.join(ROOT, 'api', 'species-pictures.json')
if not os.path.exists(f):
    print('skipped: the build has not run'); sys.exit(0)
d = json.load(open(f))
ids = [k for k in d['ph'] if re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', k)]
assert ids, 'no species id entries in the shared picture file'
for k in ids:
    e = d['ph'][k]
    assert isinstance(e, list) and len(e) == 2 and e[0].endswith('.webp'), (k, e)
# an id entry carries the credit the same picture has under its own record
sp = json.load(open(os.path.join(ROOT, 'photos', 'species_pictures.json')))
pics = sp.get('pics', sp)
for k in ids:
    assert k in pics, 'id %s is not a species picture record' % k
    assert d['ph'][k][0] == pics[k]['f'], (k, d['ph'][k], pics[k].get('f'))
print('ok', len(ids), 'id entries')
