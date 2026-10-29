#!/usr/bin/env python3
"""regen.py AR,KY: rebuild only the food web (nodes, raw, ev) of state parks that the pilot holds back for plants or links
(plants < floor, links < floor, family-level links, links without evidence), using the current plant pick.
Everything else on the place (name, photo, sources, notes, story) is kept. Parks held for too few species are not touched.
Writes regen.md (before/after table, for the pull request body) and regen.json ({'ids': [...]})."""
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import promote_check as pc, species
from state import STATES, seed
WORTH = ('plants', 'links', 'family-level')
def held(st):
    out = {}
    for f in sorted(os.listdir(os.path.join(ROOT, 'data-auto'))):
        if not f.startswith(st.lower()) or not f.endswith('.json') or f == 'order.json': continue
        e = species.load(os.path.join(ROOT, 'data-auto', f)); r = pc.check(e)
        if r['pass_'] or any(w.startswith('species') for w in r['why']): continue
        if any(w.startswith(WORTH) for w in r['why']): out[e['id']] = r
    return out
def run(cmd, env):
    print('$', ' '.join(cmd), flush=True)
    if subprocess.run(cmd, cwd=ROOT, env=dict(os.environ, **env)).returncode: sys.exit('step failed: ' + ' '.join(cmd))
if __name__ == '__main__':
    sts = [s.strip().upper() for s in sys.argv[1].split(',') if s.strip()]
    rows = []; done = []
    for st in sts:
        if st not in STATES: sys.exit('unknown state ' + st)
        H = held(st)
        print(st, len(H), 'held for plants/links:', ', '.join(H))
        if not H: continue
        work = os.path.join(ROOT, 'pipeline', 'work', 'regen_' + st); os.makedirs(work, exist_ok=True)
        pp = os.path.join(work, 'parks.json')
        if not os.path.exists(pp):
            ps = [p for p in seed(st, 40) if p['id'] in H]       # same ranking as the original build
            json.dump([{k: v for k, v in p.items() if v is not None} for p in ps], open(pp, 'w'), indent=1)
            print(len(ps), 'of', len(H), 'parks found again in the PAD-US list')
        env = {'WORK': work}
        run(['python3', 'pipeline/draft.py', 'all'], env); run(['python3', 'pipeline/autogen.py'], env)
        run(['python3', 'pipeline/names.py', '--from-data', os.path.join(work, 'out')], env); run(['python3', 'pipeline/autogen.py'], env)
        for i, before in H.items():
            p = os.path.join(work, 'out', i + '.json')
            if not os.path.exists(p): rows.append((before['name'], before['why'], 'not regenerated', False)); continue
            new = json.load(open(p)); old = json.load(open(os.path.join(ROOT, 'data-auto', i + '.json')))
            for k in ('nodes', 'raw', 'ev'): old[k] = new[k]
            if (old.get('tip') or {}).get('id') not in {n['id'] for n in new['nodes']}: old['tip'] = new.get('tip')     # the tip points at a node of the old web
            json.dump(old, open(os.path.join(ROOT, 'data-auto', i + '.json'), 'w'), ensure_ascii=False)
            after = pc.check(species.load(os.path.join(ROOT, 'data-auto', i + '.json')))
            rows.append((before['name'], before['why'], after['why'], after['pass_'])); done.append(i)
    with open(os.path.join(ROOT, 'regen.md'), 'w') as f:
        n = sum(1 for r in rows if r[3])
        f.write('Food webs rebuilt with the current plant pick for %d held parks (%s). %d now pass the promotion floors. Nothing is promoted by this pull request; run data-promote after merging.\n\n' % (len(rows), ','.join(sts), n))
        f.write('| Park | Held for | Now |\n|---|---|---|\n')
        for name, b, a, ok in rows: f.write('| %s | %s | %s |\n' % (name, '; '.join(b), 'passes' if ok else (a if isinstance(a, str) else '; '.join(a))))
    json.dump({'ids': done, 'pass': sum(1 for r in rows if r[3])}, open(os.path.join(ROOT, 'regen.json'), 'w'))
    print(open(os.path.join(ROOT, 'regen.md')).read())
