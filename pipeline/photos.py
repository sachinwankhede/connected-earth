#!/usr/bin/env python3
"""photos.py: store each place's photo in the repo with its author and licence.
Usage: photos.py <outdir> <data-dir> [<data-dir>...]   writes <outdir>/<id>.jpg and <outdir>/places.json (resumable)
Source: Wikipedia page summary (thumbnail, 330px wide) + file metadata from the English Wikipedia API (Commons files)."""
import sys,os,re,json,glob,time,html,urllib.request,urllib.parse
UA={'User-Agent':'ConnectedEarth/1.0 (sachinw_80@yahoo.com)'}
def get(u,raw=False):
    for k in range(7):
        try:
            b=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read()
            return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(6*(k+1)); continue
            if e.code==404: return None
            raise
        except Exception: time.sleep(3)
def strip(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',s or ''))).strip()
def one(i,title,out,man):
    j=get('https://en.wikipedia.org/api/rest_v1/page/summary/'+urllib.parse.quote(title.replace(' ','_')))
    th=(j or {}).get('thumbnail')
    if not th: return 'nophoto'
    m=re.search(r'/commons/thumb/\w/\w\w/([^/]+)/',th['source'])
    if not m: return 'notcommons'
    fn=urllib.parse.unquote(m.group(1)); path=os.path.join(out,i+'.jpg')
    if not os.path.exists(path):
        b=get(th['source'],raw=True)
        if not b: return 'nodl'
        open(path,'wb').write(b)
    q=get('https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata&format=json&titles='+urllib.parse.quote('File:'+fn))
    md=(list((q or {}).get('query',{}).get('pages',{}).values()) or [{}])[0].get('imageinfo',[{}])[0].get('extmetadata',{})
    v=lambda k: strip((md.get(k) or {}).get('value'))
    man[title]=dict(f=i+'.jpg',a=v('Artist') or v('Credit') or 'Unknown author',l=v('LicenseShortName') or 'See file page',lu=v('LicenseUrl'),p='https://commons.wikimedia.org/wiki/File:'+urllib.parse.quote(fn.replace(' ','_')),w='https://en.wikipedia.org/wiki/'+urllib.parse.quote(j.get('title',title).replace(' ','_')))
    return 'ok'
if __name__=='__main__':
    out=sys.argv[1]; os.makedirs(out,exist_ok=True); mp=os.path.join(out,'places.json')
    man=json.load(open(mp)) if os.path.exists(mp) else {}
    stat={}
    for d in sys.argv[2:]:
        for f in sorted(glob.glob(d+'/*.json')):
            if f.endswith(('order.json','links.json')): continue
            e=json.load(open(f)); t=e.get('imgwiki')
            if not t or t in man: continue
            try: r=one(e['id'],t,out,man)
            except Exception as ex: r='err '+str(ex)[:50]
            stat[t]=r; time.sleep(0.8)
            json.dump(man,open(mp,'w'),ensure_ascii=False,indent=0)
            if r!='ok': print(t,r,flush=True)
    print('done',len(man),'photos; problems:',sum(1 for r in stat.values() if r!='ok'))
