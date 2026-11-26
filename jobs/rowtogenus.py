#!/usr/bin/env python3
"""rowtogenus.py (#1142, owner 26 Nov: "a row is whatever its Wikipedia page is"): a species row whose Wikipedia page is really a genus (the species title redirects to the genus article) becomes the genus row:
latin = the genus (Wikidata P225 of the page, from data/audit/identity.json), wiki = the genus page, sid = slug(genus), name by docs/NODE-NAMES.md (kept when the web name check says `same`, else its proposed name),
the photo, the nodes of every place and the diets follow. No network. Read-only unless --apply.
  python3 jobs/rowtogenus.py [--dry]      # default: print what would change and what is skipped
  python3 jobs/rowtogenus.py --apply      # write it; exits 1 and writes nothing on any collision
Converted: a taxon row of two or more words whose page the identity check says is a genus (jobs/identitycheck.py "species row on a genus page"), whose page is the row's own latin name or the genus (not a common-name
title: those are the owner's case), and whose name the web check (data/audit/rowtitles.json) settles (`same`, `change`). Skipped and listed: a genus with no English name (`unresolved`), `wrongpage`, a common-name
title, and a page of any rank above genus. Genus rows on a species page ("genus row on a species page") are never touched.
Each converted row: its row file is replaced by the genus row; place nodes `sp`, diet file and diet entries, search_vocabulary `also_called` (the old latin name is added), the picture (lib/species_photos.py rekey) and the two
audit files follow the new id. Its species-level taxonomy and conservation entries are dropped (they describe the species, not the genus). Journeys name (place, node id), which do not change.
Writes data/audit/rowtogenus.json = {asOf, converted:{old sid:[new sid, name]}, skipped:{sid:why}}."""
import datetime, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in ('build', 'lib', 'jobs'): sys.path.insert(0, os.path.join(ROOT, d))
import species, identitycheck, strictrows

def plan(root=ROOT):
    """(convert, skipped, problems): convert = {old sid: {sid, latin, name, wiki}}; skipped = {sid: why}; problems = collisions (empty means the apply is safe)."""
    ident = json.load(open(os.path.join(root, 'data', 'audit', 'identity.json'), encoding='utf-8'))
    web = json.load(open(os.path.join(root, 'data', 'audit', 'rowtitles.json'), encoding='utf-8'))['rows']
    tab = {r['sid']: r for r in species.table(root).values() if r.get('sid')}
    mm = identitycheck.mismatches(tab, ident); convert, skipped, problems = {}, {}, []
    for sid, (reason, latin, genus, rank) in sorted(mm.items()):
        if not reason.startswith('species row'): continue
        r = tab[sid]
        if r.get('sk') != 'taxon': continue
        if rank != 'genus': skipped[sid] = 'its page is a %s, not a genus' % rank; continue
        page = (r.get('wiki') or '').replace('_', ' ').lower()
        if page not in ((latin or '').lower(), (genus or '').lower()): skipped[sid] = 'its page %s is a common-name title: the owner\'s case' % r.get('wiki'); continue
        st = (web.get(sid) or ['?'])[0]
        if st not in ('same', 'change'): skipped[sid] = 'name check says %s (a genus with no English name is the owner\'s case, docs/NODE-NAMES.md step 5)' % st; continue
        name = r.get('name') if st == 'same' else (web[sid][1] or r.get('name'))
        convert[sid] = {'sid': species.slug(genus), 'latin': genus, 'name': name, 'wiki': genus}
    seen = {}
    others = {species_norm(t.get('name')): s for s, t in tab.items() if t.get('sk') == 'taxon' and s not in convert}
    for old, c in sorted(convert.items()):
        n = c['sid']
        if n in tab: problems.append('%s -> %s: a row %s already exists' % (old, n, n))
        if n in seen: problems.append('%s and %s both become %s' % (seen[n], old, n))
        seen[n] = old
        if species_norm(c['name']) in others: problems.append('%s -> %s: the name %r is already row %s' % (old, n, c['name'], others[species_norm(c['name'])]))
    return convert, skipped, problems

def species_norm(s): return ' '.join((s or '').lower().split())

