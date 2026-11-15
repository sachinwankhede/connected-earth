#!/usr/bin/env python3
"""place_photos.py: the one writer for place pictures (docs/DATA-PLAN.md, steps 3 and 4; #887).

A place picture is several things that must agree: the file `photos/places/<id>.jpg`, its row in `photos/places/places.json`, its larger copy
`photos/places-lg/<id>.webp` with its row in `photos/places_large.json`, and the place's absence from `photos/places/missing.json` and from the retry ledger
`photos/places_tried.json`. Everything here is keyed by the PLACE ID, never by a Wikipedia title (two places can share a title).

Jobs call put / put_large / remove / miss and then commit(); none of them writes those files itself. commit() writes every file through a temporary name
and os.replace, files first and lists last, deletions after that, so a job that is killed leaves at worst a file no list mentions (check() finds it, repair() removes
it), never a list row without its file, and never a larger copy of a picture that is gone.

The place pictures are keyed by place id (migration #906, 15 Nov); each row carries the Wikipedia title it was keyed by as `wiki`."""
import datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photo_registry as pr

PLACES = ('photos', 'places', 'places.json'); MISSING = ('photos', 'places', 'missing.json')
LARGE = ('photos', 'places_large.json'); TRIED = ('photos', 'places_tried.json')
SMALL_DIR = ('photos', 'places'); LARGE_DIR = ('photos', 'places-lg')


def _read(path):
    if not os.path.exists(path): return {}
    with open(path) as f: return json.load(f)

def _write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True); tmp = path + '.tmp'
    with open(tmp, 'wb') as f: f.write(data); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def _write_json(path, obj, indent=0):
    os.makedirs(os.path.dirname(path), exist_ok=True); tmp = path + '.tmp'
    with open(tmp, 'w') as f: json.dump(obj, f, ensure_ascii=False, indent=indent, sort_keys=True); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


