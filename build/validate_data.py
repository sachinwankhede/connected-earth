#!/usr/bin/env python3
"""validate_data.py [root]: format checks for the data files that are not places (places have build/validate.py).
Species table, journeys, outlines, species pictures (by species id). Prints one line per problem and exits 1 if there is any."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
DIRTY_AUTHOR_IS_ERROR = True   # the cleanauthors data merged on 15 Nov (#930), so the validator fails a place picture whose author is not in the stored form (lib/author_clean.py)
OUTSIDE_IS_ERROR = True   # a place's own point more than 5 km outside its own outline (#977; lib/outline_check.py) fails a data pull request (#1004: the 22 places were fixed by jobs/fixoutlinepoints.py, 17 Nov)

def load(root, *p):
    path = os.path.join(root, *p)
    return json.load(open(path)) if os.path.exists(path) else None

SCHEMAS = os.path.join(HERE, 'schemas')
_validators = {}
def shape(obj, kind, where, errs):
    """Check one object against build/schemas/<kind>.schema.json (the written contract of that file); one error line per problem, with the path of the bad value."""
    import jsonschema
    if kind not in _validators:
        schema = json.load(open(os.path.join(SCHEMAS, kind + '.schema.json')))
        _validators[kind] = jsonschema.Draft202012Validator(schema)
    for e in sorted(_validators[kind].iter_errors(obj), key=lambda e: [str(p) for p in e.absolute_path]):
        path = '/'.join(str(p) for p in e.absolute_path)
        errs.append('%s%s: %s' % (where, ' [%s]' % path if path else '', e.message[:160]))

# Two places must not share one `imgwiki` (the Wikipedia title the place's picture and links come from; #887, #908).
# The ten places that shared five titles were fixed in #908 (data-fiximgwiki: six got their own title, the duplicate sdponca was removed, 15 Nov), so the check is an ERROR: it fails the data pull request.
SHARED_IMGWIKI_IS_ERROR = True

def shared_imgwiki(root):
    """{title: [place ids]} for every `imgwiki` used by more than one place (reads only that field of each file)."""
    by = {}; full = os.path.join(root, 'data/places')
    if os.path.isdir(full):
        for f in sorted(os.listdir(full)):
            if not f.endswith('.json') or f in ('order.json', 'links.json'): continue
            try: e = json.load(open(os.path.join(full, f)))
            except (OSError, ValueError): continue
            t = e.get('imgwiki') if isinstance(e, dict) else None
            if isinstance(t, str) and t: by.setdefault(t, []).append(f[:-5])
    return {t: ids for t, ids in by.items() if len(ids) > 1}

def place_ids(root):
    ids = set()
    full = os.path.join(root, 'data/places')
    if os.path.isdir(full): ids |= {f[:-5] for f in os.listdir(full) if f.endswith('.json')}
    return ids

def local_ids(root):
    """Places whose level is "local": the app loads their entries on demand, so a journey must not end at one (#406)."""
    out = set(); full = os.path.join(root, 'data/places')
    if os.path.isdir(full):
        for f in os.listdir(full):
            if not f.endswith('.json') or f in ('order.json', 'links.json'): continue
            try: e = json.load(open(os.path.join(full, f)))
            except (OSError, ValueError): continue
            if isinstance(e, dict) and e.get('level') == 'local': out.add(f[:-5])
    return out

def species_sid_errors(spw, sids):
    """What lib/species_photos.SpeciesPhotos.check() does not see (#934 phase 6): every list is keyed by a species id that is a row of data/species/rows, and no file of the picture folders
    is of a kind the writer never makes (check() only counts .webp in photos/species)."""
    import species_photos as spm
    errs = []
    for label, d in (('species_pictures.json', spw.pics), ('species_medium.json', spw.medium), ('species_large.json', spw.large), ('species_missing.json', spw.miss_), ('species_tried.json', spw.tried)):
        for sid in sorted(set(d) - sids): errs.append('photos/%s: %r is not a species row' % (label, sid))
    for parts in (spm.SMALL_DIR, spm.MEDIUM_DIR, spm.LARGE_DIR):
        for f in sorted(spw._files(parts)):
            if not f.endswith('.webp'): errs.append('%s/%s is not a .webp picture (nothing writes it)' % ('/'.join(parts), f))
    return errs

NAME_OVERRIDE_LIMIT = 730    # #887 step 7: a place node names its species by id and keeps a `name` or `wiki` of its own only when it differs from the species row. These are the counts left after
WIKI_OVERRIDE_LIMIT = 250    # jobs/cleanoverrides.py dropped the case-and-punctuation-only names (17 Nov); a pull request may lower them (edit the number) but never raise them: a change of name or page belongs in the species row.

def override_errors(root, sp):
    """A place node must not repeat the row's name in other capitals, and the number of nodes with a name or wiki of their own must not grow."""
    import species
    by_sid = {r['sid']: r for r in sp.values() if r.get('sid')}; errs = []; names = wikis = 0
    full = os.path.join(root, 'data/places')
    for f in sorted(os.listdir(full)) if os.path.isdir(full) else []:
        if not f.endswith('.json') or f in ('links.json', 'order.json', 'species.json', 'bounds.json'): continue
        try: e = json.load(open(os.path.join(full, f)))
        except (OSError, ValueError): continue
        for n in (e.get('nodes') or []) if isinstance(e, dict) else []:
            row = by_sid.get(n.get('sp'))
            if not row: continue
            if 'name' in n:
                names += 1
                if species.same_name(n['name'], row.get('name')): errs.append('data/places/%s: node %s has name %r, the species row says %r (same name; drop it: python3 jobs/cleanoverrides.py)' % (f, n.get('id'), n['name'], row.get('name')))
            if 'wiki' in n: wikis += 1
    if names > NAME_OVERRIDE_LIMIT: errs.append('place nodes with a name of their own: %d, over the limit of %d (#887 step 7): change the species row, or point the node at the right species (sp); a different concept (Decomposers, Soil microbes) is a group row of its own. Never create a species row only to hold a spelling or regional name (one species has one row; #1038).' % (names, NAME_OVERRIDE_LIMIT))
    if wikis > WIKI_OVERRIDE_LIMIT: errs.append('place nodes with a wiki page of their own: %d, over the limit of %d (#887 step 7): change the species row, or point the node at the right species (sp). Never create a species row only to hold a spelling or regional name (one species has one row; #1038).' % (wikis, WIKI_OVERRIDE_LIMIT))
    return errs

PAGE_SHARED_LIMIT = 151      # #1061 / docs/NODE-IDENTITY.md I3 and I4: counts today; a pull request may lower them (merge or retire rows) but never raise them. The add process refuses a row whose page another row or a place already holds, so these only go down.
PAGE_PLACE_LIMIT = 27

def page_errors(root, sp):
    """I3: a Wikipedia page is the article of one row. I4: no row's page is a place's own article (a place is never a row)."""
    import re, collections
    n = lambda t: re.sub(r'[\s_]+', ' ', str(t or '')).strip().lower()
    pg = collections.defaultdict(set)
    for r in sp.values():
        if r.get('wiki') and r.get('sid'): pg[n(r['wiki'])].add(r['sid'])
    shared = sorted(p for p, v in pg.items() if len(v) > 1)
    places = set(); full = os.path.join(root, 'data/places')
    for f in sorted(os.listdir(full)) if os.path.isdir(full) else []:
        if not f.endswith('.json') or f in ('links.json', 'order.json', 'species.json', 'bounds.json'): continue
        try: e = json.load(open(os.path.join(full, f)))
        except (OSError, ValueError): continue
        if isinstance(e, dict): places.update(n(e[k]) for k in ('name', 'imgwiki') if e.get(k))
    held = sorted(p for p in pg if p in places); errs = []
    if len(shared) > PAGE_SHARED_LIMIT: errs.append('Wikipedia pages held by more than one species row: %d, over the limit of %d (I3): one page, one row; add through the add process, which refuses a page that is taken. Newest: %s' % (len(shared), PAGE_SHARED_LIMIT, ', '.join(shared[:5])))
    if len(held) > PAGE_PLACE_LIMIT: errs.append('species rows whose page is a place article: %d, over the limit of %d (I4): a place is never a node or a row. Pages: %s' % (len(held), PAGE_PLACE_LIMIT, ', '.join(held[:5])))
    return errs

def check(root):
    errs = []; warns = []
    sys.path.insert(0, HERE); import species
    sp = species.table(root)
    rows_dir = os.path.join(root, 'data', 'species', 'rows'); nodes_dir = os.path.join(root, 'data', 'nodes', 'rows')
    node_sids = set()
    if os.path.isdir(rows_dir):   # one file per species (#276) and per non-species node (#976): each is checked on its own, and sits where its sid says
        keys = {}
        for base, label in ((rows_dir, 'species'), (nodes_dir, 'node')):
            if not os.path.isdir(base): continue
            for d in sorted(os.listdir(base)):
                for f in sorted(os.listdir(os.path.join(base, d))):
                    if not f.endswith('.json'): continue
                    r = json.load(open(os.path.join(base, d, f)))
                    shape(r, 'species-row', '%s file %s/%s' % (label, d, f), errs)
                    if isinstance(r, dict) and isinstance(r.get('sid'), str) and (d, f) != (r['sid'][:2], r['sid'] + '.json'):
                        errs.append('%s file %s/%s: a row with sid %r belongs in %s/%s.json' % (label, d, f, r['sid'], r['sid'][:2], r['sid']))
                    if isinstance(r, dict) and label == 'node':
                        node_sids.add(r.get('sid'))
                        if r.get('sk') != 'resource': errs.append('node file %s/%s: data/nodes/rows holds only rows of kind resource (sk is %r)' % (d, f, r.get('sk')))
                    elif isinstance(r, dict) and r.get('sk') == 'resource' and os.path.isdir(nodes_dir): errs.append('species file %s/%s: a row of kind resource is not a species, it belongs in data/nodes/rows (#976; checked once that folder exists, so the one-time move job can land after this code)' % (d, f))
                    if isinstance(r, dict) and r.get('name'):
                        k = (r.get('latin') or r['name']).lower()
                        if k in keys: errs.append('%s files %s and %s have the same table key %r (the loader keeps only one)' % (label, keys[k], '%s/%s' % (d, f), k))
                        keys.setdefault(k, '%s/%s' % (d, f))
    else:
        for k, v in sp.items(): shape(v, 'species-row', 'species %r' % k, errs)
    errs += override_errors(root, sp)
    errs += page_errors(root, sp)
    sids = [v.get('sid') for v in sp.values()]
    if sp and (None in sids or len(set(sids)) != len(sids)): errs.append('species: every row needs its own sid (stable id)')
    for k, v in sp.items():   # #1013: the build writes the id of a species node, a file name and a link from the stored sid, and the app and the tests treat it as the slug of the Latin name; that holds for every taxon and group today, so it is enforced here. A resource row (rain, soil: not a species) may carry a `-2` suffix when two names slug alike.
        if v.get('sk') in ('taxon', 'group') and v.get('sid') and v['sid'] != species.slug(v.get('latin') or v.get('name') or ''):
            errs.append('species %r: its sid %r is not the slug of its name (%r); the build and the app expect it to be' % (k, v['sid'], species.slug(v.get('latin') or v.get('name') or '')))
    ids = place_ids(root)
    pd_ = os.path.join(root, 'data', 'places')   # #973 phase 4: every node of a food web that names a species row (`sp`) finds it, and the row has its id, so the app can ask for its picture by id
    if sp and os.path.isdir(pd_):
        have = {v['sid'] for v in sp.values() if v.get('sid')}
        for f in sorted(os.listdir(pd_)):
            if not f.endswith('.json') or f in ('links.json', 'order.json', 'species.json', 'bounds.json'): continue
            for n in json.load(open(os.path.join(pd_, f))).get('nodes', []):
                if isinstance(n, dict) and 'sp' in n and n['sp'] not in have: errs.append('place %s: node %r names species id %r, which is not the sid of any species row' % (f[:-5], n.get('id'), n['sp']))
    import journeydata
    errs += journeydata.order_problems(root)
    has_links = os.path.exists(os.path.join(root, 'data', 'journeys', 'links.json'))
    if has_links or journeydata.journeys_are_new(root):
        order = journeydata.order(root)[0]
        if len(order) != len(set(order)): errs.append('journeys: place order has duplicates')
        for i in order:
            if i not in ids: errs.append('journeys: ordered place %r has no file' % i)
        seen = set(); locs = local_ids(root)
        for where, c in journeydata.raw_journeys(root):
            shape(c, 'journey', where, errs)
            if not isinstance(c, dict): continue
            cid = c.get('id')
            if not cid or cid in seen: errs.append('journeys: missing or repeated id %r' % cid)
            seen.add(cid)
            for en in list(c.get('ends') or []) + [c.get('from'), c.get('to')]:
                if isinstance(en, dict) and en.get('eco') not in ids: errs.append('journey %r: place %r has no file' % (cid, en.get('eco')))
                elif isinstance(en, dict) and en.get('eco') in locs: errs.append('journey %r: place %r is local; its entry may not be loaded when the journey is drawn (the app reads ECO_BY[eco].conts)' % (cid, en.get('eco')))
        if journeydata.journeys_are_new(root): shape(json.load(open(os.path.join(root, 'data', 'journeys', 'config.json'))), 'journey-config', 'journeys/config.json', errs)
    od = os.path.join(root, 'data', 'outlines')
    if os.path.isdir(od):
        for f in sorted(os.listdir(od)):
            if not f.endswith('.json'): continue
            if f[:-5] not in ids: errs.append('outline %s has no place' % f)   # an error since #255 (a leftover usually means a rename went wrong)
            o = json.load(open(os.path.join(od, f)))
            shape(o, 'outline', 'outline %s' % f, errs)
            for n, ring in enumerate(o.get('r', []) if isinstance(o, dict) and isinstance(o.get('r'), list) else []):
                if not isinstance(ring, list) or any(not isinstance(v, (int, float)) for v in ring): continue   # the shape check reports it
                if len(ring) % 2: errs.append('outline %s: ring %d has an odd number of values (it is [lon, lat, ...])' % (f, n))
                elif any(not -180 <= ring[i] <= 180 or not -90 <= ring[i + 1] <= 90 for i in range(0, len(ring), 2)):
                    errs.append('outline %s: ring %d has a point outside lon -180..180 / lat -90..90' % (f, n))
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib'))   # species pictures (#934): keyed by species id, checked by their one writer (lib/species_photos.py); a missing list is an empty one
    import species_photos; spw = species_photos.SpeciesPhotos(root); errs += spw.check(); errs += species_sid_errors(spw, {r.get('sid') for r in sp.values()} - node_sids)
    dirty_sp = spw.dirty_authors()   # an error since the cleanauthors job cleaned the stored rows (15 Nov, #964), as for places
    if dirty_sp: (errs if DIRTY_AUTHOR_IS_ERROR else warns).append('photos/species_pictures.json: %d stored author(s) need cleaning (lib/author_clean.py), first %s' % (len(dirty_sp), ', '.join(dirty_sp[:5])))
    import journey_pics   # journey cover pictures (#945): by journey id, checked by their one writer once photos/journey_pictures.json exists (nothing to check before)
    errs += journey_pics.check(root)
    if journey_pics.new_shape(root):
        import journey_photos; dirty_jp = journey_photos.JourneyPhotos(root).dirty_authors()
        if dirty_jp: (errs if DIRTY_AUTHOR_IS_ERROR else warns).append('photos/journey_pictures.json: %d stored author(s) need cleaning (lib/author_clean.py), first %s' % (len(dirty_jp), ', '.join(dirty_jp[:5])))
    import node_photos   # pictures of non-species nodes (#976): by node id, checked by their one writer (lib/node_photos.py); nothing to check before photos/node_pictures.json exists
    errs += node_photos.NodePhotos(root).check()
    import outline_check; far = outline_check.outside(root, 5.0)   # a point far outside its own outline means a wrong point or the wrong outline (#977, docs/DATA-AUDIT.md)
    if far: (errs if OUTSIDE_IS_ERROR else warns).append('%d place point(s) lie more than 5 km outside their own outline, first %s' % (len(far), ', '.join('%s (%s km)' % (pid, d) for d, pid in far[:5])))
    import outline_records   # credit records of park outlines (#977): files and records agree, once data/outline_records.json exists (nothing to check before)
    orx = outline_records.OutlineRecords(root); errs += orx.check()
    import place_inputs; pe, pw_ = place_inputs.PlaceInputs(root).check(); errs += pe; warns += pw_   # what each place's food web and story were built from (#887 step 5b): a web that changed without `build/species.py pack`, a story with no record
    st = orx.stale()   # the place moved or was renamed after its outline was built: look again (jobs/dropoutlines.py puts it back on the list); a warning until the outline job re-checks by itself
    if st: warns.append('%d outline(s) were built for a place that has since moved or been renamed, first %s' % (len(st), ', '.join('%s (%s)' % x for x in st[:5])))
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib'))   # place pictures (#887): files, lists, larger copies, missing.json and authors agree; the app does not depend on this (a place without a picture shows none), the data keeps itself consistent
    import place_photos; pw = place_photos.PlacePhotos(root); errs += pw.check()
    dirty = pw.dirty_authors()   # authors that carry an email, talk stamp, web address or sentence (owner, 15 Nov); an error since jobs/cleanauthors.py cleaned the stored rows (DIRTY_AUTHOR_IS_ERROR)
    if dirty: (errs if DIRTY_AUTHOR_IS_ERROR else warns).append('photos/places/places.json: %d stored author(s) need cleaning (lib/author_clean.py), first %s' % (len(dirty), ', '.join(dirty[:5])))
    # taxonomy sidecar (#254): shape per file, and rules across files
    ld = os.path.join(root, 'data', 'ledger')   # docs/ADD-SPECIES.md: the refusal ledger, one file per kind, written only by lib/creation_ledger.py
    for f in sorted(os.listdir(ld)) if os.path.isdir(ld) else []:
        if f.endswith('.json'): shape(json.load(open(os.path.join(ld, f))), 'ledger', 'data/ledger/' + f, errs)
    tx = load(root, 'data', 'species', 'taxonomy.json'); rv = load(root, 'data', 'species', 'taxonomy_review.json')
    man = load(root, 'data', 'species', 'taxonomy_manual.json')
    if tx is not None or rv is not None or man is not None:
        taxa = {r.get('sid') for r in sp.values() if r.get('sk') == 'taxon'}
        for obj, kind, name in ((tx, 'taxonomy', 'taxonomy.json'), (rv, 'taxonomy-review', 'taxonomy_review.json')):
            if obj is None: continue
            shape(obj, kind, 'data/species/' + name, errs)
            for sid in sorted(set(obj) - taxa): errs.append('data/species/%s: %r is not a species of kind taxon' % (name, sid))
        if man is not None:
            shape(man, 'taxonomy-manual', 'data/species/taxonomy_manual.json', errs)
            for sid in sorted(set(man) - taxa): errs.append('data/species/taxonomy_manual.json: %r is not a species of kind taxon' % sid)
        for sid in sorted(set(tx or {}) & set(rv or {})): errs.append('taxonomy: %r is both accepted and in the review list' % sid)
    # conservation status (#1024): by species id, like every other species file
    cons = load(root, 'data', 'species', 'conservation.json'); casked = load(root, 'data', 'species', 'conservation_asked.json')
    if cons is not None or casked is not None:
        for name, ids in (('conservation.json', cons or {}), ('conservation_asked.json', casked or [])):
            for sid in sorted(set(ids) - set(sids), key=str): errs.append('data/species/%s: %r is not the id of a species row' % (name, sid))
    # web name check (#1061): what jobs/rowtitles.py decided for each row; the data status page reads it
    rt = load(root, 'data', 'audit', 'rowtitles.json')
    if rt is not None:
        if not isinstance(rt, dict) or not isinstance(rt.get('rows'), dict) or not isinstance(rt.get('asOf'), str): errs.append('data/audit/rowtitles.json: expected {asOf, rows}')
        else:
            for sid in sorted(set(rt['rows']) - set(sids), key=str): errs.append('data/audit/rowtitles.json: %r is not the id of a species row' % (sid,))
            for sid, v in sorted(rt['rows'].items()):
                if not (isinstance(v, list) and len(v) == 3 and v[0] in ('same', 'change', 'wrongpage', 'specific', 'repoint', 'newrow', 'unresolved')): errs.append('data/audit/rowtitles.json: %r is not [status, proposed, why]' % (sid,))
    # eating-link table (#256): one file per consumer species, sitting where its sid says; the consumer and every prey must be species of the table
    dd = os.path.join(root, 'data', 'diets')
    if os.path.isdir(dd):
        sids = {r.get('sid') for r in sp.values()}
        for sub_ in sorted(os.listdir(dd)):
            for f in sorted(os.listdir(os.path.join(dd, sub_))):
                if not f.endswith('.json'): continue
                rel = 'data/diets/%s/%s' % (sub_, f); o = json.load(open(os.path.join(dd, sub_, f)))
                shape(o, 'diets', rel, errs)
                if not isinstance(o, dict) or not isinstance(o.get('prey'), dict): continue
                if o.get('sid', '')[:2] != sub_ or o.get('sid', '') + '.json' != f: errs.append('%s: the file belongs at data/diets/%s/%s.json' % (rel, str(o.get('sid', ''))[:2], o.get('sid')))
                if o.get('sid') not in sids: errs.append('%s: consumer %r is not a species' % (rel, o.get('sid')))
                for prey in sorted(set(o['prey']) - sids): errs.append('%s: prey %r is not a species' % (rel, prey))
    # job-written lists (#255, PR 2): one schema each. Old-format records and empty values are warnings, not errors, until the jobs that wrote them are cleaned up
    about = load(root, 'data', 'species', 'about.json')
    if about is not None:
        shape(about, 'about', 'data/species/about.json', errs)
        empty = sorted(k for k, v in about.items() if v == '')
        if empty: warns.append('data/species/about.json: %d empty sentence(s), first %r' % (len(empty), empty[0]))
    sums = load(root, 'data', 'text', 'summaries.json')
    if sums is not None: shape(sums, 'summaries', 'data/text/summaries.json', errs)
    names = load(root, 'jobs', 'names.json')
    if names is not None: shape(names, 'names', 'jobs/names.json', errs)
    sm = load(root, 'photos', 'species_missing.json')
    if sm is not None:   # by species id (#934): the same record as a place miss (status, checkedAt, expiresAt, attempts)
        shape(sm, 'photo-missing', 'photos/species_missing.json', errs)
    pm = load(root, 'photos', 'places', 'missing.json')
    if pm is not None:
        old = sorted(k for k, v in pm.items() if isinstance(v, str))
        if old: warns.append('photos/places/missing.json: %d old-format record(s) (plain text), first %r; the daily photo run stamps them' % (len(old), old[0]))
        shape({k: v for k, v in pm.items() if not isinstance(v, str)}, 'photo-missing', 'photos/places/missing.json', errs)
        for k, v in pm.items():
            if isinstance(v, dict) and isinstance(v.get('checkedAt'), str) and isinstance(v.get('expiresAt'), str) and v['expiresAt'] <= v['checkedAt']:
                errs.append('photos/places/missing.json [%s]: expiresAt is not after checkedAt' % k)
    geo = load(root, 'data', 'geo', 'geo.json')
    if geo is not None:
        shape(geo, 'geo', 'data/geo/geo.json', errs)
        for kind in ('countries', 'states'):
            ids = [f.get('id') for f in geo.get(kind, []) if isinstance(f, dict)]
            for i in sorted({i for i in ids if ids.count(i) > 1}, key=str): errs.append('data/geo/geo.json %s: id %r is repeated' % (kind, i))
    land = load(root, 'data', 'geo', 'land.json')
    if land is not None: shape(land, 'land', 'data/geo/land.json', errs)
    dup = shared_imgwiki(root)
    if dup:
        msg = 'data/places: %d imgwiki title(s) shared by %d places (each place needs its own, #908): %s' % (len(dup), sum(len(v) for v in dup.values()), '; '.join('%s (%s)' % (t, ', '.join(ids)) for t, ids in sorted(dup.items())))
        (errs if SHARED_IMGWIKI_IS_ERROR else warns).append(msg)
    return errs, warns

if __name__ == '__main__':
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    errs, warns = check(root)
    for w in warns[:50]: print('warn ', w)
    for e in errs[:200]: print('ERROR', e)
    print('data format: %d problem(s), %d warning(s)' % (len(errs), len(warns))); sys.exit(1 if errs else 0)
