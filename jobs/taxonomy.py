#!/usr/bin/env python3
"""taxonomy.py: kingdom, phylum, class, order and family for every species of kind "taxon" (#254), from the GBIF backbone.
Writes two sidecar files, both keyed by species id (sid), by this job only:
  data/species/taxonomy.json         accepted matches {sid: {kingdom, phylum, class, order, family, rank, key, match, conf, gname, src, at}}
  data/species/taxonomy_review.json  doubtful or missing matches {sid: {match, conf, gname, rank, kingdom, why, at}}: the owner looks at these; nothing is guessed
Resumable: a species already in either file is skipped. LIMIT=n does at most n species this run (0 = all left).
Groups and resources get no taxonomy. Nothing here touches the species rows, the built pages or api/."""
import datetime, json, os, sys, time, urllib.error, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'build'))
OUT = os.path.join(ROOT, 'data', 'species', 'taxonomy.json')
REVIEW = os.path.join(ROOT, 'data', 'species', 'taxonomy_review.json')
UA = {'User-Agent': 'ConnectedEarth/1.0 (+https://github.com/sachinwankhede/connected-earth)'}
GAP = 0.15            # seconds between requests: polite, and about 4,950 species take 15 minutes
MIN_CONF = 90         # an exact match below this goes to the review list
HIGHER_OK = ('GENUS', 'FAMILY', 'ORDER', 'CLASS', 'PHYLUM')   # ranks above species that count as a match when the name is the same
RANKS = ('kingdom', 'phylum', 'class', 'order', 'family')

def today(): return datetime.date.today().isoformat()

def hint(row):
    """Consumers (tl 2 and up) are animals, which settles names shared by an animal and a plant; producers (tl 1) can be plants, algae or fungi, so no hint."""
    return 'Animalia' if row.get('tl', 0) >= 2 else None

def classify(row, resp, at=None):
    """(accepted, record): decide from one GBIF match response. Pure, so it is tested without the network."""
    at = at or today()
    mt = (resp or {}).get('matchType', 'NONE'); conf = (resp or {}).get('confidence', 0) or 0
    base = {'match': mt.lower(), 'conf': conf, 'gname': (resp or {}).get('scientificName', ''), 'rank': (resp or {}).get('rank', '')}
    same_name = False
    if mt == 'HIGHERRANK':   # GBIF calls a genus or family name looked up on its own a "higher rank" match; it is right when the answer is that same name (never a bare kingdom)
        same_name = (resp.get('rank') in HIGHER_OK and (resp.get('canonicalName') or '').lower() == (row.get('latin') or '').lower())
    if mt != 'EXACT' and not same_name: return False, dict(base, why='no exact match' if mt == 'NONE' else 'only a %s match' % mt.lower().replace('higherrank', 'higher-rank'), at=at)
    if conf < MIN_CONF: return False, dict(base, why='confidence %s is below %d' % (conf, MIN_CONF), at=at)
    if not resp.get('kingdom'): return False, dict(base, why='no kingdom in the answer', at=at)
    h = hint(row)
    if h and resp['kingdom'] != h: return False, dict(base, kingdom=resp['kingdom'], why='a consumer matched kingdom %s, expected %s' % (resp['kingdom'], h), at=at)
    rec = {k: resp[k] for k in RANKS if resp.get(k)}
    rec.update(rank=resp.get('rank', ''), key=resp.get('usageKey'), match='higher-rank' if same_name else 'exact', conf=conf, gname=resp.get('scientificName', ''), src='gbif', at=at)
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
    todo = sorted(set(rows) - set(got) - set(rev))
    limit = int(os.environ.get('LIMIT', '0') or 0)
    if limit: todo = todo[:limit]
    print(len(todo), 'to match (%d done, %d to review)' % (len(got), len(rev)), flush=True)
    for n, sid in enumerate(todo, 1):
        row = rows[sid]
        ok, rec = classify(row, gbif(row['latin'], hint(row)))
        (got if ok else rev)[sid] = rec
        if n % 50 == 0 or n == len(todo): save(OUT, got); save(REVIEW, rev); print(n, 'of', len(todo), flush=True)
    save(OUT, got); save(REVIEW, rev)
    print('done: %d matched, %d to review' % (len(got), len(rev)))

if __name__ == '__main__': main()