class PlacePhotos:
    def __init__(self, root='.'):
        self.root = root; p = lambda parts: os.path.join(root, *parts)
        self.pics = _read(p(PLACES)); self.miss_ = _read(p(MISSING)); self.large = _read(p(LARGE)); self.tried = _read(p(TRIED))
        self._write = {}; self._delete = []   # path -> bytes to write; paths to delete after the lists are written

    def _path(self, parts, name): return os.path.join(self.root, *parts, name)

    # --- reading
    def has(self, pid): return pid in self.pics
    def is_missing(self, pid): return pid in self.miss_
    def has_large(self, pid): return pid in self.large

    # --- writing (nothing touches the disk until commit)
    def put(self, pid, entry, jpg):
        """Store a picture for this place. The file name is always <id>.jpg. The place leaves missing.json and the ledger; a larger copy of a
        different picture is dropped (placepictures makes a new one)."""
        entry = dict(entry); entry['f'] = pid + '.jpg'
        if pid in self.pics and self.pics[pid].get('sha256') != entry.get('sha256'): self._drop_large(pid)
        self.pics[pid] = entry; self._write[self._path(SMALL_DIR, entry['f'])] = jpg
        self.miss_.pop(pid, None); self.tried.pop(pid, None)

    def put_large(self, pid, webp):
        """The larger copy of a stored picture. Refused when the place has no stored picture."""
        if pid not in self.pics: raise ValueError('no stored place picture for %r: a larger copy needs one' % pid)
        name = pid + '.webp'; self.large[pid] = name; self._write[self._path(LARGE_DIR, name)] = webp

    def remove(self, pid, status, source='', now=None):
        """Remove a place's picture with everything that depends on it, and record why (status is one of photo_registry.PERMANENT or a transient word)."""
        if pid in self.pics: self._delete.append(self._path(SMALL_DIR, self.pics.pop(pid).get('f') or pid + '.jpg'))
        self._write.pop(self._path(SMALL_DIR, pid + '.jpg'), None); self._drop_large(pid)
        self.miss(pid, status, source, now=now)

    def miss(self, pid, status, source='', attempts=None, now=None):
        """Record that no usable picture was found for this place. One retry policy (photo_registry.negative_entry) for every source; the ledger notes who tried."""
        if pid in self.pics: raise ValueError('%r has a stored picture: use remove() to drop it first' % pid)
        prev = self.miss_.get(pid, {}); n = attempts if attempts is not None else int(prev.get('attempts', 0)) + 1
        e = pr.negative_entry(status, n, now); self.miss_[pid] = e
        if source: self.tried.setdefault(pid, {})[source] = e['checkedAt'][:10]

    def note_tried(self, pid, source, now=None):
        """Record in the ledger only that `source` looked for this place's picture and found none: missing.json is not touched (a later source may still try the place).
        The retry hold of a source is read from this date (jobs/placepictures.py)."""
        if pid in self.pics: raise ValueError('%r has a stored picture: nothing to note' % pid)
        self.tried.setdefault(pid, {})[source] = (now or pr._utcnow()).isoformat()[:10]

    def _drop_large(self, pid):
        name = self.large.pop(pid, None)
        if name: self._delete.append(self._path(LARGE_DIR, name))
        self._write.pop(self._path(LARGE_DIR, pid + '.webp'), None)

    def commit(self):
        """Files first, then the lists, then deletions. Idempotent."""
        for path, data in self._write.items(): _write_bytes(path, data)
        for parts, obj in ((PLACES, self.pics), (MISSING, self.miss_), (LARGE, self.large), (TRIED, self.tried)):
            _write_json(os.path.join(self.root, *parts), obj, indent=0 if parts != TRIED else None)
        for path in self._delete:
            if not any(path == w for w in self._write):
                try: os.remove(path)
                except OSError: pass
        self._write = {}; self._delete = []

    # --- consistency
    def check(self):
        """Problems between the files and the lists. Empty means consistent."""
        errs = []; sd = os.path.join(self.root, *SMALL_DIR); ld = os.path.join(self.root, *LARGE_DIR)
        files = {f for f in os.listdir(sd) if f.endswith('.jpg')} if os.path.isdir(sd) else set()
        lfiles = set(os.listdir(ld)) if os.path.isdir(ld) else set()
        for pid, e in sorted(self.pics.items()):
            if e.get('f') != pid + '.jpg': errs.append('%s: file name %r is not %s.jpg' % (pid, e.get('f'), pid))
            elif e['f'] not in files: errs.append('%s: listed in places.json but %s is missing' % (pid, e['f']))
            if pid in self.miss_: errs.append('%s: has a picture and is also in missing.json' % pid)
        for f in sorted(files - {e.get('f') for e in self.pics.values()}): errs.append('photos/places/%s is not listed in places.json' % f)
        for pid, name in sorted(self.large.items()):
            if pid not in self.pics: errs.append('%s: larger copy but no stored picture' % pid)
            elif name != pid + '.webp': errs.append('%s: larger copy name %r is not %s.webp' % (pid, name, pid))
            elif name not in lfiles: errs.append('%s: listed in places_large.json but %s is missing' % (pid, name))
        for f in sorted(lfiles - set(self.large.values())): errs.append('photos/places-lg/%s is not listed in places_large.json' % f)
        return errs

    def repair(self):
        """Remove files no list mentions and list rows whose file is gone (what a killed job can leave). Returns what it removed."""
        removed = []; sd = os.path.join(self.root, *SMALL_DIR); ld = os.path.join(self.root, *LARGE_DIR)
        for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
            if f.endswith('.jpg') and f not in {e.get('f') for e in self.pics.values()}: os.remove(os.path.join(sd, f)); removed.append('photos/places/' + f)
        for f in sorted(os.listdir(ld)) if os.path.isdir(ld) else []:
            if f not in set(self.large.values()): os.remove(os.path.join(ld, f)); removed.append('photos/places-lg/' + f)
        for pid in [p for p, n in self.large.items() if p not in self.pics or not os.path.exists(os.path.join(ld, n))]: del self.large[pid]; removed.append('places_large.json:' + pid)
        for pid in [p for p, e in self.pics.items() if not os.path.exists(os.path.join(sd, e.get('f', '')))]: del self.pics[pid]; removed.append('places.json:' + pid)
        if removed: self.commit()
        return removed
