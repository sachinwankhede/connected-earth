#!/usr/bin/env python3
"""codes.py: match pilot places managed by the National Park Service to their NPS unit codes.
Tries likely 4-letter codes and checks the nps.gov page title names the same place. Writes pipeline/nps/codes.json."""
import json,glob,re,itertools,subprocess,sys,os,time
here=os.path.dirname(os.path.abspath(__file__)); root=os.path.dirname(os.path.dirname(here))
STOP={'national','park','monument','preserve','recreation','area','and','of','the','historic','site','seashore','lakeshore','river','scenic','riverway','wild','memorial','battlefield','military','historical','parkway','reserve','trail','state','fossil','beds'}
def title(code):
    r=subprocess.run(['curl','-s','-L','-m','25','https://www.nps.gov/%s/index.htm'%code],capture_output=True)
    m=re.search(rb'<title>(.*?)</title>',r.stdout,re.S|re.I)
    return m.group(1).decode('utf8','replace').strip() if m else ''
OVERRIDE={'Gateway Arch National Park':'JEFF','George Washington Memorial Parkway':'GWMP','Lake Chelan National Recreation Area':'LACH','Lake Meredith National Recreation Area':'LAMR','Saint Croix National Scenic Riverway':'SACN','Tule Springs Fossil Beds National Monument':'TUSK','Colorado National Monument':'COLM','Katahdin Woods and Waters National Monument':'KAWW','Chimborazo Park':'RICH'}
def cands(name):
    if name in OVERRIDE: return [OVERRIDE[name]]
    n=re.sub(r"[^a-z ]",' ',name.lower().replace('-',' ')); w=[x for x in n.split() if x not in STOP]; allw=[x for x in n.split() if x not in ('and','of','the')]
    out=[]
    if len(w)>=2: out+= [w[0][:2]+w[1][:2], w[0][:4]+'' ,w[0][:2]+w[-1][:2], w[0][:1]+w[1][:3]]
    if w: out+=[w[0][:4]]
    if len(allw)>=2: out+=[allw[0][:2]+allw[1][:2]]
    if len(w)>=3: out+=[w[0][0]+w[1][0]+w[2][:2]]
    seen=[];[seen.append(c) for c in out if len(c)==4 and c not in seen]; return seen
if __name__=='__main__':
    P={p['id']:p for p in json.load(open(os.path.join(root,'pipeline/reports/us-parks.json')))}
    res=json.load(open(os.path.join(here,'codes.json'))) if os.path.exists(os.path.join(here,'codes.json')) else {}
    for f in sorted(glob.glob(os.path.join(root,'data-auto','us*.json'))):
        e=json.load(open(f)); p=P.get(e['id'],{})
        if p.get('des') not in ('NP','NM','NRA','NLS','WSR') or e['id'] in res: continue
        key=[x for x in re.sub(r"[^a-z ]",' ',e['name'].lower()).split() if x not in STOP|{'national','area'}][:2]
        hit=None
        for c in cands(e['name']):
            t=title(c).lower()
            if t and all(k[:5] in t for k in key) and 'page not found' not in t and 'error' not in t: hit=(c.upper(),t); break
        res[e['id']]=dict(name=e['name'],code=hit[0] if hit else None,title=hit[1] if hit else None)
        print(e['name'],'->',res[e['id']]['code'],'|',res[e['id']]['title'],flush=True)
        json.dump(res,open(os.path.join(here,'codes.json'),'w'),indent=1)
