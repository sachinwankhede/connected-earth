#!/usr/bin/env python3
"""journeyresearch.py [latin name ...]: source material for writing real journeys (docs/JOURNEYS.md, "Finding more journeys").

The candidate ranking only says a species lives in two far-apart places; that is not a route (a robin in Maine and one in California
are not one journey). For each species this saves what Wikipedia says about where it breeds, winters and migrates, plus every place in the
app that has the species with its country and coordinates, so the two ends can be chosen where the text supports them.
Output: research/journey-research.md. With no names it uses SHORTLIST. Needs the web, so it runs in the data-journeyresearch job.
JOURNEYS_OFFLINE=1 skips the web (layout test)."""
import datetime, os, re, sys, urllib.parse
here = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(here)
sys.path.insert(0, here); import journeys as J
OFFLINE = bool(os.environ.get('JOURNEYS_OFFLINE')); TODAY = datetime.date.today().isoformat()
SHORTLIST = ['Limosa lapponica', 'Grus grus', 'Danaus plexippus', 'Pelecanus onocrotalus', 'Circus aeruginosus', 'Neophron percnopterus',
             'Milvus migrans', 'Haliaeetus leucocephalus', 'Anser caerulescens', 'Anas platyrhynchos', 'Branta canadensis', 'Turdus migratorius',
             'Falco sparverius', 'Melospiza melodia', 'Zonotrichia leucophrys', 'Setophaga coronata', 'Haliaeetus albicilla', 'Schistocerca gregaria',
             'Vulpes lagopus', 'Sturnus vulgaris', 'Agelaius phoeniceus', 'Zenaida macroura', 'Junco hyemalis', 'Buteo buteo', 'Colaptes auratus']
WANT = re.compile(r'migrat|distribution|range|habitat|winter|breeding|behavio|ecology|movement', re.I)
SEC = 3000; TOTAL = 9000

def article(title):
    import wm
    d = wm.get('https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1&prop=extracts|categories&explaintext=1&exlimit=1&cllimit=max&clshow=!hidden&titles=' + urllib.parse.quote(title))
    p = next(iter(((d or {}).get('query', {}).get('pages', {})).values()), {})
    return p.get('title', title), p.get('extract') or '', [c['title'] for c in p.get('categories', []) if re.search(r'migrat', c['title'], re.I)]

def sections(text):
    parts = re.split(r'\n(={2,})\s*(.+?)\s*\1\n', text)       # [lead, eq, heading, body, eq, heading, body ...]
    out = [('Lead', parts[0].strip()[:900])]; used = len(out[0][1])
    for i in range(1, len(parts) - 2, 3):
        head, body = parts[i + 1], re.sub(r'\n+', '\n', parts[i + 2]).strip()
        if body and WANT.search(head) and used < TOTAL:
            out.append((head, body[:SEC])); used += min(len(body), SEC)
    return out

def main(names):
    tab, places, links = J.load(); occ = J.occurrences(tab, places); cov = J.covered(places, links)
    pl = {e['id']: e for e in places}; byl = {}
    for k, r in tab.items():
        if r.get('latin'): byl.setdefault(r['latin'].lower(), []).append(k)
    out = ['# Journey research', '', 'Retrieved %s. Wikipedia text is CC BY-SA; each section names its article. Nothing here is verified beyond what the source says.' % TODAY, '',
           'Use: pick the two ends only where the text says the species travels between those regions. Skip a species when no pair of places fits.', '']
    for lat in names:
        keys = byl.get(lat.lower(), []); sp = keys[0] if keys else None
        r = tab.get(sp, {}) if sp else {}
        out += ['## %s (%s)' % (r.get('name', lat), lat), '']
        if not sp or sp not in occ: out += ['Not found in the app (or only one place).', '']; continue
        out += ['Existing journey: ' + (cov.get(sp) or 'none'), '', '### Places in the app with this species (%d)' % len(occ[sp]), '', '| id | place | country | lat | lon | node |', '|---|---|---|---|---|---|']
        for pid, (nm, la, lo) in sorted(occ[sp].items(), key=lambda x: (pl[x[0]].get('country', ''), x[1][0])):
            e = pl[pid]; node = next((n['id'] for n in e['nodes'] if n.get('sp') == sp), '')
            out.append('| %s | %s | %s | %.1f | %.1f | %s |' % (pid, nm, e.get('country', ''), la, lo, node))
        out.append('')
        if OFFLINE or not r.get('wiki'): out += ['(Wikipedia not read)', '']; continue
        title, text, cats = article(r['wiki'])
        out += ['### Wikipedia: %s' % title, 'Source: <https://en.wikipedia.org/wiki/%s>' % urllib.parse.quote(title.replace(' ', '_')), 'Migration categories: ' + (', '.join(cats) or 'none'), '']
        for head, body in sections(text): out += ['**%s**' % head, body, '']
    os.makedirs(os.path.join(ROOT, 'research'), exist_ok=True)
    open(os.path.join(ROOT, 'research', 'journey-research.md'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out[:40]))

if __name__ == '__main__':
    main(sys.argv[1:] or SHORTLIST)
