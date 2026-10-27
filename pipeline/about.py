#!/usr/bin/env python3
"""about.py: fetch the first sentences of each species' Wikipedia page into pipeline/about.json {wiki title: text}.
Resumable. Uses the polite Wikimedia client in wm.py. Text is CC BY-SA: credited on the Credits page and linked from each species.
After it finishes: python3 build/species.py about && python3 build/build.py --all"""
import json,os,sys,urllib.parse
here=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(here); OUT=os.path.join(here,'about.json')
sys.path.insert(0,os.path.join(ROOT,'build')); sys.path.insert(0,here)
import species, wm
tab=species.table(); got=json.load(open(OUT)) if os.path.exists(OUT) else {}
titles=sorted({r['wiki'] for r in tab.values() if r.get('wiki') and not r.get('cat')} - set(got))
print(len(titles),'to fetch',flush=True)
for n,i in enumerate(range(0,len(titles),20)):
    b=titles[i:i+20]
    d=wm.get('https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&exsentences=2&exlimit=20&redirects=1&format=json&titles='+urllib.parse.quote('|'.join(b)))
    q=(d or {}).get('query',{}); redir={}
    for k in ('normalized','redirects'):
        for r in q.get(k,[]): redir[r['from']]=r['to']
    pages={p['title']:p.get('extract','') for p in q.get('pages',{}).values()}
    for x in b:
        y=x
        while y in redir and redir[y]!=y: y=redir[y]
        got[x]=pages.get(y,'')
    json.dump(got,open(OUT,'w'),ensure_ascii=False)
    if n%10==0: print(len(got),'of',len(got)+len(titles)-i-len(b),flush=True)
print('done',len(got))
