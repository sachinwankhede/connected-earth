#!/usr/bin/env python3
"""bounds.py: real park outlines from PAD-US (US Geological Survey, public domain) for US places.
For each US place, ask PAD-US for protected areas around the place point, keep the pieces whose name matches the place,
simplify and write one file per place, data/outlines/<place id>.json = {"n": unit name, "r": [ring, ...]} with rings as flat [lon,lat,...]
lists rounded to 4 decimals (the app fetches a park's file when the park opens; no file = no outline).
Resumable: places that already have a file are skipped.  Usage: bounds.py [id ...]"""
import json,os,re,sys,time,urllib.request,urllib.parse
here=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(here)
sys.path.insert(0,os.path.join(ROOT,'build')); import species
B="https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Fee_Managers_PADUS/FeatureServer/0/query"
OUT=os.path.join(ROOT,'data','outlines')
def path(i): return os.path.join(OUT,i+'.json')
STOP=set('national state park forest refuge wildlife nwr monument historic site memorial recreation area preserve seashore lakeshore river the of and wilderness natural conservation'.split())
import unicodedata
def toks(s): return {w for w in re.findall(r'[a-z]+',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().replace("'s",'s')) if w not in STOP and len(w)>2}
def get(p, empty_ok=False):
    """The service sometimes answers with no 'features', or an empty list, when asked quickly; that looked like 'no match'
    (17 of 23 Iowa parks). So wait and ask again. An empty list is accepted as real only after 3 empty answers (empty_ok)."""
    err = RuntimeError('PAD-US gave no answer'); empties = 0
    for t in range(6):
        try:
            j = json.load(urllib.request.urlopen(B+'?'+urllib.parse.urlencode(p),timeout=120))
            if j.get('features'): return j
            empties += 1; err = RuntimeError('PAD-US gave no features')
            if empty_ok and 'features' in j and empties >= 3: return j
        except Exception as e: err=e
        time.sleep(3*(t+1))
    if empty_ok: return {'features': []}
    raise err
def places():
    for p in species.files():
        e=json.load(open(p))
        if e.get('country')=='United States of America' and e.get('park') and e.get('lat') is not None: yield e
def fetch(e):
    big=e.get('level')!='local'
    off=0.01 if big else 0.0006
    p=dict(geometry='%s,%s'%(e['lon'],e['lat']),geometryType='esriGeometryPoint',inSR='4326',spatialRel='esriSpatialRelIntersects',distance=40000 if big else 4000,units='esriSRUnit_Meter',
           outFields='Unit_Nm,Des_Tp,GIS_Acres',returnGeometry='true',outSR='4326',maxAllowableOffset=off,f='json',resultRecordCount=200)
    fs=get(p,True).get('features',[])   # an empty list is a real answer for a place outside PAD-US; retried a few times first
    want=toks(e['name'])|toks(e.get('short',''))
    best=[]
    sc={}
    for f in fs:
        n=f['attributes']['Unit_Nm'] or ''; t=toks(n)
        s=len(want&t)/max(1,len(want|t)) if t else 0
        sc.setdefault(n,[0,0]); sc[n][0]=s; sc[n][1]+=f['attributes']['GIS_Acres'] or 0
    if not sc: return None
    top=max(sc,key=lambda n:(sc[n][0],sc[n][1]))
    if sc[top][0]<0.34: return None
    rings=[]
    for f in fs:
        if f['attributes']['Unit_Nm']==top: rings+=f['geometry']['rings']
    out=[]
    for r in rings:
        if len(r)<4: continue
        flat=[]
        for x,y in r: flat+= [round(x,4),round(y,4)]
        out.append(flat)
    return top,out
if __name__=='__main__':
    os.makedirs(OUT,exist_ok=True)
    want=sys.argv[1:]; miss=[]; have=sum(1 for f in os.listdir(OUT) if f.endswith('.json'))
    for e in places():
        if want and e['id'] not in want: continue
        if os.path.exists(path(e['id'])): continue
        try: r=fetch(e)
        except Exception as ex: print('ERR',e['id'],ex); continue
        if not r: miss.append(e['id']); print('none',e['id'],e['name'],flush=True); continue
        json.dump({'n':r[0],'r':r[1]},open(path(e['id']),'w'),separators=(',',':'),ensure_ascii=False); have+=1
        print('ok',e['id'],r[0],len(r[1]),flush=True)
    print(have,'outlines;',len(miss),'without a match')
