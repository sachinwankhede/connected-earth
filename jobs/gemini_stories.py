#!/usr/bin/env python3
"""gemini_stories.py: draft the story and the "why it matters" line for places that have research but no story (#196, #747), with the Gemini API.
Usage: gemini_stories.py <research dir> <out dir> [limit] [--again]
  <research dir>  a checkout of the `research` branch (files research/<id>.md: the source text for each place)
  <out dir>       a checkout of the `gemini-stories` branch: one file per place, written the moment its answer is checked, so nothing is lost if the run stops
Places chosen: data/places/<id>.json with no `story` and no `matters`, a research file, no draft yet (a rejected draft is not asked again unless --again).
Free-tier friendly: one request at a time, at least GAP seconds apart; on a 429 it waits as long as Google says (up to MAX_WAIT) and tries again once, and if that fails too
it STOPS cleanly (exit 0) with a message: the drafts written so far stay, and the next run carries on where this one stopped. `limit` places per run (default 15; 0 = every place left; never more than MAX_ROWS). A big run is safe because it is resumable and stops cleanly on a quota stop.
The draft is only a draft: it is written to <out dir>/<id>.json (accepted) or <out dir>/rejected/<id>.json (a check failed, with the reason) and to no place file. The owner reads
the drafts; a later step promotes the approved ones into the place files. Checks: story at most 60 words, why at most 40, every number in the draft appears in the research text, no
capitalised word in the draft that the research text lacks (names are not invented).
The key is read from GEMINI_API_KEY, sent only in a header and never printed or written."""
import sys, os, re, json, time, glob, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, HERE)
import fetch, urllib.request, urllib.error
MODELS = ('gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-3.8-flash')   # free-tier daily limits seen 13 Nov: 500, 500 and 20 requests; each model has its own quota
MODEL = os.environ.get('GEMINI_MODEL') or MODELS[0]   # one model, or several separated by commas: tried in that order, the next one takes over when a model is out of quota or stays busy
URL = 'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'
MAX_ROWS = 150; PAGE = 15; MAX_OUT = 600; GAP = 15; MAX_WAIT = 90; RESEARCH_CHARS = 30000
PROMPT_VERSION = 'stories-2'
STORY_WORDS = 60; WHY_WORDS = 40
SYSTEM = ('You write two short texts about a protected natural place for a children-friendly nature atlas. Use ONLY facts stated in the SOURCE TEXT: no outside knowledge, no guesses. '
          'Every number, name, date and place name you write must appear in the source text. If the source does not support a fact, leave it out. Plain sentences, no marketing words, no lists, no bold. Never write latitude or longitude coordinates; say the region or country instead, and open with what makes the place special.\n'
          '"story": 2 to 3 sentences, at most %d words: where the place is, how big or how old, and what lives or is special there.\n'
          '"matters": 1 to 2 sentences, at most %d words: why the place matters for nature (a species it shelters, a larger ecosystem it belongs to, a connection to other places).\n'
          'Examples of the style (do not copy their facts):\n'
          'story: Gunung Leuser National Park covers 7,927 km² of northern Sumatra, straddling Aceh and North Sumatra. About 40%% of it is steep and over 1,500 m high. With two other parks, it forms the Tropical Rainforest Heritage of Sumatra.\n'
          'matters: It is one of the two remaining habitats of the Sumatran orangutan, which is critically endangered and lives only in northern Sumatra. An orangutan sanctuary operates at Bukit Lawang.\n'
          'Reply as JSON: {"story": "...", "matters": "..."}.') % (STORY_WORDS - 10, WHY_WORDS - 6)   # the prompt asks for fewer words than the checks allow, so a draft that runs long still passes
SCHEMA = {'type': 'OBJECT', 'properties': {'story': {'type': 'STRING'}, 'matters': {'type': 'STRING'}}, 'required': ['story', 'matters']}

class QuotaStop(Exception): pass
class Overloaded(Exception): pass
BUSY_WAITS = (30, 90, 180)   # seconds to wait before each retry of a 503 or timeout
MAX_BUSY_IN_A_ROW = 3        # places in a row that stay busy: stop the run, nothing is lost

def words(s): return len(re.findall(r"\S+", s or ''))
def numbers(s): return set(re.findall(r'\d[\d,.]*\d|\d', s or ''))
def capwords(s):
    """Capitalised words that do not start a sentence."""
    out = set()
    for sent in re.split(r'(?<=[.!?])\s+', s or ''):
        toks = re.findall(r"[A-Za-z][A-Za-z'’\-]*", sent)
        out |= {t for t in toks[1:] if t[0].isupper()}
    return out

