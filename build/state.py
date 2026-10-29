#!/usr/bin/env python3
"""state.py: build a batch of state parks for one US state, start to finish.

  python3 build/state.py IL --top 25              seed + draft + generate + add to the pilot + checks + report
  python3 build/state.py IL --top 25 --scratch    same, but only in a scratch folder (nothing added to the repo)
  python3 build/state.py IL --report              just re-run the promotion check for that state's places

Steps (each one resumes where it stopped): 1 seed the park list from PAD-US (largest state parks first), 2 species near each
park (GBIF) and who eats whom (GloBI), 3 common names, 4 generate the places, 5 add to data-auto (pilot), 6 shared species
table, 7 outlines, 8 promotion check. Photos and Wikipedia lines come from pipeline/fetch_all.sh (slow, run separately).
Promotion to main is a separate step: python3 build/promote.py --local (or ids)."""
import json, os, re, subprocess, sys, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
B = "https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Fee_Managers_PADUS/FeatureServer/0/query"
STATES = dict(AL='Alabama', AK='Alaska', AZ='Arizona', AR='Arkansas', CA='California', CO='Colorado', CT='Connecticut', DE='Delaware', FL='Florida', GA='Georgia', HI='Hawaii', ID='Idaho', IL='Illinois', IN='Indiana', IA='Iowa', KS='Kansas', KY='Kentucky', LA='Louisiana', ME='Maine', MD='Maryland', MA='Massachusetts', MI='Michigan', MN='Minnesota', MS='Mississippi', MO='Missouri', MT='Montana', NE='Nebraska', NV='Nevada', NH='New Hampshire', NJ='New Jersey', NM='New Mexico', NY='New York', NC='North Carolina', ND='North Dakota', OH='Ohio', OK='Oklahoma', OR='Oregon', PA='Pennsylvania', RI='Rhode Island', SC='South Carolina', SD='South Dakota', TN='Tennessee', TX='Texas', UT='Utah', VT='Vermont', VA='Virginia', WA='Washington', WV='West Virginia', WI='Wisconsin', WY='Wyoming')

def get(p):
    for t in range(5):
        try: return json.load(urllib.request.urlopen(B + '?' + urllib.parse.urlencode(dict(p, f='json')), timeout=180))
        except Exception as e: err = e
    raise err

def slug(name): return re.sub(r'[^a-z0-9]', '', re.sub(r' (State )?(Park|Recreation Area|Historic Site|Natural Area)$', '', name, flags=re.I).lower())[:16]
def kind(name):
    n = name.lower()
    if re.search(r'lake|reservoir|river|spring|bay|falls|creek|marsh|swamp|wetland|island', n): return 'Lakes & wetlands'
    if re.search(r'prairie|grassland|savanna|plain', n): return 'Grassland'
    return 'Forest'

def seed(st, top):
    rows = {}; off = 0
    while True:
        d = get(dict(where="State_Nm='%s' AND Des_Tp='SP' AND Mang_Type='STAT'" % st, outFields='Unit_Nm,GIS_Acres,Mang_Name', returnGeometry='false', resultOffset=off, resultRecordCount=1000))
        for f in d.get('features', []):
            a = f['attributes']; r = rows.setdefault(a['Unit_Nm'], dict(acres=0, mgr=a['Mang_Name'])); r['acres'] += a['GIS_Acres'] or 0
        if not d.get('exceededTransferLimit'): break
        off += 1000
    names = sorted(rows, key=lambda n: -rows[n]['acres'])[:top]
    import points
    out = []
    for n in names:
        acres = rows[n]['acres']; k = 1 if acres < 3000 else 3 if acres < 20000 else 5
        try: pts = points.pick(n, k)
        except Exception as ex: print('skipped', n, '-', ex); continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        radius = round(max(1.5, min(12, (acres * 0.004047) ** 0.5 / 2)), 1)
        i = st.lower() + slug(n)
        out.append(dict(id=i, name=n, short=re.sub(r' (State )?(Park|Recreation Area)$', '', n)[:20], states=[STATES[st]], kind=kind(n), lat=round(sum(ys) / len(ys), 4), lon=round(sum(xs) / len(xs), 4),
                        radius=radius, points=pts if k > 1 else None, acres=round(acres), des='SP', mgr=rows[n]['mgr']))
    return out

def run(cmd, env):
    print('$', ' '.join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=ROOT, env=dict(os.environ, **env))
    if r.returncode: sys.exit('step failed: ' + ' '.join(cmd))

if __name__ == '__main__':
    a = sys.argv[1:]; st = a[0].upper(); top = int(a[a.index('--top') + 1]) if '--top' in a else 25
    if st not in STATES: sys.exit('unknown state ' + st)
    scratch = '--scratch' in a
    work = os.path.join(ROOT, 'pipeline', 'work', st) if not scratch else os.path.join(os.environ.get('SCRATCH', '/tmp'), 'state_' + st)
    os.makedirs(work, exist_ok=True); env = {'WORK': work}
    if '--report' not in a:
        pp = os.path.join(work, 'parks.json')
        if not os.path.exists(pp):
            ps = seed(st, top); json.dump([{k: v for k, v in p.items() if v is not None} for p in ps], open(pp, 'w'), indent=1); print(len(ps), 'parks seeded')
        run(['python3', 'pipeline/draft.py', 'all'], env)
        run(['python3', 'pipeline/autogen.py'], env)                       # first pass (Latin names where no common name yet)
        run(['python3', 'pipeline/names.py', '--from-data', os.path.join(work, 'out')], env)
        run(['python3', 'pipeline/autogen.py'], env)                       # second pass with common names
        outs = [f for f in os.listdir(os.path.join(work, 'out')) if f.endswith('.json')]
        print(len(outs), 'places generated in', work)
        if scratch: sys.exit(0)
        order = json.load(open(os.path.join(ROOT, 'data-auto', 'order.json')))
        for f in sorted(outs):
            e = json.load(open(os.path.join(work, 'out', f))); e['park'] = True; e['level'] = 'local'
            json.dump(e, open(os.path.join(ROOT, 'data-auto', f), 'w'), ensure_ascii=False)
            if e['id'] not in order and not os.path.exists(os.path.join(ROOT, 'data', f)): order.append(e['id'])
        json.dump(order, open(os.path.join(ROOT, 'data-auto', 'order.json'), 'w'))
        run(['python3', 'pipeline/wikinames.py', st], {})                   # real Wikipedia names and source links (needs the web)
        run(['python3', 'build/species.py', 'pack'], {})
        run(['python3', 'pipeline/bounds.py'], {})
    import promote_check as pc, species
    ids = [f[:-5] for f in os.listdir(os.path.join(ROOT, 'data-auto')) if f.startswith(st.lower()) and f.endswith('.json') and f != 'order.json']
    ok = 0; held = []
    for i in sorted(ids):
        r = pc.check(species.load(os.path.join(ROOT, 'data-auto', i + '.json')))
        if r['pass_']: ok += 1
        else: held.append((r['name'], r['why']))
    print('%d places for %s: %d pass the promotion floors; %d held: %s' % (len(ids), st, ok, len(held), held))
