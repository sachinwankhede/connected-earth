#!/usr/bin/env python3
"""draft.py <id>|all : species near each park (GBIF) + what each animal eats (GloBI), cached. Writes drafts/<id>.json"""
import sys,json,math,subprocess,urllib.parse,os,csv,io,hashlib
from concurrent.futures import ThreadPoolExecutor
here=os.environ.get('WORK') or os.path.dirname(os.path.abspath(__file__))  # work dir holds cache/ drafts/ parks.json
def curl(u):
    for _ in range(3):
        r=subprocess.run(['curl','-sS','-f','-m','90',u],capture_output=True)
        if r.returncode==0: return r.stdout.decode('utf8','replace')
    return None
def cached(key,fn):
    p=os.path.join(here,'cache',hashlib.md5(key.encode()).hexdigest()+'.json')
    if os.path.exists(p): return json.load(open(p))
    v=fn(); 
    if v is not None: json.dump(v,open(p,'w'))
    return v
G={'Mammals':359,'Birds':212,'Reptiles':11592253,'Amphibians':131,'Fish':204,'Insects':216,'Plants':7707728}
LIM={'Mammals':20,'Birds':34,'Reptiles':10,'Amphibians':8,'Fish':14,'Insects':18,'Plants':30}
def circ(lat,lon,rad):
    pts=[(lon+rad/(111.32*math.cos(math.radians(lat)))*math.cos(2*math.pi*i/16), lat+rad/110.57*math.sin(2*math.pi*i/16)) for i in range(16)]; pts.append(pts[0])
    return 'POLYGON(('+','.join('%.4f %.4f'%p for p in pts)+'))'
def sp(k):
    def f():
        t=curl('https://api.gbif.org/v1/species/%s'%k)
        if not t: return None
        d=json.loads(t); return {'name':d.get('canonicalName') or d.get('species'),'common':d.get('vernacularName'),'family':d.get('family'),'order':d.get('order'),'cls':d.get('class'),'genus':d.get('genus')}
    return k,cached('sp'+str(k),f)
def eats(n):
    def f():
        u='https://api.globalbioticinteractions.org/interaction?sourceTaxon=%s&interactionType=eats&field=source_taxon_name&field=target_taxon_name&field=target_taxon_path&limit=1500&type=csv'%urllib.parse.quote(n)
        t=curl(u)
        if t is None: return None
        rows=list(csv.reader(io.StringIO(t)))[1:]
        names=set()
        for r in rows:
            if len(r)>2 and r[0].lower()==n.lower():
                names.add(r[1])
                for x in r[2].split('|'): names.add(x.strip())
        return sorted(names)
    return n,cached('eats'+n,f)
def run(p):
    out={'id':p['id'],'park':p,'groups':{}}
    pts=p.get('points') or [[p['lon'],p['lat']]]
    def facet(g):
        tot={}
        for (lo,la) in pts:
            wkt=circ(la,lo,p['radius'])
            u='https://api.gbif.org/v1/occurrence/search?limit=0&hasCoordinate=true&occurrenceStatus=PRESENT&taxonKey=%d&geometry=%s&facet=speciesKey&facetLimit=%d'%(G[g],urllib.parse.quote(wkt),LIM[g])
            key='facet%s%s'%(p['id'],g) if len(pts)==1 else 'facet%s%s%.4f%.4f'%(p['id'],g,lo,la)
            t=cached(key,lambda:curl(u) and json.loads(curl(u)))
            f=(t or {}).get('facets',[{}])
            for c in (f[0].get('counts',[]) if f else []): tot[c['name']]=tot.get(c['name'],0)+c['count']
        return g,sorted(tot.items(),key=lambda x:-x[1])[:LIM[g]]
    facs=dict(facet(g) for g in G)
    keys=sorted({k for v in facs.values() for k,_ in v})
    with ThreadPoolExecutor(8) as ex: info=dict(ex.map(sp,keys))
    allsp=[]
    for g,v in facs.items():
        out['groups'][g]=[]
        for k,c in v:
            i=info.get(k)
            if i and i['name'] and len(i['name'].split())>=2:
                out['groups'][g].append(dict(latin=i['name'],common=i['common'],family=i['family'],order=i['order'],cls=i['cls'],genus=i['genus'],records=c)); allsp.append(i['name'])
    cons=[x['latin'] for g in ('Mammals','Birds','Reptiles','Amphibians','Fish','Insects') for x in out['groups'][g]]
    with ThreadPoolExecutor(6) as ex: out['eats']=dict(ex.map(eats,cons))
    json.dump(out,open(os.path.join(here,'drafts',p['id']+'.json'),'w'),ensure_ascii=False)
    return p['id'],{g:len(v) for g,v in out['groups'].items()}
if __name__=='__main__':
    for d in ('cache','drafts'): os.makedirs(os.path.join(here,d),exist_ok=True)
    P=json.load(open(os.path.join(here,'parks.json')))
    sel=[p for p in P if sys.argv[1]=='all' or p['id']==sys.argv[1]]
    with ThreadPoolExecutor(3) as ex:
        for r in ex.map(run,sel): print(*r,flush=True)
