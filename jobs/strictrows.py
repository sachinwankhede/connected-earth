#!/usr/bin/env python3
"""strictrows.py (#1061, owner 23 Nov: "delete all bad/conflicting data... no data is better than bad data"): remove species rows whose page is not about exactly that thing,
with everything that depends on them, in batches. Reads data/audit/identity.json (jobs/identity.py); no network.
  python3 jobs/strictrows.py --batch nopage [--dry]     # rows whose page has no Wikidata item (missing, disambiguation, section redirect, no page)
Removing a row removes: its row file; the nodes of every place that name it (and the edge records `raw`/`ev` that name those nodes); its diet file and its entries in other diet files;
its taxonomy, conservation and picture entries (through lib/species_photos.py). A row whose node is the end of a journey is KEPT and listed (a journey is not edited here).
It writes data/audit/strictrows.json = {asOf, removed:{sid:[batch, reason]}, kept:{sid:reason}} so the status page and the validator know what was removed and why. It never touches a row it was not asked for."""
import datetime, glob, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in ('build', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import species
SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')

def batch_nopage(ident):
    return {s: 'page has no Wikidata item' for s, v in ident['rows'].items() if not v[0]}

def batch_shared(ident, root=ROOT):
    """Rows that share a page (Wikidata item) with another row, and are not the one that page is about. Per item: if the item names a taxon, the row whose Latin name is that taxon stays (none stays when no row is that taxon);
    otherwise the row with the most nodes stays (ties: the first id). Every other row goes. Synonyms are removed, not merged: no data is better than bad data (owner, 23 Nov)."""
    import collections
    tab = {r['sid']: r for r in species.table(root).values() if r.get('sid')}; use = collections.Counter()
    for f in place_files(root):
        try: e = json.load(open(f, encoding='utf-8'))
        except ValueError: continue
        for n in (e.get('nodes') or []) if isinstance(e, dict) else []:
            if n.get('sp'): use[n['sp']] += 1
    cl = collections.defaultdict(list)
    for s, v in ident['rows'].items():
        if v[0] and s in tab: cl[v[0]].append(s)
    out = {}
    for q, m in cl.items():
        if len(m) < 2: continue
        tax = (ident['rows'][m[0]][2] or '').lower()
        if tax:
            keep = [s for s in m if (tab[s].get('latin') or '').lower() == tax]
            k = keep[0] if keep else None; why = 'shares its page with another row; the page is about %s' % ident['rows'][m[0]][2]
        else:
            k = max(sorted(m), key=lambda s: use[s]); why = 'shares its page with another row, which has more nodes'
        for s in m:
            if s != k: out[s] = why
    return out

def batch_all(ident, root=ROOT):
    out = batch_shared(ident, root); out.update(batch_nopage(ident)); return out
BATCHES = {'nopage': batch_nopage, 'shared': batch_shared, 'all': batch_all}

def dump_like(path, obj, text):
    """Write obj in the layout `text` (the file as it was) has; the first of a few common layouts that reproduces the old text from the old object is used."""
    for kw in ({'indent': None, 'separators': (',', ':')}, {'indent': 1}, {'indent': 0}, {'indent': 2}, {'indent': None}):
        for sk in (True, False):
            for ea in (False, True):
                if json.dumps(json.loads(text), ensure_ascii=ea, sort_keys=sk, **kw) == text.rstrip('\n'):
                    with open(path, 'w', encoding='utf-8') as h: h.write(json.dumps(obj, ensure_ascii=ea, sort_keys=sk, **kw) + ('\n' if text.endswith('\n') else ''))
                    return True
    return False

def edit(path, fn):
    """Apply fn(obj) -> changed? to a JSON file, keeping its layout. Returns True when the file changed."""
    text = open(path, encoding='utf-8').read(); obj = json.loads(text)
    if not fn(obj): return False
    if not dump_like(path, obj, text): raise SystemExit('cannot reproduce the layout of %s' % path)
    return True

def journey_nodes(root):
    """{(place, node)} named by a journey stop or end."""
    out = set()
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get('eco'), str) and isinstance(o.get('node'), str): out.add((o['eco'], o['node']))
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    for f in glob.glob(os.path.join(root, 'data', 'journeys', '*.json')):
        try: walk(json.load(open(f, encoding='utf-8')))
        except ValueError: pass
    return out

