import json,urllib.request,urllib.parse,collections,sys
B="https://services.arcgis.com/v01gqwM5QqNysAAi/arcgis/rest/services/Fee_Managers_PADUS/FeatureServer/0/query"
def q(where,off):
    p=dict(where=where,outFields='Unit_Nm,Des_Tp,Mang_Name,GIS_Acres,Date_Est',returnGeometry='true',outSR='4326',maxAllowableOffset='0.003',resultOffset=off,resultRecordCount=500,f='json')
    return json.load(urllib.request.urlopen(B+'?'+urllib.parse.urlencode(p),timeout=120))
out={};BIG={}
for des in sys.argv[2:]:
    off=0
    while True:
        d=q("State_Nm='%s' AND Des_Tp='%s'"%(sys.argv[1],des),off)
        for f in d.get('features',[]):
            a=f['attributes'];g=f['geometry']
            xs=[pt[0] for r in g['rings'] for pt in r];ys=[pt[1] for r in g['rings'] for pt in r]
            for r in g['rings']:
                rx=[p[0] for p in r];ry=[p[1] for p in r];ar=(max(rx)-min(rx))*(max(ry)-min(ry))
                if ar>BIG.get(a['Unit_Nm'],(-1,))[0]: BIG[a['Unit_Nm']]=(ar,(min(rx)+max(rx))/2,(min(ry)+max(ry))/2,max(rx)-min(rx),max(ry)-min(ry))
            k=(a['Unit_Nm'],des);u=out.setdefault(k,dict(name=a['Unit_Nm'],des=des,mgr=a['Mang_Name'],acres=0,x0=999,x1=-999,y0=99,y1=-99))
            u['acres']+=a['GIS_Acres'] or 0;u['x0']=min(u['x0'],min(xs));u['x1']=max(u['x1'],max(xs));u['y0']=min(u['y0'],min(ys));u['y1']=max(u['y1'],max(ys))
        if not d.get('exceededTransferLimit'): break
        off+=500
[u.update(big=BIG[u['name']][1:]) for u in out.values()]
json.dump(list(out.values()),open('padus_%s.json'%sys.argv[1],'w'),indent=0)
for u in sorted(out.values(),key=lambda u:-u['acres'])[:80]: print(u['des'],u['name'],round(u['acres']),u['mgr'])
print(len(out))
