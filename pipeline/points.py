#!/usr/bin/env python3
"""points.py <Unit name> [k]: pick k sample points spread across a protected area using its PAD-US outline.
Prints JSON [[lon,lat],...]. Large or fragmented units are sampled in several places instead of one."""
import sys,json,math,urllib.request,urllib.parse
B="https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Fee_Managers_PADUS/FeatureServer/0/query"
def rings(name):
    out=[];off=0
    while True:
        p=dict(where="Unit_Nm='%s'"%name.replace("'","''"),outFields='Unit_Nm',returnGeometry='true',outSR='4326',maxAllowableOffset='0.02',resultOffset=off,resultRecordCount=200,f='json')
        j=json.load(urllib.request.urlopen(B+'?'+urllib.parse.urlencode(p),timeout=180)); fs=j.get('features',[])
        for f in fs: out+=f['geometry']['rings']
        if len(fs)<200: return out
        off+=200
def inside(x,y,r):
    c=False;j=len(r)-1
    for i in range(len(r)):
        xi,yi=r[i];xj,yj=r[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi: c=not c
        j=i
    return c
def pick(name,k=5,grid=40):
    R=rings(name)
    # only outer rings (clockwise in ArcGIS) with some size
    xs=[p[0] for r in R for p in r];ys=[p[1] for r in R for p in r]
    x0,x1,y0,y1=min(xs),max(xs),min(ys),max(ys); cand=[]
    for i in range(grid):
        for j in range(grid):
            x=x0+(x1-x0)*(i+.5)/grid;y=y0+(y1-y0)*(j+.5)/grid
            if any(inside(x,y,r) for r in R): cand.append((x,y))
    if not cand: return [[(x0+x1)/2,(y0+y1)/2]]
    def d(a,b): return math.hypot((a[0]-b[0])*math.cos(math.radians((a[1]+b[1])/2)),a[1]-b[1])
    cx=sum(c[0] for c in cand)/len(cand);cy=sum(c[1] for c in cand)/len(cand)
    pts=[min(cand,key=lambda c:d(c,(cx,cy)))]
    while len(pts)<min(k,len(cand)): pts.append(max(cand,key=lambda c:min(d(c,p) for p in pts)))
    return [[round(p[0],4),round(p[1],4)] for p in pts]
if __name__=='__main__': print(json.dumps(pick(sys.argv[1],int(sys.argv[2]) if len(sys.argv)>2 else 5)))
