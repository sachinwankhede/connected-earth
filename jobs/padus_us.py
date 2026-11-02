import json,urllib.request,urllib.parse,sys,concurrent.futures as cf
B="https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Fee_Managers_PADUS/FeatureServer/0/query"
def get(p):
    for t in range(4):
        try: return json.load(urllib.request.urlopen(B+'?'+urllib.parse.urlencode(p),timeout=180))
        except Exception as e: err=e
    raise err
def des(d):
    n=get(dict(where="Des_Tp='%s'"%d,returnCountOnly='true',f='json'))['count']
    out={}
    def page(off):
        return get(dict(where="Des_Tp='%s'"%d,outFields='Unit_Nm,Mang_Name,GIS_Acres,State_Nm',returnGeometry='true',outSR='4326',maxAllowableOffset='0.01',resultOffset=off,resultRecordCount=300,f='json')).get('features',[])
    with cf.ThreadPoolExecutor(4) as ex:
        for fs in ex.map(page,range(0,n,300)):
            for f in fs:
                a=f['attributes'];g=f['geometry'];k=a['Unit_Nm']
                u=out.setdefault(k,dict(name=k,des=d,mgr=a['Mang_Name'],acres=0,states=set(),x0=999,x1=-999,y0=99,y1=-99,big=(-1,)))
                u['acres']+=a['GIS_Acres'] or 0;u['states'].add(a['State_Nm'])
                for r in g['rings']:
                    rx=[p[0] for p in r];ry=[p[1] for p in r]
                    u['x0']=min(u['x0'],min(rx));u['x1']=max(u['x1'],max(rx));u['y0']=min(u['y0'],min(ry));u['y1']=max(u['y1'],max(ry))
                    ar=(max(rx)-min(rx))*(max(ry)-min(ry))
                    if ar>u['big'][0]: u['big']=(ar,(min(rx)+max(rx))/2,(min(ry)+max(ry))/2,max(rx)-min(rx),max(ry)-min(ry))
    for u in out.values(): u['states']=sorted(u['states'])
    return n,out
res={}
for d in sys.argv[1:]:
    n,o=des(d);res[d]=o;print(d,n,'features',len(o),'units',flush=True)
json.dump(res,open('padus_us.json','w'))
