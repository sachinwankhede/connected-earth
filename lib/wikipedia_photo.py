"""wikipedia_photo.py: a place's picture from its Wikipedia page summary (the rules of jobs/photos.py; #887). MOVED unchanged from jobs/photos.py, which imports them back and keeps its own job
(prune_large and main), so lib/place_sources.py does not reach into jobs/. Network through lib/wm.py; the licence rule is lib/licences.py (#421)."""
import sys,os,re,json,glob,time,html,urllib.request,urllib.parse,datetime
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import wm, licences
from photo_registry import ALLOWED_IMAGE_HOSTS, cache_active, failure_class, negative_entry, safe_https
UA={'User-Agent':'ConnectedEarth/1.0 (https://connected-earth-5ps.pages.dev/; data job)'}   # the live site is the contact (Wikimedia accepts a URL)
def get(u,raw=False): return wm.get(u,raw)
def strip(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>','',s or ''))).strip()
# Files that are logos, seals, flags or drawings are not photos of the place
NOTPHOTO=re.compile(r'logo|arrowhead|emblem|coat[_ ]of[_ ]arms|seal[_ ]of|(^|[_ ])flag([_ .]|$)|\.svg|map\.(png|jpe?g|gif)$|(^|[_ -])maps?([_ .0-9-]|$)|topograph|locator|diagram|[_ -]chart|waterfowl_counts|(^|[/:])White[_ ]River[_ ]National[_ ]Wildlife[_ ]Refuge\.jpg$',re.I)
# A part of a combined name ("Flathead Lake/Big Arm State Park") is tried on its own only when it names a park by itself (a bare "Okmulgee" is a town, so a picture of it would be wrong)
PARK_WORD=re.compile(r'(Park|Preserve|Refuge|Seashore|Lakeshore|Forest|Monument|Recreation Area|Wildlife Area|Reserve)$')
def titles(title):
    """The Wikipedia titles to try for a place, in order: its own name, then each part of a name joined with a slash that ends in a park word."""
    out=[title]
    for p in (x.strip() for x in title.split('/')) if '/' in title else []:
        if p and PARK_WORD.search(p) and p not in out: out.append(p)
    return out
def right_page(j,where):
    """None when the Wikipedia page summary j can be this place, else 'wrongpage' (#767): a disambiguation page never is, and for a US place (where: its state name) the page must name the state in its title, description or first paragraph, so
    a page about Trout Pond in West Virginia is not taken for Trout Pond in Maine. where empty: no state check."""
    if (j or {}).get('type')=='disambiguation': return 'wrongpage'
    if where and where.lower() not in ' '.join(str((j or {}).get(k) or '') for k in ('title','description','extract')).lower(): return 'wrongpage'
    return None
def one(i,title,out,man,where=''):
    """Stores the first free photo found under any of titles(title); the manifest key stays the place's own imgwiki. A transient problem on any title wins over a permanent no-photo, so the place is tried again."""
    res=[]
    for t in titles(title):
        res.append(fetch(i,t,out,man,title,where))
        if res[-1]=='ok': return 'ok'
    return next((r for r in res if failure_class(r)!='permanent'),res[0])
def fetch(i,title,out,man,key,where=''):
    j=get('https://en.wikipedia.org/api/rest_v1/page/summary/'+urllib.parse.quote(title.replace(' ','_'),safe=''))
    th=(j or {}).get('thumbnail')
    if not th: return 'nophoto'
    if right_page(j,where): return 'wrongpage'
    if not safe_https(th.get('source'), ALLOWED_IMAGE_HOSTS): return 'source-rejected'
    m=re.search(r'/commons/thumb/\w/\w\w/([^/]+)/',th['source'])
    if not m: return 'notcommons'
    fn=urllib.parse.unquote(m.group(1)); path=os.path.join(out,i+'.jpg')
    if NOTPHOTO.search(fn): return 'notphoto'
    made=not os.path.exists(path)
    if made:
        b=get(th['source'],raw=True)
        if not b: return 'nodl'
        open(path,'wb').write(b)
    q=get('https://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata&format=json&titles='+urllib.parse.quote('File:'+fn))
    md=(list((q or {}).get('query',{}).get('pages',{}).values()) or [{}])[0].get('imageinfo',[{}])[0].get('extmetadata',{})
    v=lambda k: strip((md.get(k) or {}).get('value'))
    lic=v('LicenseShortName')
    if not licences.ok('Wikimedia',lic):   # the picture licence rule (#421): CC0, CC BY, CC BY-SA, public domain; anything else, or no licence given, is not kept
        if made: os.remove(path)
        return 'notfree'
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    man[key]=dict(f=i+'.jpg',a=v('Artist') or v('Credit') or 'Unknown author',l=v('LicenseShortName') or 'See file page',lu=v('LicenseUrl'),p='https://commons.wikimedia.org/wiki/File:'+urllib.parse.quote(fn.replace(' ','_')),w='https://en.wikipedia.org/wiki/'+urllib.parse.quote(j.get('title',title).replace(' ','_')),checkedAt=now,fetchedAt=now)
    return 'ok'