def check(draft, source):
    """None when the draft is usable, else the reason."""
    st, wy = draft.get('story', '').strip(), draft.get('matters', '').strip()
    if not st or not wy: return 'story or matters is empty'
    if words(st) > STORY_WORDS: return 'story has %d words (limit %d)' % (words(st), STORY_WORDS)
    if words(wy) > WHY_WORDS: return 'matters has %d words (limit %d)' % (words(wy), WHY_WORDS)
    src_nums = numbers(source); bad = sorted(n for n in numbers(st + ' ' + wy) if n not in src_nums)
    if bad: return 'numbers not in the research text: ' + ', '.join(bad)
    low = source.lower(); miss = sorted(w for w in capwords(st + ' ' + wy) if w.lower() not in low)
    if miss: return 'names not in the research text: ' + ', '.join(miss[:8])
    return None

def todo(research_dir, out_dir, again, data_dir=None):
    """Place ids to draft, in id order."""
    data_dir = data_dir or os.path.join(ROOT, 'data', 'places'); ids = []
    for f in sorted(glob.glob(os.path.join(data_dir, '*.json'))):
        if f.endswith(('order.json', 'links.json')): continue
        e = json.load(open(f)); pid = e['id']
        if e.get('story') or e.get('matters'): continue
        if not os.path.exists(os.path.join(research_dir, 'research', pid + '.md')): continue
        done = os.path.exists(os.path.join(out_dir, pid + '.json'))
        rej = os.path.exists(os.path.join(out_dir, 'rejected', pid + '.json'))
        if done or (rej and not again): continue
        ids.append((pid, e.get('name', pid), e.get('country') or e.get('place') or '', e.get('kind', '')))
    return ids

def ask(name, where, kind, source, key, model=None):
    body = {'systemInstruction': {'parts': [{'text': SYSTEM}]},
            'contents': [{'parts': [{'text': 'PLACE: %s (%s; %s)\n\nSOURCE TEXT:\n%s' % (name, where, kind, source[:RESEARCH_CHARS])}]}],
            'generationConfig': {'temperature': 0.2, 'maxOutputTokens': MAX_OUT, 'responseMimeType': 'application/json', 'responseSchema': SCHEMA}}
    req = urllib.request.Request(URL % (model or MODEL.split(',')[0].strip()), data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'x-goog-api-key': key}, method='POST')
    attempt = busy = 0
    while True:
        try:
            j = json.loads(fetch.urlopen(req, timeout=120).read()); break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = retry_delay(e.read())
                if attempt == 0 and wait <= MAX_WAIT: attempt = 1; time.sleep(wait + 2); continue
                raise QuotaStop('HTTP 429, retry in %ss' % wait)
            if e.code in (500, 503, 504) and busy < len(BUSY_WAITS): time.sleep(BUSY_WAITS[busy]); busy += 1; continue
            if e.code in (500, 503, 504): raise Overloaded('HTTP %d' % e.code)
            return dict(error='HTTP %d' % e.code, detail=e.read()[:200].decode('utf-8', 'replace'))
        except Exception as e:
            if busy < len(BUSY_WAITS): time.sleep(BUSY_WAITS[busy]); busy += 1; continue
            raise Overloaded(type(e).__name__)
    try:
        return dict(draft=json.loads(j['candidates'][0]['content']['parts'][0]['text']), tokens=j.get('usageMetadata', {}))
    except Exception:
        return dict(error='unreadable answer')

def retry_delay(body):
    m = re.search(r'"retryDelay"\s*:\s*"(\d+(?:\.\d+)?)s"', body.decode('utf-8', 'replace') if isinstance(body, bytes) else str(body))
    return int(float(m.group(1))) + 1 if m else 3600

def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True); tmp = path + '.tmp'
    json.dump(obj, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, path)   # written whole, then moved into place

