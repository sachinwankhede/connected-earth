#!/usr/bin/env python3
"""speciesphotos.py: one thumbnail link per species, so the food webs need no Wikipedia call for photos.
Usage: speciesphotos.py <outfile> [limit]   writes {wiki title: [thumbnail path under https://thumb.wikimedia.org/wikipedia/commons/thumb/, Wikipedia page name]} (resumable).
Titles Wikipedia has no picture for go to <outfile minus .json>_missing.json and are not tried again.
Uses the batched pageimages query (50 titles per request), so about 115 requests cover all species. Links only; no image files are stored."""
import sys, os, json, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import wm
from photo_registry import ALLOWED_IMAGE_HOSTS, cache_active, negative_entry, safe_https
NOTPHOTO = __import__('re').compile(r'logo|emblem|coat[_ ]of[_ ]arms|(^|[_ ])flag([_ .]|$)|\.svg|map\.(png|jpe?g|gif)$|(^|[_ -])maps?([_ .0-9-]|$)|locator|diagram|[_ -]chart', 2)
def main():
    out = sys.argv[1]; limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    man = json.load(open(out)) if os.path.exists(out) else {}
    ms = out[:-5] + '_missing.json'; miss = json.load(open(ms)) if os.path.exists(ms) else {}
    sp = json.load(open('data/species.json'))
    todo = sorted({v['wiki'] for v in sp.values() if v.get('wiki')} - set(man) - {t for t, entry in miss.items() if cache_active(entry)})
    if limit: todo = todo[:limit]
    print(len(todo), 'titles to try', flush=True)
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        q = 'https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&piprop=thumbnail&pithumbsize=330&redirects=1&format=json&titles=' + urllib.parse.quote('|'.join(batch))
        j = wm.get(q)
        if not j: print('batch failed', i, flush=True); continue
        qq = j.get('query', {}); back = {}
        for k in ('normalized', 'redirects'):
            for r in qq.get(k, []): back.setdefault(r['to'], []).append(r['from'])
        hit = {}
        for p in qq.get('pages', {}).values():
            names = [p.get('title')]; 
            for _ in range(2): names += [f for n in list(names) for f in back.get(n, [])]
            th = p.get('thumbnail')
            src = th['source'].split('?')[0] if th else ''
            for n in set(names):
                if th and not safe_https(src, ALLOWED_IMAGE_HOSTS):
                    continue
                if th and not NOTPHOTO.search(urllib.parse.unquote(src.split('/')[-2] if '/thumb/' in src else src)):
                    image = src.replace('https://thumb.wikimedia.org/wikipedia/commons/thumb/', '')
                    hit[n] = (image, urllib.parse.quote(p['title'].replace(' ', '_')))
                else:
                    hit[n] = None
        for t in batch:
            h = hit.get(t)
            if h:
                man[t] = list(h)
                miss.pop(t, None)
            elif t in hit or t in {x for v in back.values() for x in v}:
                old = miss.get(t); attempts = (old.get('attempts', 0) if isinstance(old, dict) else 0) + 1
                miss[t] = negative_entry('nophoto', attempts)
        json.dump(man, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
        json.dump(miss, open(ms, 'w'), ensure_ascii=False, separators=(',', ':'))
        print(i + len(batch), 'of', len(todo), '| photos', len(man), '| none', len(miss), flush=True)
main()
