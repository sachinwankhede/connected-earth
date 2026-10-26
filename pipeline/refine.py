import json,subprocess,urllib.parse,statistics,math,re
from concurrent.futures import ThreadPoolExecutor
from parks import P
def curl(u):
    for _ in range(3):
        r=subprocess.run(['curl','-sS','-f','-m','60',u],capture_output=True)
        if r.returncode==0: return r.stdout.decode()
def circ(lat,lon,rad):
    pts=[(lon+rad/(111.32*math.cos(math.radians(lat)))*math.cos(2*math.pi*i/16), lat+rad/110.57*math.sin(2*math.pi*i/16)) for i in range(16)]; pts.append(pts[0])
    return 'POLYGON(('+','.join('%.4f %.4f'%p for p in pts)+'))'
def km(a,b,c,d): return math.hypot((a-c)*110.57,(b-d)*111.32*math.cos(math.radians(a)))
def one(p):
    name,short,county,acres,lat,lon,kind=p
    core=re.sub(r"^(Dr\. |Edward \"Ted\" and Pat |Annie and Abel |Harry S |Don |Sam A\. )","",name).replace(' State Park','').replace(' Memorial','')
    key=core.lower().split(',')[0]
    pts=[]
    for off in (0,300):
        u='https://api.gbif.org/v1/occurrence/search?limit=300&offset=%d&hasCoordinate=true&country=US&stateProvince=Missouri&q=%s&geometry=%s'%(off,urllib.parse.quote(core+' State Park'),urllib.parse.quote(circ(lat,lon,14)))
        t=curl(u)
        if not t: break
        for r in json.loads(t)['results']:
            s=json.dumps(r).lower()
            if key in s and ('state park' in s or key.split()[0] in s) and r.get('coordinateUncertaintyInMeters',0)<3000:
                pts.append((r['decimalLatitude'],r['decimalLongitude']))
    out=dict(name=name,short=short,county=county,acres=acres,kind=kind,seed=[lat,lon],n=len(pts))
    if len(pts)>=6:
        la=statistics.median(x[0] for x in pts); lo=statistics.median(x[1] for x in pts)
        out.update(lat=round(la,4),lon=round(lo,4),shift_km=round(km(lat,lon,la,lo),1),conf='gbif')
    else: out.update(lat=lat,lon=lon,shift_km=0,conf='seed')
    return out
with ThreadPoolExecutor(6) as ex: res=list(ex.map(one,P))
json.dump(res,open('parks.json','w'),indent=1)
for r in res: print('%-52s n=%-4d %-5s shift=%s'%(r['name'][:52],r['n'],r['conf'],r['shift_km']))
