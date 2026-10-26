#!/usr/bin/env python3
"""names.py: find a common English name for species that only have a Latin name.
Uses the Wikipedia page title (it is the common name when one exists) and GBIF's English vernacular names.
Writes pipeline/names.json  {latin: common}. Usage: names.py latin1 latin2 ... | names.py --from-data data-auto"""
import sys,json,os,glob,urllib.request,urllib.parse,time
here=os.path.dirname(os.path.abspath(__file__)); P=os.path.join(here,'names.json')
UA={'User-Agent':'ConnectedEarth/1.0 (sachinw_80@yahoo.com)'}
def get(u):
    for k in range(5):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(5*(k+1)); continue
            if e.code==404: return None
            raise
def lookup(latin):
    j=get('https://en.wikipedia.org/api/rest_v1/page/summary/'+urllib.parse.quote(latin.replace(' ','_')))
    t=(j or {}).get('title')
    if t and t.lower()!=latin.lower() and not t.lower().startswith(latin.split()[0].lower()+' '): return t
    m=get('https://api.gbif.org/v1/species/match?name='+urllib.parse.quote(latin))
    if m and m.get('usageKey'):
        v=get('https://api.gbif.org/v1/species/%s/vernacularNames?limit=60'%m['usageKey'])
        for r in (v or {}).get('results',[]):
            if r.get('language')=='eng' and r.get('vernacularName'): return r['vernacularName'].title()
    return None
if __name__=='__main__':
    names=json.load(open(P)) if os.path.exists(P) else {}
    todo=sys.argv[1:]
    if todo[:1]==['--from-data']:
        todo=set()
        for f in glob.glob(os.path.join(todo and '' or '',sys.argv[2],'*.json')):
            if f.endswith('order.json'): continue
            for n in json.load(open(f))['nodes']:
                if n['latin'] and n['tl']>0 and n['name'].split(' (')[0]==n['latin']: todo.add(n['latin'])
        todo=sorted(todo)
    for l in todo:
        if l in names: continue
        names[l]=lookup(l); time.sleep(0.3); print(l,'->',names[l],flush=True)
        json.dump(names,open(P,'w'),indent=1,ensure_ascii=False)
