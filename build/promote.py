#!/usr/bin/env python3
"""promote.py id [id ...]: move places from data-auto/ (pilot) to data/ (main) when they pass build/promote_check.py.
Usage: promote.py --from-codes   promotes every place that has an official NPS list and passes the check."""
import json,os,sys,subprocess
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,os.path.join(ROOT,'build'))
import promote_check as pc
ids=sys.argv[1:]
if ids[:1]==['--from-codes']:
    ids=[k for k,v in json.load(open(os.path.join(ROOT,'pipeline/nps/codes.json'))).items() if v['code']]
if ids[:1]==['--local']:
    ids=[]
    for f in sorted(os.listdir(os.path.join(ROOT,'data-auto'))):
        if f.endswith('.json') and f!='order.json' and json.load(open(os.path.join(ROOT,'data-auto',f))).get('level')=='local': ids.append(f[:-5])
    LOCAL=True
else: LOCAL=False
order=json.load(open(os.path.join(ROOT,'data-auto/order.json')))
moved=[];held=[];movedids=[]
for i in ids:
    p=os.path.join(ROOT,'data-auto',i+'.json')
    if not os.path.exists(p): continue
    e=json.load(open(p)); r=pc.check(e)
    if not r['pass_'] or (not r['official'] and not LOCAL): held.append((e['name'],r['why'] or ['no official list'])); continue
    subprocess.run(['git','mv',p,os.path.join(ROOT,'data',i+'.json')],check=True,cwd=ROOT); moved.append(e['name']); movedids.append(i)
order=[x for x in order if x not in movedids]
json.dump([x for x in order if os.path.exists(os.path.join(ROOT,'data-auto',x+'.json'))],open(os.path.join(ROOT,'data-auto/order.json'),'w'))
L=os.path.join(ROOT,'data','links.json'); lk=json.load(open(L))
for i in movedids:
    if i not in lk['order']: lk['order'].append(i)
json.dump(lk,open(L,'w'),indent=1,ensure_ascii=False)
print(len(moved),'promoted;',len(held),'held:',held)
