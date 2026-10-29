#!/usr/bin/env python3
"""autogen.py : drafts/<id>.json -> out/<id>.json in the app's ecosystem schema (automatic, no hand curation)."""
import json,os,re,sys,collections
here=os.path.dirname(os.path.abspath(__file__)); work=os.environ.get('WORK') or here; os.makedirs(os.path.join(work,'out'),exist_ok=True)
# ---- layer rules (by taxonomy) ----
APEX={'Canis latrans','Lynx rufus','Ursus americanus','Puma concolor','Haliaeetus leucocephalus','Buteo jamaicensis','Bubo virginianus','Strix varia','Buteo lineatus','Alligator mississippiensis','Esox americanus'}
SCAV={'Cathartes aura','Coragyps atratus','Didelphis virginiana'}
def layer(g,s):
    o,f,c,l=s.get('order') or '',s.get('family') or '',s.get('cls') or '',s['latin']
    if g=='Plants': return 1
    if l in APEX: return 4
    if g=='Insects': return 3 if o in ('Odonata','Mantodea','Neuroptera') or f in ('Carabidae','Coccinellidae','Asilidae','Vespidae') else 2
    if g=='Fish': return 2 if f in ('Cyprinidae','Catostomidae') else 3
    if g=='Amphibians': return 3
    if g=='Reptiles': return 2 if o=='Testudines' and f in ('Emydidae','Trionychidae')==False and f=='Emydidae' else 3
    if g=='Birds':
        if o in ('Accipitriformes','Falconiformes','Strigiformes'): return 3
        if o in ('Anseriformes','Galliformes','Columbiformes'): return 2
        if o=='Passeriformes': return 2 if f in ('Cardinalidae','Fringillidae','Passerellidae','Emberizidae','Icteridae','Paridae','Passeridae','Estrildidae') else 3
        return 3
    if g=='Mammals':
        if o in ('Rodentia','Lagomorpha','Artiodactyla','Perissodactyla'): return 2
        return 3
    return 3
def icon(g,s,tl):
    o,f=(s.get('order') or ''),(s.get('family') or ''); l=s['latin']
    if g=='Plants': return 'grass' if f=='Poaceae' else 'aspen'
    if g=='Fish': return 'trout'
    if g=='Insects': return 'ant' if o=='Hymenoptera' else 'mayfly' if o in ('Odonata','Ephemeroptera') else 'hopper'
    if g=='Reptiles': return 'snake' if o=='Squamata' and f in ('Colubridae','Viperidae','Natricidae','Dipsadidae') else 'shell' if o=='Testudines' else 'quad'
    if g=='Amphibians': return 'quad'
    if g=='Birds': return 'baldeagle' if f=='Accipitridae' and tl>=3 else 'hawk' if o in ('Accipitriformes','Falconiformes','Strigiformes') else 'raven' if f=='Corvidae' else 'osprey' if o in ('Pelecaniformes','Charadriiformes','Coraciiformes') else 'meadowlark'
    if g=='Mammals':
        if f=='Canidae': return 'coyote' if 'Canis' in l else 'fox'
        if f=='Cervidae': return 'muledeer'
        if f=='Sciuridae': return 'rsquirrel' if 'Sciurus' in l else 'gsquirrel'
        if f=='Castoridae': return 'beaver'
        if f=='Mustelidae': return 'otter'
        if f=='Ursidae': return 'grizzly'
        return 'quad'
    return 'quad'
_N=json.load(open(os.path.join(here,'names.json'))) if os.path.exists(os.path.join(here,'names.json')) else {}
def clean(s):
    return re.sub(r'\s+',' ',re.sub(r'\s*\[[^\]]*\]','',s.split(',')[0])).strip()
def titled(s): return s[:1].upper()+s[1:]
ROLE={1:'a plant that turns sunlight into food',2:'eats plants or other primary food sources',3:'hunts or scavenges other animals',4:'a top predator in this web'}
RAPTOR={'Accipitriformes','Strigiformes','Falconiformes','Cathartiformes'}
ABSENT={'Canis lupus'}
NAMES={'Danaus plexippus':'Monarch butterfly','Cervus elaphus':'Elk','Cervus canadensis':'Elk','Sus scrofa':'Feral pig','Asimina triloba':'Pawpaw','Trillium recurvatum':'Prairie trillium','Perilla frutescens':'Perilla (beefsteak mint)','Rhus aromatica':'Fragrant sumac','Phlox divaricata':'Wild blue phlox','Claytonia virginica':'Spring beauty','Tephrosia virginiana':"Goat's rue",'Sambucus canadensis':'American elderberry','Staphylea trifolia':'American bladdernut','Branta canadensis':'Canada goose','Mertensia virginica':'Virginia bluebells','Podophyllum peltatum':'Mayapple'}
def plausible(c,s):
    if c['latin'].split()[0] in ('Nerodia','Thamnophis') and s['g'] in ('Mammals','Birds'): return False
    # eater c, food s: block records that are biologically implausible (size / diet)
    if s['g'] in ('Mammals','Birds') and c['g']=='Birds' and c.get('order') not in RAPTOR: return False
    if s['g'] in ('Mammals','Birds') and c['g']=='Mammals' and c.get('order') not in ('Carnivora','Didelphimorphia','Soricomorpha','Eulipotyphla'): return False
    if s['g']=='Mammals' and c['g'] in ('Amphibians','Fish','Insects'): return False
    return True
