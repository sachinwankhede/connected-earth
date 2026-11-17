#!/usr/bin/env python3
"""outline_records.py: the one writer for the credit records of park outlines (#977, docs/DATA-PLAN.md "Credits").

An outline is the file `data/outlines/<place id>.json` ({n, r} and `s` for the two open sources); its credit record is a row in `data/outline_records.json`, keyed by place id, in the shared
credit shape: source, licence, licence link, page (where it was found), built (when we stored it), checkedAt (when the source was last confirmed). No author (optional for an outline: the OpenStreetMap
credit is one shared line in the app) and no `expires`. A place with no outline is in `data/outline_missing.json` (one retry policy, photo_registry.negative_entry).
commit() writes the outline file first, the lists last. check() finds a file without a record, a record without a file, a source that disagrees with the file's own `s`, and a licence that is not the source's."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import photo_registry as pr
from place_photos import _read, _write_json

RECORDS = ('data', 'outline_records.json'); MISSING = ('data', 'outline_missing.json'); DIR = ('data', 'outlines')
ID_RE = re.compile(r'^[a-z0-9]+$')
# source -> (licence, licence link). The links are the authoritative licence pages (hosts approved by the owner, 16 Nov); they are references on the record, never fetched.
# The outline file carries `s` for the two open sources; a file without `s` is PAD-US.
SOURCES = {
    'padus': ('Public domain (US Geological Survey)', 'https://www.usgs.gov/programs/gap-analysis-project/science/pad-us-data-overview'),
    'wikidata': ('CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/'),
    'osm': ('ODbL 1.0', 'https://opendatacommons.org/licenses/odbl/1-0/'),
}


def source_of(outline):
    """The source an outline file names (`s`), PAD-US when it names none."""
    return (outline or {}).get('s') or 'padus'


class OutlineRecords:
    def __init__(self, root='.'):
        self.root = root; p = lambda parts: os.path.join(root, *parts)
        self.recs = _read(p(RECORDS)); self.miss_ = _read(p(MISSING))

    def has(self, pid): return pid in self.recs
    def is_missing(self, pid): return pid in self.miss_

    def record(self, pid, source, page=None, now=None):
        """Set the credit record of this place's outline; `built` stays when the record is replaced."""
        if not ID_RE.match(pid or ''): raise ValueError('%r is not a place id' % pid)
        if source not in SOURCES: raise ValueError('unknown outline source %r' % source)
        licence, link = SOURCES[source]; stamp = (now or pr._utcnow()).isoformat()
        e = {'source': source, 'licence': licence, 'built': (self.recs.get(pid) or {}).get('built', stamp), 'checkedAt': stamp}
        if link: e['licence link'] = link
        if page: e['page'] = page
        self.recs[pid] = e; self.miss_.pop(pid, None)

    def miss(self, pid, status, attempts=None, now=None, inputs=None):
        if pid in self.recs: raise ValueError('%r has an outline record: drop it first' % pid)
        prev = self.miss_.get(pid, {}); n = attempts if attempts is not None else int(prev.get('attempts', 0)) + 1
        self.miss_[pid] = pr.negative_entry(status, n, now, inputs)

    def drop(self, pid, status='wrong', now=None):
        """Remove this place's outline file and credit record and put the place in the missing list, so the acquire job looks again after its delay (#1004: an outline that is the wrong unit).
        Remove the file first, the lists last, as commit() does."""
        f = os.path.join(self.root, *DIR, pid + '.json')
        if os.path.exists(f): os.remove(f)
        self.recs.pop(pid, None); self.miss_.pop(pid, None); self.miss(pid, status, now=now)

    def commit(self):
        for parts, obj in ((RECORDS, self.recs), (MISSING, self.miss_)): _write_json(os.path.join(self.root, *parts), obj, indent=0)

    def check(self):
        """Problems between the outline files and the records. Nothing to check until the record file exists."""
        errs = []; d = os.path.join(self.root, *DIR)
        if not os.path.exists(os.path.join(self.root, *RECORDS)): return errs
        files = {f[:-5] for f in os.listdir(d) if f.endswith('.json')} if os.path.isdir(d) else set()
        for pid, e in sorted(self.recs.items()):
            if pid not in files: errs.append('%s: has an outline record but data/outlines/%s.json is missing' % (pid, pid)); continue
            if e.get('source') not in SOURCES: errs.append('%s: unknown outline source %r' % (pid, e.get('source'))); continue
            if (e.get('licence'), e.get('licence link')) != SOURCES[e['source']]: errs.append('%s: licence is not the one for source %s' % (pid, e['source']))
            try:
                with open(os.path.join(d, pid + '.json')) as fh: s = source_of(json.load(fh))
            except (OSError, ValueError): errs.append('%s: outline file unreadable' % pid); continue
            if s != e['source']: errs.append('%s: record says %s but the file says %s' % (pid, e['source'], s))
            if not e.get('checkedAt') or not e.get('built'): errs.append('%s: record lacks built or checkedAt' % pid)
            if pid in self.miss_: errs.append('%s: has an outline and is also in outline_missing.json' % pid)
        for pid in sorted(files - set(self.recs)): errs.append('data/outlines/%s.json has no record in outline_records.json' % pid)
        return errs
