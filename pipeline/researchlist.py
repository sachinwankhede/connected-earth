#!/usr/bin/env python3
"""researchlist.py <spec>: research several places in one job (research.py does each one).
  spec = id1,id2,...        those places
  spec = next:N[:prefix]    the next N places in data/ that have no story yet and no research file on the `research` branch,
                            optionally only ids starting with a prefix (wh = World Heritage, np = national parks)
Prints the ids it did. Needs the web (run by the data-research workflow)."""
import json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(here)
sys.path.insert(0, here); import research
def have():
    r = subprocess.run(['git', 'ls-tree', '--name-only', 'origin/research', 'research/'], capture_output=True, text=True, cwd=ROOT)
    return {os.path.basename(l)[:-3] for l in r.stdout.split() if l.endswith('.md')}
def pick(spec):
    if not spec.startswith('next:'): return [s.strip() for s in spec.split(',') if s.strip()]
    a = spec.split(':'); n = int(a[1]); pre = a[2] if len(a) > 2 else ''
    done = have(); out = []
    order = json.load(open(os.path.join(ROOT, 'data', 'links.json')))['order']
    for i in order:
        if len(out) >= n: break
        p = os.path.join(ROOT, 'data', i + '.json')
        if not i.startswith(pre) or i in done or not os.path.exists(p) or json.load(open(p)).get('story'): continue
        out.append(i)
    return out
if __name__ == '__main__':
    ids = pick(sys.argv[1]); print('places:', ' '.join(ids), flush=True)
    open(os.path.join(ROOT, 'research.ids'), 'w').write(' '.join(ids))
    for i in ids:
        try: research.main(i)
        except SystemExit as e: print('skipped', i, e)