def build(d):
    p=d['park']; cand=[]
    for g,L in d['groups'].items():
        for s in L:
            if s['latin'] in ABSENT: continue
            if d.get('nps') and g!='Insects' and s['latin'].lower() not in d['nps']: continue   # official park list: keep only species the park confirms (it has no insect list)
            tl=layer(g,s); cand.append(dict(g=g,tl=tl,**s))
    # balanced pick: quotas per taxonomic group so frequently-recorded birds do not crowd everything else out
    quota={'Plants':6,'Mammals':6,'Birds':6,'Reptiles':3,'Amphibians':2,'Fish':3,'Insects':4}
    cap={1:6,2:10,3:10,4:3}
    chosen=collections.defaultdict(list); seen=set(); gcount=collections.Counter()
    for c in sorted(cand,key=lambda c:-c['records']):
        if c['latin'] in seen or gcount[c['g']]>=quota[c['g']] or len(chosen[c['tl']])>=cap[c['tl']]: continue
        if sum(1 for x in chosen[c['tl']] if x['family']==c['family'])>=2: continue
        chosen[c['tl']].append(c); seen.add(c['latin']); gcount[c['g']]+=1
    # ---- edges from GloBI ----
    def mk_edges(sel):
        by={x['latin']:x for x in sel}; E={}
        for c in sel:
            if c['tl']<2: continue
            T=set(t.lower() for t in d['eats'].get(c['latin'],[]) or [])
            if not T: continue
            for s in sel:
                if s is c or s['tl']>=c['tl'] and not (c['tl']==4 and s['tl']==3 and False): continue
                if not plausible(c,s): continue
                lv=None
                if s['latin'].lower() in T: lv='g'
                elif s['g']=='Plants' and s['genus'] and s['genus'].lower() in T: lv='gg'
                elif s['g']=='Plants' and s['family'] and s['family'].lower() in T: lv='gf'
                if lv: E[(s['latin'],c['latin'])]=lv
        return E
    sel=[c for tl in (1,2,3,4) for c in chosen[tl]]
    for _ in range(3):
        E=mk_edges(sel); eaters={b for a,b in E}
        drop=[c for c in sel if c['tl']>=2 and c['latin'] not in eaters]
        keep=[c for c in sel if c not in drop]
        if len([c for c in keep if c['tl']==1])>=3 and len(keep)>=12: sel=keep
        else: break
    E=mk_edges(sel)
    # a plant or prey nobody eats is fine, but drop animals that are completely unlinked
    linked={a for a,b in E}|{b for a,b in E}
    sel=[c for c in sel if c['tl']==1 or c['latin'] in linked]
    E=mk_edges(sel)
    rank={'g':0,'gg':1,'gf':2}; byfood=collections.defaultdict(list)
    for (a,b),lv in E.items(): byfood[a].append((rank[lv],b))
    for a,L in byfood.items():
        if len(L)>8:
            for _,b in sorted(L)[8:]:
                if sum(1 for (x,y) in E if y==b)>1: del E[(a,b)]
    return p,sel,E
