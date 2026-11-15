#!/usr/bin/env python3
"""photos.py: store each place's photo in the repo with its author and licence.
Usage: photos.py <outdir> <data-dir> [<data-dir>...]   writes <outdir>/<id>.jpg and <outdir>/places.json (resumable)
Source: Wikipedia page summary (thumbnail, 330px wide) + file metadata from the English Wikipedia API (Commons files)."""
import sys,os,re,json,glob,time,html,urllib.request,urllib.parse,datetime
sys.path.insert(0,os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'lib'))
import wm, licences
from wikipedia_photo import UA, get, strip, NOTPHOTO, PARK_WORD, titles, right_page, one, fetch   # the rules live in lib/wikipedia_photo.py (moved unchanged)
from photo_registry import ALLOWED_IMAGE_HOSTS, cache_active, failure_class, negative_entry, safe_https
def prune_large(out,man):
    """Drop every larger copy (photos/places-lg/, listed in photos/places_large.json) whose small picture is no longer stored under the same name.
    The job that removes or replaces a place picture owns its larger copy too (ground rule 10, #727): the list and the files must agree, so a removed picture
    cannot leave a copy behind that the data check then fails on. Idempotent; the copy is made again by data-placepictures if the picture comes back."""
    base=os.path.dirname(os.path.normpath(out)); lp=os.path.join(base,'places_large.json'); ld=os.path.join(base,'places-lg')
    if not os.path.exists(lp): return []
    large=json.load(open(lp)); gone=[t for t,n in large.items() if t not in man or os.path.splitext(man[t].get('f',''))[0]+'.webp'!=n]
    for t in gone:
        try: os.remove(os.path.join(ld,large[t]))
        except OSError: pass
        del large[t]; print('removed larger copy of',t,flush=True)
    if gone:
        tmp=lp+'.tmp'; json.dump(large,open(tmp,'w'),indent=0,sort_keys=True); os.replace(tmp,lp)
    return gone
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
            if not t or t in man or (t in miss and cache_active(miss[t])): continue
            if LIMIT and tried>=LIMIT: continue
            tried+=1
            pl=(e.get('place') or '')
            try: r=one(e['id'],t,out,man,pl.split(',')[0].strip() if pl.endswith(', USA') else '')
            except Exception as ex: r='err '+str(ex)[:50]
            stat[t]=r
            if failure_class(r) == 'permanent':
                old=miss.get(t); attempts=(old.get('attempts',0) if isinstance(old,dict) else 0)+1
                miss[t]=negative_entry(r,attempts); json.dump(miss,open(ms,'w'),ensure_ascii=False,indent=0)
            elif r == 'ok':
                miss.pop(t,None); json.dump(miss,open(ms,'w'),ensure_ascii=False,indent=0)
            json.dump(man,open(mp,'w'),ensure_ascii=False,indent=0)
            if r!='ok': print(t,r,flush=True)
    print('done',len(man),'photos;',len(miss),'places with no usable photo; tried',tried,'this run; problems:',sum(1 for r in stat.values() if r not in ('ok','nophoto','notcommons','notphoto')))
    prune_large(out,man)   # after every change above, so the larger copies follow the pictures
    open(os.path.join(out,'.tried'),'w').write(str(tried))
