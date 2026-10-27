#!/usr/bin/env python3
"""about.py: fetch the first sentences of each species' Wikipedia page into pipeline/about.json {wiki title: text}.
Resumable and slow on purpose (Wikipedia rate limits). Text is CC BY-SA, credited on the Credits page and linked from each species."""
import json,os,sys,time,urllib.request,urllib.parse
here=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(here); OUT=os.path.join(here,'about.json')
sys.path.insert(0,os.path.join(ROOT,'build')); import species
UA={'User-Agent':'ConnectedEarth/1.0 (sachinw_80@yahoo.com)'}
tab=species.table(); got=json.load(open(OUT)) if os.path.exists(OUT) else {}
titles=sorted({r['wiki'] for r in tab.values() if r.get('wiki') and not r.get('cat')} - set(got))
print(len(titles),'to fetch',flush=True)
for i in range(0,len(titles),20):
    b=titles[i:i+20]
    u='https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&exsentences=2&exlimit=20&redirects=1&format=json&titles='+urllib.parse.quote('|'.join(b))
    for t in range(8):
        try:
            d=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read()); break
        except Exception as ex:
            time.sleep(10*(t+1)); d=None
    if d is None: print('gave up at',i); break
    q=d.get('query',{}); redir={}
    for k in ('normalized','redirects'):
        for r in q.get(k,[]): redir[r['from']]=r['to']
    pages={p['title']:p.get('extract','') for p in q.get('pages',{}).values()}
    for x in b:
        y=x
        while y in redir and redir[y]!=y: y=redir[y]
        got[x]=pages.get(y,'')
    json.dump(got,open(OUT,'w'),ensure_ascii=False)
    time.sleep(6)
print('done',len(got))
