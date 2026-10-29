#!/usr/bin/env python3
"""research.py <place id>: gather the source material for one place into research/<id>.md (for writing and checking its story and links).
Version 1 contents: Wikipedia text of the place's article(s), the place's own data (species, current story), and what GloBI records
say about each feeding link. Every item names its source and the date it was retrieved. Capped at about 40 KB.
Run by the data-research workflow (open internet); set RESEARCH_OFFLINE=1 to skip the web calls when testing the layout."""
import datetime, json, os, re, sys, urllib.parse
here = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(here)
sys.path.insert(0, here); import wm
CAP = 40_000; WIKI_CHARS = 9_000; MAX_LINKS = 60
OFFLINE = bool(os.environ.get('RESEARCH_OFFLINE'))
TODAY = datetime.date.today().isoformat()

def load(pid):
    for d in ('data', 'data-auto'):
        p = os.path.join(ROOT, d, pid + '.json')
        if os.path.exists(p): return json.load(open(p))
    sys.exit('no such place: ' + pid)

def wiki_titles(e):
    t = []
    for s in (e.get('sources') or []):
        m = re.search(r'wikipedia\.org/wiki/([^#?]+)', s.get('url', ''))
        if m: t.append(urllib.parse.unquote(m.group(1)).replace('_', ' '))
    if e.get('imgwiki'): t.append(e['imgwiki'])
    seen = []; [seen.append(x) for x in t if x not in seen]; return seen

def wiki_text(title):
    if OFFLINE: return None, None
    d = wm.get('https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1&redirects=1&format=json&titles=' + urllib.parse.quote(title))
    pages = list(((d or {}).get('query') or {}).get('pages', {}).values())
    if not pages or not pages[0].get('extract'): return None, None
    txt = pages[0]['extract']
    txt = re.split(r'\n== (?:See also|References|External links|Further reading|Notes|Bibliography) ==', txt)[0]
    txt = re.sub(r'\n{3,}', '\n\n', txt).strip()
    return pages[0]['title'], txt[:WIKI_CHARS] + ('\n[...trimmed]' if len(txt) > WIKI_CHARS else '')

def globi(eater, food):
    if OFFLINE: return None
    u = 'https://api.globalbioticinteractions.org/interaction?sourceTaxon=%s&targetTaxon=%s&interactionType=eats&type=json.v2&limit=5' % (urllib.parse.quote(eater), urllib.parse.quote(food))
    d = wm.get(u)
    return d if isinstance(d, list) else None

def main(pid):
    e = load(pid); nodes = {n['id']: n for n in e['nodes']}; ev = e.get('ev') or {}
    name = lambda i: (nodes.get(i) or {}).get('name') or i
    out = ['# Research file: %s (%s)\n' % (e['name'], pid), 'Retrieved %s. Each section names its source. Nothing here is verified beyond what the source says.\n' % TODAY]
    out += ['## 1. Where the place is', '%s. Coordinates %s, %s. Kind: %s.\n' % (e.get('place'), e.get('lat'), e.get('lon'), e.get('kind'))]
    out += ['## 2. What the app says today', '**Story:** %s\n' % (e.get('story') or '(none)'), '**Why it matters:** %s\n' % (e.get('matters') or '(none)'), '**Current notes on sources:** %s\n' % (e.get('notes') or '(none)'),
            '**Current sources:** ' + '; '.join('%s <%s>' % (s.get('title'), s.get('url')) for s in (e.get('sources') or [])) + '\n']
    sp = [n for n in e['nodes'] if not n.get('cat')]
    out += ['## 3. Species in the app (%d)' % len(sp), ', '.join('%s (%s)' % (n.get('name') or n['id'], n.get('sp') or '') for n in sp) + '\n']
    out += ['## 4. Wikipedia text']
    for t in wiki_titles(e)[:2]:
        title, txt = wiki_text(t)
        out += ['### %s' % (title or t), 'Source: <https://en.wikipedia.org/wiki/%s> (CC BY-SA), retrieved %s.\n' % (urllib.parse.quote((title or t).replace(' ', '_')), TODAY), txt or '(not retrieved)', '']
    out += ['## 5. Feeding links and what GloBI records say']
    rows = []; gaps = []; n = 0
    eats = [(r[0], r[1]) for r in e['raw'] if len(r) == 2 or r[2] == 's']
    for s, t in eats:
        x = ev.get(s + '>' + t)
        label = '%s -> %s' % (name(s), name(t))
        if not x: gaps.append(label + ' (no evidence entry)'); continue
        code, eater, food = x[0], x[1] if len(x) > 1 else None, x[2] if len(x) > 2 else None
        if code == 'a' or not eater: gaps.append(label + ' (no GloBI record found; from general ecology)'); continue
        if n >= MAX_LINKS: gaps.append(label + ' (not queried this run)'); continue
        n += 1; res = globi(eater, food)
        if res is None: rows.append('| %s | %s | %s -> %s | not queried |' % (label, code, eater, food)); continue
        seen = []
        for r in res:
            line = '%s %s %s' % (r.get('source_taxon_name') or eater, r.get('interaction_type') or 'eats', r.get('target_taxon_name') or food)
            if line not in seen: seen.append(line)
        rows.append('| %s | %s | %s -> %s | %d%s record(s): %s |' % (label, code, eater, food, len(res), '+' if len(res) >= 5 else '', '; '.join(seen[:3]).replace('|', '/')))
    out += ['Source: GloBI <https://www.globalbioticinteractions.org>, retrieved %s. Codes: g = recorded for these species, gg = genus, gf = family, ga = added from a record.\n' % TODAY, '| Link | Code | Query | Records found |', '|---|---|---|---|'] + rows + ['']
    out += ['### Links with no GloBI record (be careful with these)', '\n'.join('- ' + g for g in gaps) or '(none)', '']
    txt = '\n'.join(out)
    if len(txt) > CAP: txt = txt[:CAP] + '\n[...file capped]'
    os.makedirs(os.path.join(ROOT, 'research'), exist_ok=True)
    p = os.path.join(ROOT, 'research', pid + '.md'); open(p, 'w').write(txt + '\n'); print('wrote', p, len(txt), 'bytes')

if __name__ == '__main__': main(sys.argv[1])
