#!/usr/bin/env python3
"""journey_photos.py: the one writer for journey cover pictures (docs/DATA-PLAN.md, "Journey pictures: by journey id"; owner, 15 Nov: "Own").

A journey cover is its own picture row, keyed by the JOURNEY ID (the file name of data/journeys/<id>.json), never by a Wikipedia title: the file `photos/journeys/<id>.webp` (96 px), its row in
`photos/journey_pictures.json` ({f, a, l, lu, p, wiki, page, u, src}: credit, the title it was found under, the source path the larger copy is made from), its larger copy
`photos/journeys-lg/<id>.webp` (400 px) with its row in `photos/journey_large.json`, and the journey's absence from `photos/journey_missing.json` and from the retry ledger
`photos/journey_tried.json`. The ends of a journey are not stored here: they use the place pictures by place id.

Jobs call put / put_large / remove / miss / note_tried and then commit(); none of them writes those files itself. commit() writes every file through a temporary name and os.replace,
files first and lists last, deletions after that, so a killed job leaves at worst a file no list mentions (check() finds it, repair() removes it), never a list row without its file and never a
larger copy of a picture that is gone. The same methods and the same author rule as lib/place_photos.py (author_missing, lib/author_clean.py). A journey's own file name is `<id>.webp` in both folders
(a journey id is unique, so no content hash is needed)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photo_registry as pr
import author_clean as ac
from place_photos import author_missing, _read, _write_bytes, _write_json   # one author rule and one atomic write for all writers

PICS = ('photos', 'journey_pictures.json'); MISSING = ('photos', 'journey_missing.json'); LARGE = ('photos', 'journey_large.json'); TRIED = ('photos', 'journey_tried.json')
SMALL_DIR = ('photos', 'journeys'); LARGE_DIR = ('photos', 'journeys-lg')


class JourneyPhotos:
    def __init__(self, root='.'):
        self.root = root; p = lambda parts: os.path.join(root, *parts)
        self.pics = _read(p(PICS)); self.miss_ = _read(p(MISSING)); self.large = _read(p(LARGE)); self.tried = _read(p(TRIED))
        self._write = {}; self._delete = []   # path -> bytes to write; paths to delete after the lists are written

    def _path(self, parts, name): return os.path.join(self.root, *parts, name)

    def _stored(self, jid):
        try:
            with open(self._path(SMALL_DIR, jid + '.webp'), 'rb') as f: return f.read()
        except OSError: return None

    # --- reading
    def has(self, jid): return jid in self.pics
    def is_missing(self, jid): return jid in self.miss_
    def has_large(self, jid): return jid in self.large

    # --- writing (nothing touches the disk until commit)
    def put(self, jid, entry, webp):
        """Store the 96 px cover of this journey. The file name is always <id>.webp. The journey leaves missing.json and the ledger; a larger copy of a
        different picture is dropped (the job makes a new one)."""
        entry = dict(entry); entry['a'] = ac.clean_author(entry.get('a')) or 'Unknown author'   # one stored form for the author (lib/author_clean.py)
        if author_missing(entry): raise ValueError('picture for %r is %s with no named author: refused' % (jid, entry.get('l')))
        entry['f'] = jid + '.webp'
        if jid in self.pics and (self._write.get(self._path(SMALL_DIR, entry['f'])) or self._stored(jid)) != webp: self._drop_large(jid)
        self.pics[jid] = entry; self._write[self._path(SMALL_DIR, entry['f'])] = webp
        self.miss_.pop(jid, None); self.tried.pop(jid, None)

    def put_large(self, jid, webp):
        """The larger copy of a stored cover. Refused when the journey has no stored picture."""
        if jid not in self.pics: raise ValueError('no stored journey picture for %r: a larger copy needs one' % jid)
        name = jid + '.webp'; self.large[jid] = name; self._write[self._path(LARGE_DIR, name)] = webp

    def remove(self, jid, status, source='', now=None):
        """Remove a journey's picture with everything that depends on it, and record why (status is one of photo_registry.PERMANENT or a transient word)."""
        if jid in self.pics: self._delete.append(self._path(SMALL_DIR, self.pics.pop(jid).get('f') or jid + '.webp'))
        self._write.pop(self._path(SMALL_DIR, jid + '.webp'), None); self._drop_large(jid)
        self.miss(jid, status, source, now=now)

    def miss(self, jid, status, source='', attempts=None, now=None):
        """Record that no usable picture was found for this journey. One retry policy (photo_registry.negative_entry) for every source; the ledger notes who tried."""
        if jid in self.pics: raise ValueError('%r has a stored picture: use remove() to drop it first' % jid)
        prev = self.miss_.get(jid, {}); n = attempts if attempts is not None else int(prev.get('attempts', 0)) + 1
        e = pr.negative_entry(status, n, now); self.miss_[jid] = e
        if source: self.tried.setdefault(jid, {})[source] = e['checkedAt'][:10]

    def note_tried(self, jid, source, now=None):
        """Record in the ledger only that `source` looked for this journey's picture and found none: missing.json is not touched (a later source may still try)."""
        if jid in self.pics: raise ValueError('%r has a stored picture: nothing to note' % jid)
        self.tried.setdefault(jid, {})[source] = (now or pr._utcnow()).isoformat()[:10]

    def _drop_large(self, jid):
        name = self.large.pop(jid, None)
        if name: self._delete.append(self._path(LARGE_DIR, name))
        self._write.pop(self._path(LARGE_DIR, jid + '.webp'), None)

    def commit(self):
        """Files first, then the lists, then deletions. Idempotent."""
        for path, data in self._write.items(): _write_bytes(path, data)
        for parts, obj in ((PICS, self.pics), (MISSING, self.miss_), (LARGE, self.large), (TRIED, self.tried)):
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
        files = {f for f in os.listdir(sd) if f.endswith('.webp')} if os.path.isdir(sd) else set()
        lfiles = set(os.listdir(ld)) if os.path.isdir(ld) else set()
        for jid, e in sorted(self.pics.items()):
            if e.get('f') != jid + '.webp': errs.append('%s: file name %r is not %s.webp' % (jid, e.get('f'), jid))
            elif e['f'] not in files: errs.append('%s: listed in journey_pictures.json but %s is missing' % (jid, e['f']))
            if jid in self.miss_: errs.append('%s: has a picture and is also in journey_missing.json' % jid)
            if author_missing(e): errs.append('%s: %s picture with no named author' % (jid, e.get('l')))
        for f in sorted(files - {e.get('f') for e in self.pics.values()}): errs.append('photos/journeys/%s is not listed in journey_pictures.json' % f)
        for jid, name in sorted(self.large.items()):
            if jid not in self.pics: errs.append('%s: larger copy but no stored picture' % jid)
            elif name != jid + '.webp': errs.append('%s: larger copy name %r is not %s.webp' % (jid, name, jid))
            elif name not in lfiles: errs.append('%s: listed in journey_large.json but %s is missing' % (jid, name))
        for f in sorted(lfiles - set(self.large.values())): errs.append('photos/journeys-lg/%s is not listed in journey_large.json' % f)
        return errs

    def dirty_authors(self):
        """Journey ids whose stored author clean_author would change (an email, a talk stamp, a web address, an uploader sentence)."""
        return sorted(jid for jid, e in self.pics.items() if ac.is_dirty(e.get('a')))

    def repair(self):
        """Remove files no list mentions and list rows whose file is gone (what a killed job can leave). Returns what it removed."""
        removed = []; sd = os.path.join(self.root, *SMALL_DIR); ld = os.path.join(self.root, *LARGE_DIR)
        for jid in [j for j, e in self.pics.items() if not os.path.exists(os.path.join(sd, e.get('f') or '-'))]: del self.pics[jid]; removed.append('journey_pictures.json:' + jid)   # rows first, so a larger copy of a gone picture goes too
        for jid in [j for j, n in self.large.items() if j not in self.pics or not os.path.exists(os.path.join(ld, n))]: del self.large[jid]; removed.append('journey_large.json:' + jid)
        for f in sorted(os.listdir(sd)) if os.path.isdir(sd) else []:
            if f.endswith('.webp') and f not in {e.get('f') for e in self.pics.values()}: os.remove(os.path.join(sd, f)); removed.append('photos/journeys/' + f)
        for f in sorted(os.listdir(ld)) if os.path.isdir(ld) else []:
            if f not in set(self.large.values()): os.remove(os.path.join(ld, f)); removed.append('photos/journeys-lg/' + f)
        if removed: self.commit()
        return removed
