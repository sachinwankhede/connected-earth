#!/usr/bin/env python3
"""splitbounds.py [path/to/old/bounds.json] [--force]: one-time converter from the old single-file outlines (data/bounds.json,
{place id: {"n": name, "r": [ring, ...]}}) to one file per park in data/outlines/<id>.json.
A branch that still writes the old file (for example a data-states batch started before the switch) is converted with:
    git merge origin/main   # modify/delete conflict on data/bounds.json
    git checkout --theirs data/bounds.json && python3 pipeline/splitbounds.py data/bounds.json && git rm -f data/bounds.json
Existing per-park files are kept unless --force. Prints how many files were written and skipped."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith('--')]
src = args[0] if args else os.path.join(ROOT, 'data', 'bounds.json')
out = os.path.join(ROOT, 'data', 'outlines'); os.makedirs(out, exist_ok=True)
old = json.load(open(src)); wrote = kept = 0
for i, v in old.items():
    p = os.path.join(out, i + '.json')
    if os.path.exists(p) and '--force' not in sys.argv: kept += 1; continue
    json.dump(v, open(p, 'w'), separators=(',', ':'), ensure_ascii=False); wrote += 1
print('%d written, %d kept, from %s' % (wrote, kept, src))
