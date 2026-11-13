#!/usr/bin/env python3
"""Place order and journeys (#277). One loader for both layouts.

Old layout: data/journeys/links.json ({order, cross, couple, src}) and data/journeys/pilot-order.json.
New layout (when data/order/ and data/journeys/config.json exist):
  data/order/<sortable name>.json   a list of place ids; the order is all files read in name order, one after the other.
                                    A job or promotion writes a NEW file, never an existing one, so two branches never clash.
                                    The main list is the ids whose place has no stage, the pilot list the ids with stage "pilot".
  data/journeys/<id>.json           one journey each (with `pos`, its place among the journey cards)
  data/journeys/config.json         {couple, src}
  python3 build/journeydata.py split   one-off: write the new layout from the old files and remove them."""
import json, os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
ROOT = paths.DATA_ROOT   # data/ lives here; the repository unless CE_DATA_ROOT is set (#787)

def _p(root, *a): return os.path.join(root or ROOT, *a)
def _load(path): return json.load(open(path, encoding='utf-8'))
def order_dir(root=None): return _p(root, 'data', 'order')
def order_is_new(root=None): return os.path.isdir(order_dir(root))
def journeys_are_new(root=None): return os.path.isfile(_p(root, 'data', 'journeys', 'config.json'))

def segments(root=None):
    """[(file name, [ids])] in order."""
    d = order_dir(root)
    return [(f, _load(os.path.join(d, f))) for f in sorted(os.listdir(d)) if f.endswith('.json')]

def sequence(root=None):
    seen = set(); out = []
    for _, ids in segments(root):
        for i in ids:
            if i not in seen: seen.add(i); out.append(i)
    return out

def order(root=None):
    """(main ids, pilot ids) in page order."""
    if not order_is_new(root):
        pilot = _p(root, 'data', 'journeys', 'pilot-order.json')
        return list(_load(_p(root, 'data', 'journeys', 'links.json'))['order']), (_load(pilot) if os.path.exists(pilot) else [])
    main, pilot = [], []
    for i in sequence(root):
        p = _p(root, 'data', 'places', i + '.json')
        if not os.path.exists(p): continue   # the data check reports it
        (pilot if _load(p).get('stage') == 'pilot' else main).append(i)
    return main, pilot

def order_problems(root=None):
    """New layout only: ids with no place file, ids in two files, places in no file."""
    if not order_is_new(root): return []
    errs = []; seen = {}
    for f, ids in segments(root):
        for i in ids:
            if i in seen: errs.append('order: place %r is in both %s and %s' % (i, seen[i], f))
            seen[i] = seen.get(i, f)
            if not os.path.exists(_p(root, 'data', 'places', i + '.json')): errs.append('order: %r in %s has no place file' % (i, f))
    pd = _p(root, 'data', 'places')
    for f in sorted(os.listdir(pd)) if os.path.isdir(pd) else []:
        if f.endswith('.json') and f[:-5] not in seen: errs.append('order: place %r is in no file in data/order/' % f[:-5])
    return errs

def journeys(root=None):
    if not journeys_are_new(root): return list(_load(_p(root, 'data', 'journeys', 'links.json')).get('cross', []))
    d = _p(root, 'data', 'journeys'); rows = []
    for f in os.listdir(d):
        if f.endswith('.json') and f != 'config.json':
            c = _load(os.path.join(d, f)); rows.append((c.pop('pos', 0), c.get('id', f[:-5]), c))
    return [c for _, _, c in sorted(rows, key=lambda r: (r[0], r[1]))]

def raw_journeys(root=None):
    """[(where, journey object)] exactly as stored (with `pos`), for the data check."""
    if not journeys_are_new(root): return [('journey %s' % c.get('id'), c) for c in _load(_p(root, 'data', 'journeys', 'links.json')).get('cross', [])]
    d = _p(root, 'data', 'journeys')
    return [('journey file %s' % f, _load(os.path.join(d, f))) for f in sorted(os.listdir(d)) if f.endswith('.json') and f != 'config.json']

def config(root=None):
    src = _load(_p(root, 'data', 'journeys', 'config.json' if journeys_are_new(root) else 'links.json'))
    return {'couple': src.get('couple'), 'src': src.get('src')}

def links(root=None):
    """The old links.json shape, for readers that want one object: {couple, src, cross, order (main ids)}."""
    return {**config(root), 'cross': journeys(root), 'order': order(root)[0]}

def add_segment(root, ids, tag):
    """Write the ids that are in no order file yet as a new file; returns its name, or None when there is nothing new."""
    known = set(sequence(root)); new = []
    for i in ids:
        if i not in known and i not in new: new.append(i)
    if not new: return None
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
    name = '%s-%s.json' % (stamp, tag); n = 2
    while os.path.exists(os.path.join(order_dir(root), name)): name = '%s-%s-%d.json' % (stamp, tag, n); n += 1
    json.dump(new, open(os.path.join(order_dir(root), name), 'w'))
    return name

def split(root=None):
    lp, pp = _p(root, 'data', 'journeys', 'links.json'), _p(root, 'data', 'journeys', 'pilot-order.json')
    lk = _load(lp); pilot = _load(pp) if os.path.exists(pp) else []
    os.makedirs(order_dir(root), exist_ok=True)
    json.dump(lk['order'], open(os.path.join(order_dir(root), '0000-main.json'), 'w'))
    json.dump(pilot, open(os.path.join(order_dir(root), '0001-pilot.json'), 'w'))
    for n, c in enumerate(lk.get('cross', [])):
        json.dump({'pos': n, **c}, open(_p(root, 'data', 'journeys', c['id'] + '.json'), 'w'), indent=1, ensure_ascii=False)
    json.dump({'couple': lk.get('couple'), 'src': lk.get('src')}, open(_p(root, 'data', 'journeys', 'config.json'), 'w'), indent=1, ensure_ascii=False)
    os.remove(lp)
    if os.path.exists(pp): os.remove(pp)
    print(len(lk['order']), 'main ids,', len(pilot), 'pilot ids,', len(lk.get('cross', [])), 'journeys written; links.json and pilot-order.json removed')

if __name__ == '__main__' and sys.argv[1:] == ['split']: split()
