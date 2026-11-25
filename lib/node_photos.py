#!/usr/bin/env python3
"""node_photos.py: the one writer for the pictures of non-species food-web nodes (sunlight, rain, soil, decomposers...; #976, docs/DATA-PLAN.md "Credits").

A node is named by its concept: the id is the slug of the node's `wiki` title (`Sunbeam` -> `sunbeam`; owner, 16 Nov), so the 1,519 Sunlight nodes of 1,548 places share one picture.
A node picture is its row in `photos/node_pictures.json` (the shared credit record: a author, l licence, lu licence link, p source page, f file, page, wiki, built, checkedAt; no `expires`,
owner 16 Nov) and the 192 px file `photos/nodes/<f>` the app shows. A concept with no usable picture is in `photos/node_missing.json` (one retry policy, photo_registry.negative_entry);
a node without a picture keeps its icon. Same method names as lib/species_photos.py. commit() writes files first, lists last, deletions after, so a killed job leaves at worst a file no list
mentions (check() finds it, repair() removes it)."""
import hashlib, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photo_registry as pr
import author_clean as ac
from place_photos import CreditRepair, author_missing, _read, _write_bytes, _write_json

PICS = ('photos', 'node_pictures.json'); MISSING = ('photos', 'node_missing.json'); TRIED = ('photos', 'node_tried.json'); DIR = ('photos', 'nodes')
ID_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


def node_id(wiki):
    """The node id of a concept title: the slug the species ids use (build/species.py slug)."""
    return re.sub(r'[^a-z0-9]+', '-', str(wiki or '').lower()).strip('-')


def concepts(root='.'):
    """{node id: wiki title} of every node concept the places show (a node with a category and a wiki title, once a place file is joined with the species and node rows, as the build does it)."""
    import glob
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build'))
    import species
    tab = species.table(root); out = {}
    for f in sorted(glob.glob(os.path.join(root, 'data', 'places', '*.json'))):
        try:
            with open(f, encoding='utf-8') as fh: eco = json.load(fh)
        except (OSError, ValueError): continue
        if not isinstance(eco, dict) or not isinstance(eco.get('nodes'), list): continue   # not a place file (or a damaged one: the validator says so)
        for n in species.join(eco, tab)['nodes']:
            if n.get('cat') and n.get('wiki'): out.setdefault(node_id(n['wiki']), n['wiki'])
    return out


