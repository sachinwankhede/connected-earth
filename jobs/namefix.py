#!/usr/bin/env python3
"""namefix.py (#1061, owner 24 Nov: "go ahead"): rows whose name does not match their own Wikipedia page, using the web name check (data/audit/rowtitles.json) and the identity check
(data/audit/identity.json). No network.
  python3 jobs/namefix.py --list [--dry]     # print the two lists
  python3 jobs/namefix.py --rename [--dry]   # rename the clear cases: a taxon row whose page is about exactly that taxon, or a species or subspecies row whose page is about one species; the new name is the page's own title
  (the others are removed by `jobs/strictrows.py --batch badname`: a row whose name says one thing and whose page another does not know what it is; no data is better than bad data)
A rename changes only the row's `name`; its nodes follow it. Groups and rows whose page is about something broader are never renamed."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for d in ('build', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import species, data_audit
SPECIES_RANKS = ('species', 'subspecies')

def lists(root=ROOT):
    """(rename, delete): rename = {sid: new name}; delete = {sid: reason}. Both only for rows whose name breaks the naming rule and for which the web check proposes a name."""
    web = json.load(open(os.path.join(root, 'data', 'audit', 'rowtitles.json'), encoding='utf-8'))['rows']
    ident = json.load(open(os.path.join(root, 'data', 'audit', 'identity.json'), encoding='utf-8')); ranks = ident.get('ranks') or {}
    tab = {r['sid']: r for r in species.table(root).values() if r.get('sid')}
    ren, dele = {}, {}
    for sid, r in sorted(tab.items()):
        v = web.get(sid)
        if not v or v[0] != 'change' or r.get('sk') not in ('taxon', 'group') or not r.get('wiki'): continue
        page, name = r['wiki'], r.get('name') or ''
        if data_audit.scientific(page, r) or data_audit.plain(name) == data_audit.plain(page): continue   # not a name that breaks the rule
        iv = (ident['rows'].get(sid) or [''] * 5); rank = ranks.get(iv[1], '')
        same_taxon = bool(iv[2]) and iv[2].lower() == (r.get('latin') or '').lower()   # the page is about exactly this taxon, at any rank (Salix on Willow)
        if r['sk'] == 'taxon' and v[1] and (same_taxon or (rank in SPECIES_RANKS and len((r.get('latin') or '').split()) >= 2)):
            ren[sid] = v[1]
        else:
            dele[sid] = 'its name and its page disagree on what it is (%s on the page %s)' % (name, page)
    return ren, dele

def shared(root=ROOT):
    """{sid: new name} for taxon rows that share one name with another taxon row (owner, 24 Nov, #1061). One row per name keeps it: a genus row ("Carex": Sedges) first, else the row most places use (ties: the first id).
    Every other row takes its own page's title when that is the row's own scientific name (Acer saccharinum; a page about the genus does not count), which is always true and never clashes. Nothing is deleted: these are different species that share a common name."""
    import collections
    tab = {r['sid']: r for r in species.table(root).values() if r.get('sid')}; use = collections.Counter(); d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)):
        if not f.endswith('.json') or f in data_audit.SKIP: continue
        try: e = json.load(open(os.path.join(d, f), encoding='utf-8'))
        except (OSError, ValueError): continue
        for n in (e.get('nodes') or []) if isinstance(e, dict) else []:
            if n.get('sp'): use[n['sp']] += 1
    by = collections.defaultdict(list)
    for sid, r in tab.items():
        if r.get('sk') == 'taxon' and r.get('name'): by[data_audit.norm(r['name'])].append(sid)
    taken = {data_audit.norm(r.get('name') or '') for r in tab.values() if r.get('sk') == 'taxon'}; out = {}
    for name, m in sorted(by.items()):
        if len(m) < 2: continue
        keep = sorted(m, key=lambda s: (len((tab[s].get('latin') or '').split()) > 1, -use[s], s))[0]
        for s in m:
            r = tab[s]; page = r.get('wiki') or ''
            if s != keep and page and data_audit.scientific(page, r) and data_audit.norm(page) == data_audit.norm(r.get('latin') or '') and data_audit.norm(page) not in taken: out[s] = page; taken.add(data_audit.norm(page))
    return out

def rename(root, ren, dry=False):
    done = []
    for sid, new in sorted(ren.items()):
        p = os.path.join(root, 'data', 'species', 'rows', sid[:2], sid + '.json')
        if not os.path.exists(p): continue
        text = open(p, encoding='utf-8').read(); d = json.loads(text); old = d.get('name')
        if old == new: continue
        done.append((sid, old, new))
        if dry: continue
        d['name'] = new
        out = json.dumps(d, ensure_ascii=False, indent=1 if text.startswith('{\n ') else None, separators=None if text.startswith('{\n ') else (',', ':'))
        open(p, 'w', encoding='utf-8').write(out + ('\n' if text.endswith('\n') else ''))
    return done

def main(argv):
    ren, dele = lists(ROOT); dry = '--dry' in argv
    if '--shared' in argv: ren = shared(ROOT); argv = [a for a in argv if a != '--list'] + ['--rename']
    if '--rename' in argv:
        done = rename(ROOT, ren, dry); print('%d rows %s' % (len(done), 'to rename' if dry else 'renamed'))
        for sid, old, new in done: print('rename', sid, '|', old, '->', new)
    else:
        print('%d to rename, %d to remove' % (len(ren), len(dele)))
        for s, n in sorted(ren.items()): print('rename', s, '->', n)
        for s, w in sorted(dele.items()): print('remove', s, '|', w)

if __name__ == '__main__': main(sys.argv[1:])
