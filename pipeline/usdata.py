import json,math,urllib.request,urllib.parse,concurrent.futures as cf
C=json.load(open('us_candidates.json'))
def circ(la,lo,r):
    pts=[]
    for i in range(24):
        a=2*math.pi*i/24;pts.append('%.4f %.4f'%(lo+r/(111*math.cos(math.radians(la)))*math.cos(a),la+r/111*math.sin(a)))
    pts.append(pts[0]);return 'POLYGON((%s))'%','.join(pts)
def n(u):
    b=u['big'];la,lo=b[2],b[1];dx=b[3]*111*math.cos(math.radians(la));dy=b[4]*111
    r=max(2,min(12,0.4*max(dx,dy)));u['lat']=la;u['lon']=lo;u['radius']=r
    q=urllib.parse.urlencode(dict(geometry=circ(la,lo,r),hasCoordinate='true',limit=0,facet='speciesKey',facetLimit=200,**{'taxonKey':'1'}))
    for t in range(3):
        try:
            d=json.load(urllib.request.urlopen('https://api.gbif.org/v1/occurrence/search?'+q+'&kingdomKey=1',timeout=60))
            f=d['facets'][0]['counts'];u['nsp']=len(f);return u
        except Exception as e: u['err']=str(e)
    u['nsp']=-1;return u
with cf.ThreadPoolExecutor(6) as ex: R=list(ex.map(n,C))
json.dump(R,open('us_candidates2.json','w'))
import collections
print(collections.Counter('err' if u['nsp']<0 else '<60' if u['nsp']<60 else '<150' if u['nsp']<150 else '150+' for u in R))