def review(out_dir):
    """REVIEW.md (the index) and REVIEW-01.md, REVIEW-02.md ... with PAGE drafts each, so the owner reads one sitting at a time; REVIEW-rejected.md lists the drafts the checks refused with the reason."""
    for f in glob.glob(os.path.join(out_dir, 'REVIEW*.md')): os.remove(f)
    acc = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(out_dir, '*.json')))]
    rej = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(out_dir, 'rejected', '*.json')))]
    pages = [acc[i:i + PAGE] for i in range(0, len(acc), PAGE)]; names = ['REVIEW-%02d.md' % (k + 1) for k in range(len(pages))]
    def put(name, lines): open(os.path.join(out_dir, name), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    put('REVIEW.md', ['# Story drafts (Gemini, to read and approve)', '', '%d accepted by the checks, %d rejected. Nothing here is in a place file yet. Read one page at a time:' % (len(acc), len(rej)), ''] +
        ['- [%s](%s): %s to %s' % (n, n, pg[0]['name'], pg[-1]['name']) for n, pg in zip(names, pages)] + (['- [REVIEW-rejected.md](REVIEW-rejected.md): %d drafts the checks refused' % len(rej)] if rej else []))
    for n, pg in zip(names, pages):
        out = ['# %s' % n, '']
        for r in pg: out += ['## %s (`%s`)' % (r['name'], r['id']), '', '**Story** (%d words): %s' % (words(r['story']), r['story']), '', '**Why it matters** (%d words): %s' % (words(r['matters']), r['matters']), '']
        put(n, out)
    if rej:
        out = ['# Rejected by the checks', '']
        for r in rej: out += ['## %s (`%s`) - %s' % (r['name'], r['id'], r['rejected']), '', 'Story: %s' % r['story'], '', 'Why: %s' % r['matters'], '']
        put('REVIEW-rejected.md', out)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; again = '--again' in sys.argv
    if len(args) < 2: print(__doc__); sys.exit(2)
    research_dir, out_dir = args[0], args[1]; limit = int(args[2]) if len(args) > 2 else 15
    limit = min(limit or MAX_ROWS, MAX_ROWS)   # 0 = all left, capped
    chain = [m.strip() for m in MODEL.split(',') if m.strip()]
    bad = [m for m in chain if m not in MODELS]
    if not chain or bad: print('model %r is not one of %s' % (', '.join(bad) or MODEL, ', '.join(MODELS))); sys.exit(2)
    key = os.environ.get('GEMINI_API_KEY', '')
    if not key: print('GEMINI_API_KEY is not set'); sys.exit(2)
    todo_ids = todo(research_dir, out_dir, again); print(len(todo_ids), 'places without a draft;', 'drafting', min(limit, len(todo_ids)), flush=True)
    ok = rej = tin = tout = busy_row = idx = 0; last = 0.0; out_of = []
    def next_model(why):
        nonlocal idx, busy_row
        out_of.append(chain[idx]); print('MODEL OUT: %s (%s)%s' % (chain[idx], why, '' if idx + 1 >= len(chain) else '; trying ' + chain[idx + 1]), flush=True)
        idx += 1; busy_row = 0; return idx < len(chain)
    for pid, name, where, kind in todo_ids[:limit]:
        if idx >= len(chain): break
        source = open(os.path.join(research_dir, 'research', pid + '.md'), encoding='utf-8').read()
        r = None
        while idx < len(chain) and r is None:
            wait = last + GAP - time.time()
            if wait > 0: time.sleep(wait)
            try: r = ask(name, where, kind, source, key, chain[idx])
            except QuotaStop as e: next_model('quota used up, %s' % e); last = time.time()
            except Overloaded as e:
                busy_row += 1; print(pid, 'busy on', chain[idx] + ':', e, flush=True); last = time.time()
                if busy_row >= MAX_BUSY_IN_A_ROW: next_model('busy for %d places in a row' % busy_row)
                else: break   # skip this place for now; it is asked again on the next run
        if r is None: continue
        busy_row = 0; last = time.time(); used = chain[idx]
        if 'error' in r: print(pid, 'error:', r['error'], r.get('detail', '')); continue
        t = r['tokens']; tin += t.get('promptTokenCount', 0); tout += t.get('candidatesTokenCount', 0)
        why = check(r['draft'], source)
        rec = dict(id=pid, name=name, story=r['draft'].get('story', '').strip(), matters=r['draft'].get('matters', '').strip(), model=used, prompt=PROMPT_VERSION,
                   tokens=t, at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'))
        if why: rec['rejected'] = why; write(os.path.join(out_dir, 'rejected', pid + '.json'), rec); rej += 1
        else: write(os.path.join(out_dir, pid + '.json'), rec); ok += 1
        print(pid, '->', 'REJECTED: ' + why if why else 'ok (%d + %d words)' % (words(rec['story']), words(rec['matters'])), flush=True)
    if idx >= len(chain): print('STOP: every model is out (%s). Drafts so far are kept; run again later.' % ', '.join(out_of))
    review(out_dir)
    print('accepted', ok, '| rejected', rej, '| prompt tokens', tin, '| output tokens', tout)

if __name__ == '__main__': main()
