#!/usr/bin/env python3
"""bounds.py: real park outlines from PAD-US (US Geological Survey, public domain) for US places.
For each US place, ask PAD-US for protected areas around the place point, keep the pieces whose name matches the place,
simplify and write data/bounds.json {place id: [ring, ...]} with rings as flat [lon,lat,...] lists rounded to 4 decimals.
Resumable: places already in bounds.json are skipped.  Usage: bounds.py [id ...]"""
import json,os,re,sys,time,urllib.request,urllib.parse
here=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(here)
sys.path.insert(0,os.path.join(ROOT,'build')); import species
B="https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Fee_Managers_PADUS/FeatureServer/0/query"
OUT=os.path.join(ROOT,'data','bounds.json')
STOP=set('national state park forest refuge wildlife nwr monument historic site memorial recreation area preserve seashore lakeshore river the of and wilderness natural conservation'.split())
import unicodedata
def toks(s): return {w for w in re.findall(r'[a-z]+',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower().replace("'s",'s')) if w not in STOP and len(w)>2}
def get(p):
    for t in range(6):
        try: return json.load(urllib.request.urlopen(B+'?'+urllib.parse.urlencode(p),timeout=120))
        except Exception as e: err=e; time.sleep(5*(t+1))
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
    fs=get(p).get('features',[])
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
    res=json.load(open(OUT)) if os.path.exists(OUT) else {}
    want=sys.argv[1:]; miss=[]
    for e in places():
        if want and e['id'] not in want: continue
        if e['id'] in res: continue
        try: r=fetch(e)
        except Exception as ex: print('ERR',e['id'],ex); continue
        if not r: miss.append(e['id']); print('none',e['id'],e['name'],flush=True); continue
        res[e['id']]={'n':r[0],'r':r[1]}
        json.dump(res,open(OUT,'w'),separators=(',',':'))
        print('ok',e['id'],r[0],len(r[1]),flush=True)
    print(len(res),'outlines;',len(miss),'without a match')
