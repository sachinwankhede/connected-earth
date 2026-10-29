#!/usr/bin/env python3
"""photos.py: store each place's photo in the repo with its author and licence.
Usage: photos.py <outdir> <data-dir> [<data-dir>...]   writes <outdir>/<id>.jpg and <outdir>/places.json (resumable)
Source: Wikipedia page summary (thumbnail, 330px wide) + file metadata from the English Wikipedia API (Commons files)."""
import sys,os,re,json,glob,time,html,urllib.request,urllib.parse
UA={'User-Agent':'ConnectedEarth/1.0 (sachinw_80@yahoo.com)'}
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import wm
def get(u,raw=False): return wm.get(u,raw)
def strip(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',s or ''))).strip()
# Files that are logos, seals, flags or drawings are not photos of the place
NOTPHOTO=re.compile(r'logo|arrowhead|emblem|coat[_ ]of[_ ]arms|seal[_ ]of|(^|[_ ])flag([_ .]|$)|\.svg|map\.(png|jpe?g|gif)$|(^|[_ -])maps?([_ .0-9-]|$)|topograph|locator|diagram|[_ -]chart|waterfowl_counts|(^|[/:])White[_ ]River[_ ]National[_ ]Wildlife[_ ]Refuge\.jpg$',re.I)
def one(i,title,out,man):
    j=get('https://en.wikipedia.org/api/rest_v1/page/summary/'+urllib.parse.quote(title.replace(' ','_')))
    th=(j or {}).get('thumbnail')
    if not th: return 'nophoto'
    m=re.search(r'/commons/thumb/\w/\w\w/([^/]+)/',th['source'])
    if not m: return 'notcommons'
    fn=urllib.parse.unquote(m.group(1)); path=os.path.join(out,i+'.jpg')
    if NOTPHOTO.search(fn): return 'notphoto'
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
    for t in [t for t,v in man.items() if NOTPHOTO.search(urllib.parse.unquote(v.get('p','').split('File:')[-1]))]:   # drop logos stored by earlier runs
        try: os.remove(os.path.join(out,man[t]['f']))
        except OSError: pass
        del man[t]; print('removed non-photo',t,flush=True)
    json.dump(man,open(mp,'w'),ensure_ascii=False,indent=0)
    # Places Wikipedia has no usable photo for are remembered in missing.json so later batches do not try them again (a failed download or a network error is retried).
    ms=os.path.join(out,'missing.json'); miss=json.load(open(ms)) if os.path.exists(ms) else {}
    stat={}; LIMIT=int(os.environ.get('LIMIT','0') or 0); tried=0   # a scheduled run does one batch; 0 = everything left
    for d in sys.argv[2:]:
        for f in sorted(glob.glob(d+'/*.json')):
            if f.endswith(('order.json','links.json')): continue
            e=json.load(open(f)); t=e.get('imgwiki')
            if not t or t in man or t in miss: continue
            if LIMIT and tried>=LIMIT: continue
            tried+=1
            try: r=one(e['id'],t,out,man)
            except Exception as ex: r='err '+str(ex)[:50]
            stat[t]=r
            if r in ('nophoto','notcommons','notphoto'): miss[t]=r; json.dump(miss,open(ms,'w'),ensure_ascii=False,indent=0)
            json.dump(man,open(mp,'w'),ensure_ascii=False,indent=0)
            if r!='ok': print(t,r,flush=True)
    print('done',len(man),'photos;',len(miss),'places with no usable photo; tried',tried,'this run; problems:',sum(1 for r in stat.values() if r not in ('ok','nophoto','notcommons','notphoto')))
    open(os.path.join(out,'.tried'),'w').write(str(tried))