def place_files(root):
    return [f for f in sorted(glob.glob(os.path.join(root, 'data', 'places', '*.json'))) if os.path.basename(f) not in SKIP]

def protect(root, tab, go, reason, jn=()):
    """Take out of `go` (in place) the rows whose removal would leave a place invalid (build/validate.py: at least one abiotic and one decomp node, 10 to 34 species), and return {sid: why}.
    Deterministic: for each place in file order, a missing abiotic or decomp kind keeps its first removed row (by id); too few species keeps the removed species rows (a row that shares a page before a row with no page, then by id) until there are 10.
    The kept rows are the bad rows still in the data: they are listed so a later pass can remove them once the place has accurate nodes (owner: places can evolve)."""
    places = []
    for f in place_files(root):
        try: e = json.load(open(f, encoding='utf-8'))
        except ValueError: continue
        if isinstance(e, dict) and isinstance(e.get('nodes'), list): places.append((e.get('id'), [n for n in e['nodes'] if n.get('sp') in tab], None, [r for r in e.get('raw') or [] if isinstance(r, list)]))
    kept = {}; dropped = {}
    def keep(sid, why): go.discard(sid); kept[sid] = why
    changed = True
    while changed:
        changed = False
        for pid, nodes, tip, raw in places:
            gone_n = dropped.setdefault(pid, set()); left = [n for n in nodes if n['sp'] not in go and n['id'] not in gone_n]
            hit = False
            for kind in ('abiotic', 'decomp'):
                if not any(tab[n['sp']].get('cat') == kind for n in left):
                    c = sorted(n['sp'] for n in nodes if n['sp'] in go and tab[n['sp']].get('cat') == kind)
                    if c: keep(c[0], '%s needs an %s node' % (pid, kind)); changed = hit = True; break
            if hit: continue
            sp = [n for n in left if not tab[n['sp']].get('cat')]
            if len(sp) < 10:
                c = sorted((n['sp'] for n in nodes if n['sp'] in go and not tab[n['sp']].get('cat')), key=lambda x: (not str(reason.get(x, '')).startswith('shares'), x))
                for x in c[:10 - len(sp)]: keep(x, '%s needs 10 species' % pid); changed = True
                continue
            ids = {n['id'] for n in left}; linked = {i for r in raw if r[0] in ids and r[1] in ids for i in r[:2]}
            for o in [n for n in left if n['id'] not in linked]:   # a node whose neighbours all went has no links (build/validate.py)
                cat = tab[o['sp']].get('cat'); rest = [n for n in left if n is not o and n['id'] not in gone_n]   # nodes already dropped in this pass do not count
                essential = (pid, o['id']) in jn or (cat in ('abiotic', 'decomp') and not any(tab[n['sp']].get('cat') == cat for n in rest)) or (not cat and sum(1 for n in rest if not tab[n['sp']].get('cat')) < 10)
                if not essential: gone_n.add(o['id']); changed = True; continue
                nb = sorted(nodes_by[x]['sp'] for r in raw if o['id'] in r[:2] for x in r[:2] if x != o['id'] and x in nodes_by and nodes_by[x]['sp'] in go) if (nodes_by := {n['id']: n for n in nodes}) else []
                if nb: keep(nb[0], '%s: its node %s would have no links' % (pid, o['id'])); changed = True
    return kept, dropped

