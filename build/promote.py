#!/usr/bin/env python3
"""promote.py id [id ...]: promote places from the pilot (stage "pilot" in data/places) to the main app when they pass build/promote_check.py.
Promoting drops the stage key and adds the id to the main order in data/journeys/links.json; the file stays where it is.
Usage: promote.py --from-codes   promotes every place that has an official NPS list and passes the check."""
import json,os,sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(ROOT,'build'))
import promote_check as pc, species
ids=sys.argv[1:]
if ids[:1]==['--from-codes']:
    ids=[k for k,v in json.load(open(os.path.join(ROOT,'jobs/nps/codes.json'))).items() if v['code']]
if ids[:1]==['--local']:
    # --local [--state AR,KY]: every local (state) park in the pilot, or only those of the given states
    from state import STATES
    st={STATES[c] for c in ids[2].upper().split(',')} if ids[1:2]==['--state'] and len(ids)>2 else None
    ids=[]
    for f in sorted(os.listdir(os.path.join(ROOT,'data','places'))):
        if not f.endswith('.json'): continue
        d=json.load(open(os.path.join(ROOT,'data','places',f)))
        if d.get('stage')=='pilot' and d.get('level')=='local' and (st is None or st & set(d.get('states') or [])): ids.append(f[:-5])
    LOCAL=True
else: LOCAL=False
PO=os.path.join(ROOT,'data','journeys','pilot-order.json'); order=json.load(open(PO))
moved=[];held=[];movedids=[];cands=[]
MAX=int(os.environ.get('PROMOTE_MAX') or 0)   # promote only the best MAX (most species + links first); the data-promote workflow sets it to fit the size budget
for i in ids:
    p=os.path.join(ROOT,'data','places',i+'.json')
    if not os.path.exists(p) or json.load(open(p)).get('stage')!='pilot': continue
    e=species.load(p); r=pc.check(e)
    if not r['pass_'] or (not r['official'] and not LOCAL): held.append((e['name'],r['why'] or ['no official list'])); continue
    cands.append((r['species']+r['links'],i,p,e['name']))
cands.sort(key=lambda c:(-c[0],c[1]))
for n,(score,i,p,name) in enumerate(cands):
    if MAX and n>=MAX: held.append((name,['kept in the pilot to stay inside the size budget'])); continue
    raw=open(p).read(); d=json.loads(raw); d.pop('stage',None)
    json.dump(d,open(p,'w'),ensure_ascii=False,indent=1 if raw.startswith('{\n') else None); moved.append(name); movedids.append(i)
order=[x for x in order if x not in movedids]
json.dump(order,open(PO,'w'))
L=os.path.join(ROOT,'data','journeys','links.json'); lk=json.load(open(L))
for i in movedids:
    if i not in lk['order']: lk['order'].append(i)
json.dump(lk,open(L,'w'),indent=1,ensure_ascii=False)
print(len(moved),'promoted;',len(held),'held:',held)
open(os.path.join(ROOT,'promoted.json'),'w').write(json.dumps({'moved':movedids,'held':[[n,w] for n,w in held]}))
