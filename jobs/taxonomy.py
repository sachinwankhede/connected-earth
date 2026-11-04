#!/usr/bin/env python3
"""taxonomy.py: kingdom, phylum, class, order and family for every species of kind "taxon" (#254), from the GBIF backbone.
Writes two sidecar files, both keyed by species id (sid), by this job only:
  data/species/taxonomy.json         accepted matches {sid: {kingdom, phylum, class, order, family, rank, key, match, conf, gname, src, at}}
  data/species/taxonomy_review.json  doubtful or missing matches {sid: {match, conf, gname, rank, kingdom, why, at}}: the owner looks at these; nothing is guessed
Resumable: a species already in either file is skipped. LIMIT=n does at most n species this run (0 = all left).
RETRY_REVIEW=1 looks at the whole review list again; REDO=sid,sid looks at those species again (accepted or not).
Groups and resources get no taxonomy. Nothing here touches the species rows, the built pages or api/."""
import datetime, json, os, sys, time, urllib.error, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'build'))
OUT = os.path.join(ROOT, 'data', 'species', 'taxonomy.json')
REVIEW = os.path.join(ROOT, 'data', 'species', 'taxonomy_review.json')
UA = {'User-Agent': 'ConnectedEarth/1.0 (+https://github.com/sachinwankhede/connected-earth)'}
GAP = 0.15            # seconds between requests: polite, and about 4,950 species take 15 minutes
FUZZY_CONF = 95       # a spelling variant needs this much confidence, plus the same genus and at most two letters of difference
MIN_CONF = 90         # an exact match below this goes to the review list
HIGHER_OK = ('GENUS', 'FAMILY', 'ORDER', 'CLASS', 'PHYLUM')   # ranks above species that count as a match when the name is the same
RANKS = ('kingdom', 'phylum', 'class', 'order', 'family')

def today(): return datetime.date.today().isoformat()

def edits(a, b):
    """Number of single-letter changes between two strings (Levenshtein)."""
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]

def lookup(row):
    """Ask GBIF. A name that belongs to several kingdoms comes back as NONE ("Multiple equal matches", e.g. Ficus or Salix alba); for a producer, ask again once per likely kingdom and keep the first real answer."""
    resp = gbif(row['latin'], hint(row))
    if resp.get('matchType') == 'NONE' and 'Multiple equal matches' in (resp.get('note') or '') and row.get('tl') == 1:
        for k in ('Plantae', 'Chromista', 'Fungi', 'Bacteria'):
            r = gbif(row['latin'], k)
            if r.get('matchType') in ('EXACT', 'HIGHERRANK') and r.get('rank') != 'KINGDOM': return r
    return resp

def hint(row):
    """Consumers (tl 2 and up) are animals, which settles names shared by an animal and a plant; producers (tl 1) can be plants, algae or fungi, so no hint."""
    return 'Animalia' if row.get('tl', 0) >= 2 else None

def classify(row, resp, at=None):
    """(accepted, record): decide from one GBIF match response. Pure, so it is tested without the network."""
    at = at or today()
    mt = (resp or {}).get('matchType', 'NONE'); conf = (resp or {}).get('confidence', 0) or 0
    base = {'match': mt.lower(), 'conf': conf, 'gname': (resp or {}).get('scientificName', ''), 'rank': (resp or {}).get('rank', '')}
    latin = (row.get('latin') or '').lower(); canon = (resp or {}).get('canonicalName', '') or ''; canon = canon.lower()
    kind = 'exact'
    if mt == 'HIGHERRANK' and resp.get('rank') in HIGHER_OK + ('SPECIES',) and canon and (latin == canon or latin.startswith(canon + ' ')):
        kind = 'higher-rank'   # GBIF calls a genus or species name that is the start of ours (a subspecies, "Opuntia species") a "higher rank" match: its kingdom to family are the same as ours; never a bare kingdom
    elif mt == 'FUZZY' and conf >= FUZZY_CONF and canon and canon.split()[0] == latin.split()[0] and edits(canon, latin) <= 2:
        kind = 'fuzzy'         # a spelling variant (rueppelli / rueppellii), same genus, at most two letters apart
    elif mt != 'EXACT': return False, dict(base, why='no exact match' if mt == 'NONE' else 'only a %s match' % mt.lower().replace('higherrank', 'higher-rank'), at=at)
    if conf < MIN_CONF: return False, dict(base, why='confidence %s is below %d' % (conf, MIN_CONF), at=at)
    if not resp.get('kingdom'): return False, dict(base, why='no kingdom in the answer', at=at)
    h = hint(row)
    if row.get('tl') == 1 and resp['kingdom'] == 'Animalia': return False, dict(base, kingdom='Animalia', why='a producer matched an animal (kingdom Animalia)', at=at)   # e.g. the growth form "Liana" matched an insect genus of that name
    if h and resp['kingdom'] != h: return False, dict(base, kingdom=resp['kingdom'], why='a consumer matched kingdom %s, expected %s' % (resp['kingdom'], h), at=at)
    rec = {k: resp[k] for k in RANKS if resp.get(k)}
    rec.update(rank=resp.get('rank', ''), key=resp.get('usageKey'), match=kind, conf=conf, gname=resp.get('scientificName', ''), src='gbif', at=at)
    return True, rec

def gbif(name, kingdom=None, tries=4):
    q = {'name': name, 'strict': 'false'}
    if kingdom: q['kingdom'] = kingdom
    url = 'https://api.gbif.org/v1/species/match?' + urllib.parse.urlencode(q)
    for n in range(tries):
        time.sleep(GAP)
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(20 * (n + 1)); continue
            if e.code >= 500: time.sleep(5 * (n + 1)); continue
            raise
        except Exception: time.sleep(5 * (n + 1))
    raise RuntimeError('GBIF did not answer for %r' % name)

def save(path, d):
    t = path + '.tmp'
    json.dump(d, open(t, 'w'), ensure_ascii=False, indent=0, sort_keys=True); os.replace(t, path)

def main():
    import species
    rows = {r['sid']: r for r in species.table().values() if r.get('sk') == 'taxon'}
    got = json.load(open(OUT)) if os.path.exists(OUT) else {}
    rev = json.load(open(REVIEW)) if os.path.exists(REVIEW) else {}
    if os.environ.get('RETRY_REVIEW') == '1': rev = {}   # look at the doubtful ones again (after a rule change)
    redo = {x.strip().lower() for x in os.environ.get('REDO', '').split(',') if x.strip()}   # species ids to look at again, whether accepted or in review
    for sid in redo & (set(got) | set(rev)): got.pop(sid, None); rev.pop(sid, None)
    todo = sorted(set(rows) - set(got) - set(rev))
    limit = int(os.environ.get('LIMIT', '0') or 0)
    if limit: todo = todo[:limit]
    print(len(todo), 'to match (%d done, %d to review)' % (len(got), len(rev)), flush=True)
    for n, sid in enumerate(todo, 1):
        row = rows[sid]
        ok, rec = classify(row, lookup(row))
        (got if ok else rev)[sid] = rec
        if n % 50 == 0 or n == len(todo): save(OUT, got); save(REVIEW, rev); print(n, 'of', len(todo), flush=True)
    save(OUT, got); save(REVIEW, rev)
    print('done: %d matched, %d to review' % (len(got), len(rev)))

if __name__ == '__main__': main()