def apply(root, sids, dry=False, reason=None):
    """Remove the rows `sids`; returns (removed, kept) where kept = {sid: reason}."""
    tab = {r['sid']: r for r in species.table(root).values() if r.get('sid')}
    jn = journey_nodes(root); kept = {}; nodeids = {}   # nodeids[place] = {node id: sid}
    for f in place_files(root):
        try: e = json.load(open(f, encoding='utf-8'))
        except ValueError: continue
        if not isinstance(e, dict): continue
        for n in e.get('nodes') or []:
            if n.get('sp') in sids:
                if (e.get('id'), n.get('id')) in jn: kept[n['sp']] = 'a journey ends at its node in %s' % e.get('id')
                nodeids.setdefault(f, {})[n['id']] = n['sp']
    go = {s for s in sids if s in tab and s not in kept}
    pk, dropped = protect(root, tab, go, reason or {}, jn)
    kept.update(pk)
    if dry: return sorted(go), kept
    for f, ids in nodeids.items():
        pid = json.load(open(f, encoding='utf-8')).get('id'); gone = {i for i, s in ids.items() if s in go} | dropped.get(pid, set())
        if not gone: continue
        def fix(e):
            if (e.get('tip') or {}).get('id') in gone: del e['tip']   # the opening tip is optional (build/validate.py); it names a node that is going
            e['nodes'] = [n for n in e['nodes'] if n.get('id') not in gone]
            e['raw'] = [r for r in e.get('raw') or [] if not (gone & set(r[:2]))]
            if e.get('ev'): e['ev'] = {k: v for k, v in e['ev'].items() if not (gone & set(k.split('>')))}
            return True
        edit(f, fix)
    dd = os.path.join(root, 'data', 'diets')
    for sub in sorted(os.listdir(dd)) if os.path.isdir(dd) else []:
        for fn in sorted(os.listdir(os.path.join(dd, sub))):
            p = os.path.join(dd, sub, fn)
            if fn[:-5] in go: os.remove(p); continue
            def fixd(o):
                ch = False
                for k in ('prey', 'pred'):
                    if isinstance(o.get(k), dict):
                        for s in [s for s in o[k] if s in go]: del o[k][s]; ch = True
                return ch
            if edit(p, fixd) and not json.load(open(p, encoding='utf-8')).get('prey'): os.remove(p)   # a diet file with no prey is not a diet
    sp = os.path.join(root, 'data', 'species')
    def drop_ids(o):
        if isinstance(o, dict): return bool([o.pop(s) for s in [s for s in o if s in go]])
        if isinstance(o, list) and any(s in go for s in o): o[:] = [s for s in o if s not in go]; return True
        return False
    for name in ('taxonomy.json', 'conservation.json', 'taxonomy_manual.json', 'taxonomy_review.json', 'conservation_asked.json'):
        p = os.path.join(sp, name)
        if os.path.exists(p): edit(p, drop_ids)
    p = os.path.join(sp, 'search_vocabulary.json')   # also_called {species id: [former names]}
    if os.path.exists(p): edit(p, lambda o: bool([o['also_called'].pop(s) for s in [s for s in o.get('also_called', {}) if s in go]]))
    for name in ('identity.json', 'rowtitles.json'):   # the audit files name rows by id: a removed row leaves them (data/audit/strictrows.json says why)
        p = os.path.join(root, 'data', 'audit', name)
        if os.path.exists(p): edit(p, lambda o: bool([o['rows'].pop(s) for s in [s for s in o['rows'] if s in go]]))
    from species_photos import SpeciesPhotos
    w = SpeciesPhotos(root)
    for s in sorted(go): w.forget(s)
    w.commit()
    for s in sorted(go):
        p = species.row_path(s, os.path.join(root, 'data', 'nodes' if tab[s].get('sk') == 'resource' else 'species', 'rows'))
        if os.path.exists(p): os.remove(p)
    return sorted(go), kept

PLACE_RES = (re.compile(r'^(\w+) needs '), re.compile(r'^(\w+): its node'))

def blocking_places(kept):
    """{place id: why} for the kept rows that block a place (protect() wrote the place id in the reason). A row kept for a journey names no place."""
    out = {}
    for s, why in kept.items():
        for rx in PLACE_RES:
            m = rx.match(why)
            if m: out.setdefault(m.group(1), why); break
    return out

