#!/usr/bin/env python3
"""Validate one ecosystem data file: python3 validate.py data_new/<id>.json"""
import json,re,sys,os,difflib
here=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(here)
tpl=open(os.path.join(ROOT,'src','app.html')).read()
i0=tpl.index('var ICONS = {'); i1=tpl.index('\n  };',i0)
ICONS=set(re.findall(r"^\s{4}(\w+):",tpl[i0:i1],re.M))
geo=json.load(open(os.path.join(ROOT,'src','geo.json')))
C={c['name']:c['cont'] for c in geo['countries']}; S={s['name'] for s in geo['states']}
sys.path.insert(0,here)
import species
def check(path):
    e=species.load(path); errs=[]; warn=[]
    for k in ('id','name','short','place','lat','lon','side','blurb','tip','sources','notes','nodes','raw','cont','country','imgwiki','icon','tier','kind'):
        if k not in e: errs.append('missing field '+k)
    if errs: return errs,warn
    if os.path.basename(path)!=e['id']+'.json': errs.append('file name must be <id>.json')
    if not re.fullmatch(r'[a-z][a-z0-9]*',e['id']): errs.append('id must be lowercase letters/digits')
    if e['side'] not in ('l','r'): errs.append('side must be l or r')
    if not(-90<=e['lat']<=90 and -180<=e['lon']<=180): errs.append('lat/lon out of range')
    if e['country'] not in C: errs.append('country %r not in geo.json; close: %s'%(e['country'],difflib.get_close_matches(e['country'],list(C),3)))
    elif C[e['country']]!=e['cont']: errs.append('continent for %s should be %s'%(e['country'],C[e['country']]))
    for s in e.get('states',[]):
        if s not in S: errs.append('unknown US state '+s)
    if e.get('states') and 'United States of America' not in e.get('countries',[e['country']]): errs.append('states only for the United States')
    if e['icon'] not in ICONS: errs.append('eco icon %s not in ICONS'%e['icon'])
    if e['tier'] not in ('overview','detailed'): errs.append('tier must be overview or detailed')
    if not (isinstance(e['sources'],list) and 1<=len(e['sources'])<=8 and all(s.get('url','').startswith('https://') and s.get('title') for s in e['sources'])): errs.append('need 1-8 sources (aim for 3 or more) with title and https url')
    if len(e['sources'])<3: warn.append('only %d sources; aim for 3 or more'%len(e['sources']))
    ids=[n['id'] for n in e['nodes']]
    if len(ids)!=len(set(ids)): errs.append('duplicate node ids')
    names=[n['name'] for n in e['nodes']]
    if len(names)!=len(set(names)): errs.append('duplicate node names')
    sp=[n for n in e['nodes'] if not n.get('cat')]
    if not 10<=len(sp)<=34: errs.append('species count %d outside 10-34'%len(sp))
    cats={n.get('cat') for n in e['nodes']}
    if 'abiotic' not in cats or 'decomp' not in cats: errs.append('need at least one abiotic and one decomp node')
    for n in e['nodes']:
        for k in ('id','name','latin','tl','xh','wiki','desc','ic'):
            if k not in n: errs.append('%s missing %s'%(n.get('id'),k))
        if n.get('tl') not in (0,1,2,3,4): errs.append(n['id']+' bad tl')
        if n.get('cat') in ('abiotic','decomp') and n.get('tl')!=0: errs.append(n['id']+' env/decomp must be tl 0')
        if not n.get('cat') and n.get('tl')==0: errs.append(n['id']+' species cannot be tl 0')
        if not 0<=n.get('xh',-1)<=1: errs.append(n['id']+' xh must be 0..1')
        if n.get('ic') not in ICONS: errs.append('%s icon %s unknown'%(n['id'],n.get('ic')))
        if len(n.get('desc',''))<30 or len(n['desc'])>330: warn.append(n['id']+' desc length %d (aim 40-300)'%len(n.get('desc','')))
        if not re.fullmatch(r'[a-z][a-z0-9]*',n.get('id','')): errs.append('bad node id '+str(n.get('id')))
    S_=set(ids); tl={n['id']:n['tl'] for n in e['nodes']}; seen=set()
    for r in e['raw']:
        if len(r) not in (2,3) or r[0] not in S_ or r[1] not in S_: errs.append('bad edge %s'%r); continue
        k=tuple(r)
        if k in seen: errs.append('duplicate edge %s'%r)
        seen.add(k)
        if len(r)==3 and r[2] not in ('s','r','d'): errs.append('bad edge kind %s'%r)
        if len(r)==2 and tl[r[0]]!=0 and tl[r[1]]<=tl[r[0]]-1 and tl[r[1]]<tl[r[0]]: warn.append('eats edge goes downward in tl: %s'%r)
    if e['tip']['id'] not in S_: errs.append('tip.id not a node')
    deg={i:0 for i in ids}
    for r in e['raw']:
        if r[0] in deg and r[1] in deg: deg[r[0]]+=1; deg[r[1]]+=1
    for i,d in deg.items():
        if d==0: errs.append('node %s has no links'%i)
    for n in sp:
        if n['tl']>=2 and not any(r[1]==n['id'] and (len(r)==2) for r in e['raw']): warn.append('consumer %s has no food (eats) edge'%n['id'])
    return errs,warn
if __name__=='__main__':
    bad=0
    for p in sys.argv[1:]:
        errs,warn=check(p)
        print(p, 'OK' if not errs else 'ERRORS')
        for x in errs: print('  ERROR',x)
        for x in warn: print('  warn ',x)
        bad+=bool(errs)
    sys.exit(1 if bad else 0)