class NodePhotos(CreditRepair):
    """The ledger photos/node_tried.json {node id: {source: date}} is the same as the other kinds' (#1183). When the file does not exist (every checkout before the first commit) it is read as the
    migration: each missing record gives wikipedia and commons its date, because one run tried both. The file is then written by the next commit(); the app and the build never read it."""
    def lists(self): return [('node_pictures.json', self.pics), ('node_missing.json', self.miss_), ('node_tried.json', self.tried)]

    def __init__(self, root='.'):
        self.root = root; p = lambda parts: os.path.join(root, *parts)
        self.pics = _read(p(PICS)); self.miss_ = _read(p(MISSING)); self.tried = _read(p(TRIED)); self._write = {}; self._delete = []
        if not os.path.exists(p(TRIED)):   # the migration: the hold of a source was read from the missing record's date until now
            for nid, e in self.miss_.items():
                d = str(e.get('checkedAt', ''))[:10]
                if d: self.tried[nid] = {'wikipedia': d, 'commons': d}

    def _path(self, name): return os.path.join(self.root, *DIR, name)

    def has(self, nid): return nid in self.pics
    def is_missing(self, nid): return nid in self.miss_

    def put(self, nid, entry, webp, now=None):
        """Store the picture of this concept. The file name is the first 12 hex digits of the sha256; the concept leaves missing.json."""
        if not ID_RE.match(nid or ''): raise ValueError('%r is not a node id (a slug of the concept title)' % nid)
        entry = dict(entry); entry['a'] = ac.clean_author(entry.get('a')) or 'Unknown author'
        if author_missing(entry): raise ValueError('picture for %r is %s with no named author: refused' % (nid, entry.get('l')))
        entry['f'] = hashlib.sha256(webp).hexdigest()[:12] + '.webp'
        stamp = (now or pr._utcnow()).isoformat()
        entry.setdefault('built', stamp); entry['checkedAt'] = stamp
        old = self.pics.get(nid)
        if old and old.get('f') != entry['f']: self._delete.append(self._path(old['f']))
        self.pics[nid] = entry; self._write[self._path(entry['f'])] = webp; self.miss_.pop(nid, None); self.tried.pop(nid, None)

    def remove(self, nid, status, now=None):
        """Remove a concept's picture and record why (status as in photo_registry)."""
        if nid in self.pics: self._delete.append(self._path(self.pics.pop(nid)['f']))
        self.tried.pop(nid, None); self.miss(nid, status, now=now)

    def miss(self, nid, status, source='', attempts=None, now=None):
        if nid in self.pics: raise ValueError('%r has a stored picture: use remove() to drop it first' % nid)
        prev = self.miss_.get(nid, {}); n = attempts if attempts is not None else int(prev.get('attempts', 0)) + 1
        e = pr.negative_entry(status, n, now); self.miss_[nid] = e
        if source: self.tried.setdefault(nid, {})[source] = e['checkedAt'][:10]

    def note_tried(self, nid, source, now=None):
        """Record in the ledger only that `source` looked for this concept and found none: node_missing.json is not touched (a later source may still try)."""
        if nid in self.pics: raise ValueError('%r has a stored picture: nothing to note' % nid)
        self.tried.setdefault(nid, {})[source] = (now or pr._utcnow()).isoformat()[:10]

    def commit(self):
        for path, data in self._write.items(): _write_bytes(path, data)
        for parts, obj in ((PICS, self.pics), (MISSING, self.miss_), (TRIED, self.tried)): _write_json(os.path.join(self.root, *parts), obj, indent=0 if parts != TRIED else None)
        keep = {self._path(e['f']) for e in self.pics.values()}
        for path in self._delete:
            if path not in keep and path not in self._write:   # a file another concept still shows stays
                try: os.remove(path)
                except OSError: pass
        self._write = {}; self._delete = []

    def check(self):
        """Problems between the files and the lists. Empty means consistent."""
        errs = self.ledger_errors('node_tried.json'); d = os.path.join(self.root, *DIR); files = {f for f in os.listdir(d) if f.endswith('.webp')} if os.path.isdir(d) else set()
        for nid, e in sorted(self.pics.items()):
            if not ID_RE.match(nid): errs.append('%s: not a node id' % nid)
            if not e.get('f'): errs.append('%s: no file name' % nid)
            elif e['f'] not in files: errs.append('%s: listed in node_pictures.json but photos/nodes/%s is missing' % (nid, e['f']))
            if nid in self.miss_: errs.append('%s: has a picture and is also in node_missing.json' % nid)
            if author_missing(e): errs.append('%s: %s picture with no named author' % (nid, e.get('l')))
            if not e.get('checkedAt'): errs.append('%s: no checkedAt' % nid)
        for f in sorted(files - {e.get('f') for e in self.pics.values()}): errs.append('photos/nodes/%s is not listed in node_pictures.json' % f)
        return errs

    def repair(self):
        """Remove files no list mentions and list rows whose file is gone. Returns what it removed."""
        removed = []; d = os.path.join(self.root, *DIR); listed = {e.get('f') for e in self.pics.values()}
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.endswith('.webp') and f not in listed: os.remove(os.path.join(d, f)); removed.append('photos/nodes/' + f)
        for nid in [n for n, e in self.pics.items() if not os.path.exists(self._path(e.get('f') or '-'))]: del self.pics[nid]; removed.append('node_pictures.json:' + nid)
        if removed: self.commit()
        return removed


def seed_tried(root='.'):
    """The one-time migration of the ledger (#1183): when photos/node_tried.json does not exist, write it (NodePhotos reads the missing records into it on load). Returns the number of ledger entries written, 0 when the file exists."""
    if os.path.exists(os.path.join(root, *TRIED)): return 0
    w = NodePhotos(root); w.commit(); return len(w.tried)


if __name__ == '__main__':
    if sys.argv[1:] == ['seed']: print('node_tried.json: %d entries written' % seed_tried('.'))
    else: print('usage: python3 lib/node_photos.py seed   (run from the repository root)')