def remove_place(root, pid):
    """Remove a whole place with everything that names it: file, outline and its credit and missing rows, place_inputs row, order entry, picture and larger copy and their rows. Journeys are not edited: the caller skips places a journey names."""
    for rel in (('data', 'places', pid + '.json'), ('data', 'outlines', pid + '.json')):
        p = os.path.join(root, *rel)
        if os.path.exists(p): os.remove(p)
    for rel in (('data', 'outline_records.json'), ('data', 'outline_missing.json'), ('photos', 'places', 'places.json'), ('photos', 'places', 'missing.json'),
                ('photos', 'places_large.json'), ('photos', 'places_tried.json')):
        p = os.path.join(root, *rel)
        if not os.path.exists(p): continue
        def drop(o):
            if rel[-1] == 'places.json' and rel[1] == 'places' and pid in o:
                f = os.path.join(root, 'photos', 'places', o[pid].get('f') or pid + '.jpg')
                if os.path.exists(f): os.remove(f)
            return o.pop(pid, None) is not None
        edit(p, drop)
    import place_inputs
    pi = place_inputs.PlaceInputs(root)
    if pid in pi.recs: pi.recs.pop(pid); pi.commit()   # its file keeps its own layout
    f = os.path.join(root, 'photos', 'places-lg', pid + '.webp')
    if os.path.exists(f): os.remove(f)
    for p in sorted(glob.glob(os.path.join(root, 'data', 'order', '*.json'))):
        edit(p, lambda o: isinstance(o, list) and pid in o and (o.__setitem__(slice(None), [x for x in o if x != pid]) or True))

def run_places(root, ident, dry=False):
    """Remove every place that a kept row blocks (the only abiotic or decomp node, the 10-species minimum, a node with no links): such a place cannot lose its bad row without a replacement, so it is removed and can be
    recreated with accurate nodes later (owner, 24 Nov: delete, then recreate). A place a journey names stays. Repeats until no removable place is blocked, then removes the rows. Returns (removed places {id: why}, removed rows, kept rows)."""
    reason = BATCHES['all'](ident); jp = {p for p, _ in journey_nodes(root)}; gone = {}
    while True:
        _, kept = apply(root, set(reason), dry=True, reason=reason)
        todo = {p: w for p, w in blocking_places(kept).items() if p not in jp and p not in gone}
        if not todo: break
        for p, w in sorted(todo.items()):
            gone[p] = w
            if not dry: remove_place(root, p)
        if dry: break
    if dry: return gone, [], kept
    rows, kept = apply(root, set(reason), False, reason)
    return gone, rows, kept

def record(root, batch, removed, reason, kept, places=None):
    p = os.path.join(root, 'data', 'audit', 'strictrows.json')
    d = json.load(open(p)) if os.path.exists(p) else {'removed': {}, 'kept': {}}
    d['asOf'] = datetime.date.today().isoformat()
    if places: d.setdefault('places', {}).update(places)
    for s in removed: d['removed'][s] = [batch, reason[s]]; d['kept'].pop(s, None)
    for s, why in kept.items(): d['kept'][s] = why
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as h: json.dump(d, h, ensure_ascii=False, separators=(',', ':'), sort_keys=True)

def main(argv):
    batch = argv[argv.index('--batch') + 1]; dry = '--dry' in argv
    ident = json.load(open(os.path.join(ROOT, 'data', 'audit', 'identity.json'), encoding='utf-8'))
    if batch == 'places':
        gone, removed, kept = run_places(ROOT, ident, dry); reason = BATCHES['all'](ident)
        print('%d places %s (a kept row blocked each); %d rows %s, %d kept' % (len(gone), 'to remove' if dry else 'removed', len(removed), 'to remove' if dry else 'removed', len(kept)))
        for p, w in sorted(gone.items()): print('place', p, w)
        for s, why in sorted(kept.items()): print('kept', s, why)
        if not dry: record(ROOT, batch, removed, reason, kept, gone)
        return
    reason = BATCHES[batch](ident); removed, kept = apply(ROOT, set(reason), dry, reason)
    print('%d rows %s, %d kept (the data would break without them)' % (len(removed), 'to remove' if dry else 'removed', len(kept)))
    for s, why in sorted(kept.items()): print('kept', s, why)
    if not dry: record(ROOT, batch, removed, reason, kept)

if __name__ == '__main__': main(sys.argv[1:])
