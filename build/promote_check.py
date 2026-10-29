#!/usr/bin/env python3
"""promote_check.py [id ...]: check pilot places against docs/PROMOTION.md (floors, official list, photo). Does not move anything."""
import json,glob,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import species
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
man=json.load(open(os.path.join(ROOT,'photos/places/places.json'))) if os.path.exists(os.path.join(ROOT,'photos/places/places.json')) else {}
FAMILY_MAX=0.6   # a place whose links are mostly family-level (the eater is recorded eating the plant's family, not that species) stays in the pilot
def check(e):
    sp=[n for n in e['nodes'] if n['tl']>0]; pl=[n for n in sp if n['tl']==1]
    links=[r for r in e['raw'] if len(r)>=2 and r[0] not in('sun','rain','soil','decomp') and r[1]!='decomp' and (len(r)==2 or r[2]=='s')]
    official='official' in (e.get('notes') or '').lower() and 'checklist' in (e.get('notes') or '').lower()
    fl=(8,3,10) if official else (12,5,15)
    why=[]
    if len(sp)<fl[0]: why.append('species %d<%d'%(len(sp),fl[0]))
    if len(pl)<fl[1]: why.append('plants %d<%d'%(len(pl),fl[1]))
    if len(links)<fl[2]: why.append('links %d<%d'%(len(links),fl[2]))
    ev=e.get('ev') or {}; fam=sum(1 for r in links if (ev.get('%s>%s'%(r[0],r[1])) or [''])[0]=='gf')
    if links and fam/len(links)>FAMILY_MAX: why.append('family-level links %d%%>%d%%'%(round(100*fam/len(links)),round(100*FAMILY_MAX)))
    unev=[r for r in links if '%s>%s'%(r[0],r[1]) not in (e.get('ev') or {})]
    if unev: why.append('%d links without evidence'%len(unev))
    ph='stored' if e.get('imgwiki') in man else ('icon/live' )
    return dict(id=e['id'],name=e['name'],official=official,species=len(sp),plants=len(pl),links=len(links),photo=ph,pass_=not why,why=why)
if __name__=='__main__':
    want=set(sys.argv[1:]); rows=[]
    for f in sorted(glob.glob(os.path.join(ROOT,'data-auto','*.json'))):
        if f.endswith('order.json'): continue
        e=species.load(f)
        if want and e['id'] not in want: continue
        rows.append(check(e))
    ok=[r for r in rows if r['pass_']]
    print(len(rows),'checked;',len(ok),'pass')
    for r in rows:
        if not r['pass_']: print('  FAIL',r['name'],'|',', '.join(r['why']))
