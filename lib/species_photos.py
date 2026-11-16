#!/usr/bin/env python3
"""species_photos.py: the one writer for species pictures (docs/DATA-PLAN.md, "Species pictures"; #934).

A species picture is several things that must agree: the 96 px file `photos/species/<f>`, its row in `photos/species_pictures.json` (credit and source), the 192 px tile
copy `photos/species-md/<f>` and the 400 px copy `photos/species-lg/<f>` with their rows in `photos/species_medium.json` and `photos/species_large.json`, and the
species' absence from `photos/species_missing.json` and from the retry ledger `photos/species_tried.json`. Everything is keyed by the species `sid` (the Latin-name slug), never by a
Wikipedia title (151 titles are shared by 618 species rows; owner, 15 Nov: "Per sid"); each row carries the title it came from as `wiki`. The file name `<f>` is the first 12 hex digits of the sha256 of the 96 px picture, so two species that show the same picture
(a title shared by several species rows, such as Rain) share one file in each folder instead of each carrying a copy (the larger-copy budget has no room for 460 more); a file is deleted only when no
species row still points at it.

Jobs call put / put_medium / put_large / remove / miss / note_tried and then commit(); none of them writes those files itself. commit() writes every file through a temporary name and
os.replace, files first and lists last, deletions after that, so a killed job leaves at worst a file no list mentions (check() finds it, repair() removes it), never a list row without its file
and never a larger copy of a picture that is gone. The same methods as lib/place_photos.py, with one more copy size."""
import hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photo_registry as pr
import author_clean as ac
from place_photos import author_missing, _read, _write_bytes, _write_json   # one author rule and one atomic write for both writers

PICS = ('photos', 'species_pictures.json'); MISSING = ('photos', 'species_missing.json'); TRIED = ('photos', 'species_tried.json')
COPIES = {'small': (('photos', 'species'), ('photos', 'species_pictures.json')),
          'medium': (('photos', 'species-md'), ('photos', 'species_medium.json')),
          'large': (('photos', 'species-lg'), ('photos', 'species_large.json'))}
SMALL_DIR = COPIES['small'][0]; MEDIUM = COPIES['medium'][1]; LARGE = COPIES['large'][1]; MEDIUM_DIR = COPIES['medium'][0]; LARGE_DIR = COPIES['large'][0]


