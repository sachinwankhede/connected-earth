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
order=json.load(open(os.path.join(ROOT,'data-auto/order.json')))
moved=[];held=[]
for i in ids:
    p=os.path.join(ROOT,'data-auto',i+'.json')
    if not os.path.exists(p): continue
    e=json.load(open(p)); r=pc.check(e)
    if not r['pass_'] or not r['official']: held.append((e['name'],r['why'] or ['no official list'])); continue
    subprocess.run(['git','mv',p,os.path.join(ROOT,'data',i+'.json')],check=True,cwd=ROOT); moved.append(e['name']); 
order=[x for x in order if x not in {os.path.basename(m) for m in ids}]
json.dump([x for x in order if os.path.exists(os.path.join(ROOT,'data-auto',x+'.json'))],open(os.path.join(ROOT,'data-auto/order.json'),'w'))
print(len(moved),'promoted;',len(held),'held:',held)