def emit(d):
    p,sel,E=build(d)
    if sum(1 for c in sel if c['tl']==1)<3 or len(sel)<10: return None,{'id':p['id'],'skipped':'only %d species / %d plants after filtering'%(len(sel),sum(1 for c in sel if c['tl']==1))}
    ids={}; used=set()
    for c in sel:
        nm=NAMES.get(c['latin']) or (clean(d['npscommon'][c['latin'].lower()]) if d.get('npscommon',{}).get(c['latin'].lower()) else None) or (clean(c['common']) if c['common'] else None) or _N.get(c['latin'])
        if not nm or nm.lower()==c['latin'].lower(): nm=c['latin']
        nm=titled(nm)
        base=re.sub(r'[^a-z0-9]','',nm.lower())[:14] or 'sp'
        i=base; k=2
        while i in used: i=base+str(k); k+=1
        used.add(i); ids[c['latin']]=(i,nm)
    nm_used=collections.Counter(n for _,n in ids.values())
    nodes=[]
    rows=collections.defaultdict(list)
    for c in sel: rows[c['tl']].append(c)
    for tl,L in rows.items():
        n=len(L)
        for j,c in enumerate(sorted(L,key=lambda c:(c['g'],-c['records']))):
            i,nm=ids[c['latin']]
            if nm_used[nm]>1: nm=nm+' ('+c['latin'].split()[-1]+')'
            xh=round(0.07+0.86*(j+0.5)/n,3) if n>1 else 0.5
            nodes.append(dict(id=i,name=nm,latin=c['latin'],tl=tl,xh=xh,wiki=c['latin'],desc='%s (%s): %s. Recorded %s times near the park in GBIF.'%(nm,c['latin'],ROLE[tl],format(c['records'],',')),ic=icon(c['g'],c,tl)))
    nodes+= [dict(id='sun',name='Sunlight',latin='',tl=0,xh=0.12,cat='abiotic',wiki='Sunlight',desc='Plants turn sunlight into food, which starts the whole web.',ic='sun'),
             dict(id='rain',name='Rainfall',latin='',tl=0,xh=0.34,cat='abiotic',wiki='Rain',desc='Rain and river water set how much the plants can grow.',ic='rain'),
             dict(id='soil',name='Soil and nutrients',latin='',tl=0,xh=0.58,cat='abiotic',wiki='Soil',desc='Soil holds the nutrients plants take up.',ic='soil'),
             dict(id='decomp',name='Fungi and bacteria',latin='Decomposer community',tl=0,xh=0.84,cat='decomp',wiki='Decomposer',desc='Break down dead plants and animals and return nutrients to the soil.',ic='decomp')]
    raw=[];ev={}; cmap={c['latin']:c for c in sel}
    for (a,b),lv in E.items():
        ia,ib=ids[a][0],ids[b][0]; raw.append([ia,ib]+(['s'] if cmap[b].get('family')=='Cathartidae' else [])); ev[ia+'>'+ib]=[lv,b,a]
    plants=[c for c in sel if c['tl']==1]
    for c in plants:
        for e in ('sun','rain','soil'): raw.append([e,ids[c['latin']][0],'r'])
    raw.append(['decomp','soil','r'])
    for c in sel: raw.append([ids[c['latin']][0],'decomp','d'])
    deg=collections.Counter()
    for a,b in E: deg[a]+=1; deg[b]+=1
    top=max(sel,key=lambda c:deg[c['latin']]); tid,tnm=ids[top['latin']]
    nm_top=[n['name'] for n in nodes if n['id']==tid][0]
    counts=dict(species=len(sel),edges=len(E),tl={t:len(rows[t]) for t in rows},family_level=sum(1 for v in E.values() if v=='gf'),species_level=sum(1 for v in E.values() if v=='g'),genus_level=sum(1 for v in E.values() if v=='gg'))
    out=dict(id=p['id'],name=p['name'],short=p['short'],place=', '.join(p['states'])+', USA',lat=p['lat'],lon=p['lon'],side='r',cont='North America',country='United States of America',states=p['states'],kind=p['kind'],
        blurb='Species recorded near the park, linked by recorded feeding.',tip=dict(id=tid,title='Remove '+nm_top,text='Set '+nm_top+' to -100% and see which species are affected.'),
        sources=[dict(title='Wikipedia: '+p['name'],url='https://en.wikipedia.org/wiki/'+p['name'].replace(' ','_')),dict(title='GBIF: species occurrence records',url='https://www.gbif.org/'),dict(title='GloBI: Global Biotic Interactions',url='https://www.globalbioticinteractions.org/')],
        notes='Built automatically, not checked by a person. The species are the most often recorded in GBIF within about %s km of the park location (%s). Feeding links are only those with a GloBI record: for the species itself, its genus or, for plants and insects, its family. Library: %s.'%(p['radius'],'location from PAD-US boundary',', '.join(['%s %d'%(k,v) for k,v in counts['tl'].items()]) and 'automatic'),
        imgwiki=re.sub(r'^Dr\. |^Edward "Ted" and Pat ','',p['name']),icon='trout' if p['kind']=='Lakes & wetlands' else 'grass' if p['kind']=='Grassland' else 'aspen',tier='overview',auto=True,nodes=nodes,raw=raw,ev=ev)
    return out,dict(id=p['id'],**counts)
if __name__=='__main__':
    rep=[]
    for f in sorted(os.listdir(os.path.join(work,'drafts'))):
        d=json.load(open(os.path.join(work,'drafts',f)))
        out,r=emit(d); rep.append(r)
        if out: json.dump(out,open(os.path.join(work,'out',out['id']+'.json'),'w'),ensure_ascii=False)
    json.dump(rep,open(os.path.join(work,'report.json'),'w'),indent=1)
    ok=[r for r in rep if 'skipped' not in r]; print(len(rep),'parks;',len(ok),'built;',[r for r in rep if 'skipped' in r])