class SpeciesPhotos:
    def __init__(self, root='.'):
        self.root = root; p = lambda parts: os.path.join(root, *parts)
        self.pics = _read(p(PICS)); self.miss_ = _read(p(MISSING)); self.tried = _read(p(TRIED))
        self.medium = _read(p(MEDIUM)); self.large = _read(p(LARGE))
        self._write = {}; self._delete = []   # path -> bytes to write; paths to delete after the lists are written

    def _path(self, parts, name): return os.path.join(self.root, *parts, name)

    # --- reading
    def has(self, sid): return sid in self.pics
    def is_missing(self, sid): return sid in self.miss_
    def has_medium(self, sid): return sid in self.medium
    def has_large(self, sid): return sid in self.large

    # --- writing (nothing touches the disk until commit)
    def put(self, sid, entry, webp):
        """Store the 96 px picture of this species. The file name is always <sid>.webp. The species leaves missing.json and the ledger; the other copies of a
        different picture are dropped (the job makes new ones)."""
        entry = dict(entry); entry['a'] = ac.clean_author(entry.get('a')) or 'Unknown author'   # one stored form for the author (lib/author_clean.py)
        if author_missing(entry): raise ValueError('picture for %r is %s with no named author: refused' % (sid, entry.get('l')))
        entry['f'] = hashlib.sha256(webp).hexdigest()[:12] + '.webp'
        if sid in self.pics and self.pics[sid].get('f') != entry['f']: self._drop_copies(sid); self._delete.append(self._path(SMALL_DIR, self.pics[sid]['f']))
        self.pics[sid] = entry; self._write[self._path(SMALL_DIR, entry['f'])] = webp
        self.miss_.pop(sid, None); self.tried.pop(sid, None)

    def put_medium(self, sid, webp): self._put_copy(sid, 'medium', webp)
    def put_large(self, sid, webp): self._put_copy(sid, 'large', webp)

    def _put_copy(self, sid, which, webp):
        if sid not in self.pics: raise ValueError('no stored species picture for %r: a %s copy needs one' % (sid, which))
        name = self.pics[sid]['f']; (self.medium if which == 'medium' else self.large)[sid] = name
        self._write[self._path(COPIES[which][0], name)] = webp

    def remove(self, sid, status, source='', now=None):
        """Remove a species' picture with everything that depends on it, and record why (status is one of photo_registry.PERMANENT or a transient word)."""
        if sid in self.pics: self._delete.append(self._path(SMALL_DIR, self.pics.pop(sid)['f']))
        self._drop_copies(sid)
        self.miss(sid, status, source, now=now)

    def forget(self, sid):
        """Drop everything held for this id (picture, larger copies, missing entry, ledger) and record nothing: the id is no longer a species (#976: it became a node, whose picture is filed by node id)."""
        if sid in self.pics: self._delete.append(self._path(SMALL_DIR, self.pics.pop(sid)['f']))
        self._drop_copies(sid); self.miss_.pop(sid, None); self.tried.pop(sid, None)

    def miss(self, sid, status, source='', attempts=None, now=None):
        """Record that no usable picture was found for this species. One retry policy (photo_registry.negative_entry) for every source; the ledger notes who tried."""
        if sid in self.pics: raise ValueError('%r has a stored picture: use remove() to drop it first' % sid)
        prev = self.miss_.get(sid, {}); n = attempts if attempts is not None else int(prev.get('attempts', 0)) + 1
        e = pr.negative_entry(status, n, now); self.miss_[sid] = e
        if source: self.tried.setdefault(sid, {})[source] = e['checkedAt'][:10]

    def note_tried(self, sid, source, now=None):
        """Record in the ledger only that `source` looked for this species and found none: missing.json is not touched (a later source may still try)."""
        if sid in self.pics: raise ValueError('%r has a stored picture: nothing to note' % sid)
        self.tried.setdefault(sid, {})[source] = (now or pr._utcnow()).isoformat()[:10]

    def _drop_copies(self, sid):
        for which in ('medium', 'large'):
            d = self.medium if which == 'medium' else self.large; name = d.pop(sid, None)
            if name: self._delete.append(self._path(COPIES[which][0], name))

    def commit(self):
        """Files first, then the lists, then deletions. Idempotent."""
        for path, data in self._write.items(): _write_bytes(path, data)
        for parts, obj in ((PICS, self.pics), (MISSING, self.miss_), (MEDIUM, self.medium), (LARGE, self.large), (TRIED, self.tried)):
            _write_json(os.path.join(self.root, *parts), obj, indent=0 if parts != TRIED else None)
        keep = {self._path(SMALL_DIR, e['f']) for e in self.pics.values()} | {self._path(MEDIUM_DIR, n) for n in self.medium.values()} | {self._path(LARGE_DIR, n) for n in self.large.values()}
        for path in self._delete:
            if path not in keep and path not in self._write:   # a file another species still shows stays
                try: os.remove(path)
                except OSError: pass
        self._write = {}; self._delete = []

    # --- consistency
    def _files(self, parts):
        d = os.path.join(self.root, *parts); return set(os.listdir(d)) if os.path.isdir(d) else set()

    def check(self):
        """Problems between the files and the lists. Empty means consistent."""
        errs = []; sf = {f for f in self._files(SMALL_DIR) if f.endswith('.webp')}
        for sid, e in sorted(self.pics.items()):
            if not e.get('f'): errs.append('%s: no file name' % sid)
            elif e['f'] not in sf: errs.append('%s: listed in species_pictures.json but %s is missing' % (sid, e['f']))
            if sid in self.miss_: errs.append('%s: has a picture and is also in species_missing.json' % sid)
            if author_missing(e): errs.append('%s: %s picture with no named author' % (sid, e.get('l')))
        for f in sorted(sf - {e.get('f') for e in self.pics.values()}): errs.append('photos/species/%s is not listed in species_pictures.json' % f)
        for which, d in (('medium', self.medium), ('large', self.large)):
            files = self._files(COPIES[which][0]); label = os.path.join(*COPIES[which][1])[len('photos/'):]
            for sid, name in sorted(d.items()):
                if sid not in self.pics: errs.append('%s: %s copy but no stored picture' % (sid, which))
                elif name != self.pics[sid].get('f'): errs.append('%s: %s copy %r is not the file of its picture %r' % (sid, which, name, self.pics[sid].get('f')))
                elif name not in files: errs.append('%s: listed in %s but %s is missing' % (sid, label, name))
            for f in sorted(files - set(d.values())): errs.append('photos/%s/%s is not listed in %s' % (os.path.join(*COPIES[which][0])[len('photos/'):], f, label))
        return errs

    def dirty_authors(self):
        """Species ids whose stored author clean_author would change (an email, a talk stamp, a web address, an uploader sentence)."""
        return sorted(sid for sid, e in self.pics.items() if ac.is_dirty(e.get('a')))

    def repair(self):
        """Remove files no list mentions and list rows whose file is gone (what a killed job can leave). Returns what it removed."""
        removed = []
        for which, parts, d in (('small', SMALL_DIR, {e.get('f') for e in self.pics.values()}), ('medium', MEDIUM_DIR, set(self.medium.values())), ('large', LARGE_DIR, set(self.large.values()))):
            base = os.path.join(self.root, *parts)
            for f in sorted(os.listdir(base)) if os.path.isdir(base) else []:
                if f.endswith('.webp') and f not in d: os.remove(os.path.join(base, f)); removed.append(os.path.join(*parts, f))
        for which, parts, d in (('medium', MEDIUM_DIR, self.medium), ('large', LARGE_DIR, self.large)):
            for sid in [s for s, n in d.items() if s not in self.pics or not os.path.exists(os.path.join(self.root, *parts, n))]: del d[sid]; removed.append('%s:%s' % (which, sid))
        for sid in [s for s, e in self.pics.items() if not os.path.exists(os.path.join(self.root, *SMALL_DIR, e.get('f') or '-'))]: del self.pics[sid]; removed.append('species_pictures.json:' + sid)
        if removed: self.commit()
        return removed
