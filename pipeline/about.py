#!/usr/bin/env python3
"""about.py: fetch the first sentences of each species' Wikipedia page into pipeline/about.json {wiki title: text}.
Resumable. Uses the polite Wikimedia client in wm.py. Text is CC BY-SA: credited on the Credits page and linked from each species.
After it finishes: python3 build/species.py about && python3 build/build.py --all
It also fetches a one-sentence summary for each state park or refuge without a story (pipeline/summaries.json {wiki title: sentence}); build.py shows it on the place page."""
import json,os,sys,urllib.parse
here=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(here); OUT=os.path.join(here,'about.json'); SUMS=os.path.join(here,'summaries.json')
sys.path.insert(0,os.path.join(ROOT,'build')); sys.path.insert(0,here)
import species, wm
tab=species.table(); got=json.load(open(OUT)) if os.path.exists(OUT) else {}
titles=sorted({r['wiki'] for r in tab.values() if r.get('wiki') and not r.get('cat')} - set(got))
LIMIT=int(os.environ.get('LIMIT','0') or 0)   # a scheduled run does one batch; 0 = everything left
if LIMIT: titles=titles[:LIMIT]
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

# ---- one-sentence summaries for parks and refuges that have no story (the place page shows them; see docs/DESIGN.md "Place summary")
import glob, re
MAXW=40
def place_titles():
    out=set()
    for f in glob.glob(os.path.join(ROOT,'data','*.json'))+glob.glob(os.path.join(ROOT,'data-auto','*.json')):
        if f.endswith(('order.json','links.json','species.json','bounds.json')): continue
        try: e=json.load(open(f))
        except Exception: continue
        if not isinstance(e,dict) or not e.get('park') or e.get('story'): continue
        for src in e.get('sources',[]):
            m=re.search(r'wikipedia\.org/wiki/([^#?]+)',src.get('url','')) if src.get('title','').startswith('Wikipedia:') else None
            if m: out.add(urllib.parse.unquote(m.group(1)).replace('_',' ')); break
    return out
def clean(t):
    t=t or ''
    while re.search(r'\([^()]*\)',t): t=re.sub(r'\s*\([^()]*\)','',t)     # pronunciations, conversions, dates
    t=re.sub(r'\s+',' ',t).strip()
    return '' if (not t or species.NOT_ABOUT.search(t) or len(t.split())>MAXW or len(t)<30) else t
sums=json.load(open(SUMS)) if os.path.exists(SUMS) else {}
todo=sorted(place_titles()-set(sums))
if LIMIT: todo=todo[:LIMIT]
print(len(todo),'place summaries to fetch',flush=True)
for i in range(0,len(todo),20):
    b=todo[i:i+20]
    d=wm.get('https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&exsentences=1&exlimit=20&redirects=1&format=json&titles='+urllib.parse.quote('|'.join(b)))
    q=(d or {}).get('query',{}); redir={}
    for k in ('normalized','redirects'):
        for r in q.get(k,[]): redir[r['from']]=r['to']
    pages={p['title']:p.get('extract','') for p in q.get('pages',{}).values()}
    for x in b:
        y=x
        while y in redir and redir[y]!=y: y=redir[y]
        sums[x]=clean(pages.get(y,''))
    json.dump(sums,open(SUMS,'w'),ensure_ascii=False,indent=0)
print('summaries done',len(sums),'with text',sum(1 for v in sums.values() if v))