def apply(root, convert):
    ids = {o: c['sid'] for o, c in convert.items()}
    for old, c in convert.items():   # the row files
        p = species.row_path(old, os.path.join(root, 'data', 'species', 'rows'))
        r = json.load(open(p, encoding='utf-8')); was = r.get('latin') or ''
        r['latin'], r['sid'], r['wiki'], r['name'] = c['latin'], c['sid'], c['wiki'], c['name']
        if was and r.get('desc'): r['desc'] = r['desc'].replace('(%s)' % was, '(%s)' % c['latin'])
        os.remove(p); species.write_row(r, os.path.join(root, 'data', 'species', 'rows'))
        c['was'] = was
    for f in strictrows.place_files(root):   # the nodes
        def fix(e):
            ch = False
            for n in e.get('nodes') or []:
                if n.get('sp') in ids: n['sp'] = ids[n['sp']]; ch = True
            return ch
        try: strictrows.edit(f, fix)
        except ValueError: pass
    dd = os.path.join(root, 'data', 'diets')
    for sub in sorted(os.listdir(dd)) if os.path.isdir(dd) else []:   # the diets: entries first, then the files
        for fn in sorted(os.listdir(os.path.join(dd, sub))):
            def fixd(o):
                ch = False
                for k in ('prey', 'pred'):
                    if isinstance(o.get(k), dict):
                        for s in [s for s in o[k] if s in ids]: o[k][ids[s]] = o[k].pop(s); ch = True
                if o.get('sid') in ids: o['sid'] = ids[o['sid']]; ch = True
                return ch
            strictrows.edit(os.path.join(dd, sub, fn), fixd)
    for old, new in ids.items():
        p = os.path.join(dd, old[:2], old + '.json')
        if os.path.exists(p):
            q = os.path.join(dd, new[:2], new + '.json'); os.makedirs(os.path.dirname(q), exist_ok=True); os.replace(p, q)
    sp = os.path.join(root, 'data', 'species')
    def drop_ids(o):
        if isinstance(o, dict): return bool([o.pop(s) for s in [s for s in o if s in ids]])
        if isinstance(o, list) and any(s in ids for s in o): o[:] = [s for s in o if s not in ids]; return True
        return False
    for name in ('taxonomy.json', 'conservation.json', 'taxonomy_manual.json', 'taxonomy_review.json', 'conservation_asked.json'):
        p = os.path.join(sp, name)
        if os.path.exists(p): strictrows.edit(p, drop_ids)
    p = os.path.join(sp, 'search_vocabulary.json')
    if os.path.exists(p):
        def vocab(o):
            ac = o.setdefault('also_called', {}); ch = False
            for old, c in sorted(convert.items()):
                names = list(ac.pop(old, []))
                if c['was'] and c['was'].lower() != c['latin'].lower() and c['was'] not in names: names.append(c['was'])
                have = ac.get(c['sid'], []); add = [x for x in names if x not in have]
                if add: ac[c['sid']] = have + add; ch = True
            return ch
        strictrows.edit(p, vocab)
    for name in ('identity.json', 'rowtitles.json'):
        p = os.path.join(root, 'data', 'audit', name)
        def audit(o):
            for old, c in convert.items():
                v = o['rows'].pop(old, None)
                if v is not None: o['rows'][c['sid']] = ['same', c['name'], ''] if name == 'rowtitles.json' else v
            return True
        if os.path.exists(p): strictrows.edit(p, audit)
    from species_photos import SpeciesPhotos
    w = SpeciesPhotos(root)
    for old, new in ids.items(): w.rekey(old, new)
    w.commit()

def record(root, convert, skipped):
    p = os.path.join(root, 'data', 'audit', 'rowtogenus.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as h:
        json.dump({'asOf': datetime.date.today().isoformat(), 'converted': {o: [c['sid'], c['name']] for o, c in sorted(convert.items())}, 'skipped': dict(sorted(skipped.items()))}, h, ensure_ascii=False, separators=(',', ':'), sort_keys=True)

def main(argv):
    convert, skipped, problems = plan(ROOT)
    print('%d rows %s, %d skipped' % (len(convert), 'to convert' if '--apply' not in argv else 'converted', len(skipped)))
    for o, c in sorted(convert.items()): print('convert', o, '->', c['sid'], '|', c['name'])
    for s, w in sorted(skipped.items()): print('skip', s, '|', w)
    for q in problems: print('COLLISION', q)
    if problems: sys.exit(1)
    if '--apply' in argv:
        apply(ROOT, convert); record(ROOT, convert, skipped)

if __name__ == '__main__': main(sys.argv[1:])
