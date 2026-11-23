#!/usr/bin/env python3
"""strictrows.py (#1061, owner 23 Nov: "delete all bad/conflicting data... no data is better than bad data"): remove species rows whose page is not about exactly that thing,
with everything that depends on them, in batches. Reads data/audit/identity.json (jobs/identity.py); no network.
  python3 jobs/strictrows.py --batch nopage [--dry]     # rows whose page has no Wikidata item (missing, disambiguation, section redirect, no page)
Removing a row removes: its row file; the nodes of every place that name it (and the edge records `raw`/`ev` that name those nodes); its diet file and its entries in other diet files;
its taxonomy, conservation and picture entries (through lib/species_photos.py). A row whose node is the end of a journey is KEPT and listed (a journey is not edited here).
It writes data/audit/strictrows.json = {asOf, removed:{sid:[batch, reason]}, kept:{sid:reason}} so the status page and the validator know what was removed and why. It never touches a row it was not asked for."""
import datetime, glob, json, os, sys
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

def apply(root, sids, dry=False):
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
    if dry: return sorted(go), kept
    for f, ids in nodeids.items():
        gone = {i for i, s in ids.items() if s in go}
        if not gone: continue
        def fix(e):
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

def record(root, batch, removed, reason, kept):
    p = os.path.join(root, 'data', 'audit', 'strictrows.json')
    d = json.load(open(p)) if os.path.exists(p) else {'removed': {}, 'kept': {}}
    d['asOf'] = datetime.date.today().isoformat()
    for s in removed: d['removed'][s] = [batch, reason[s]]; d['kept'].pop(s, None)
    for s, why in kept.items(): d['kept'][s] = why
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as h: json.dump(d, h, ensure_ascii=False, separators=(',', ':'), sort_keys=True)

def main(argv):
    batch = argv[argv.index('--batch') + 1]; dry = '--dry' in argv
    ident = json.load(open(os.path.join(ROOT, 'data', 'audit', 'identity.json'), encoding='utf-8'))
    reason = BATCHES[batch](ident); removed, kept = apply(ROOT, set(reason), dry)
    print('%d rows %s, %d kept (journey)' % (len(removed), 'to remove' if dry else 'removed', len(kept)))
    for s, why in sorted(kept.items()): print('kept', s, why)
    if not dry: record(ROOT, batch, removed, reason, kept)

if __name__ == '__main__': main(sys.argv[1:])
