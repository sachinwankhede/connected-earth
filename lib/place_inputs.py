#!/usr/bin/env python3
"""place_inputs.py: what a place's derived data was built from (#887 step 5b; docs/DATA-PLAN.md principle 4 "derived data records its inputs").

One sidecar, `data/place_inputs.json`, keyed by place id, written only here (like data/outline_records.json): {id: {"web": {...}, "story": {...}}}.
  web    the food web as the place file holds it: `nodes` (hash of the sorted node id and species id pairs), `links` (hash of the sorted eating links), `n` and `l` (their counts), `at` (when it was stamped).
         stamp() is called by `build/species.py pack` at the end, so a place whose nodes or links changed without pack having run (a hand edit, a job that skipped it) no longer matches its record: check() fails.
  story  the research text the story and "why it matters" were written from: `research` (hash of research/<id>.md on the `research` branch), `at`, and `baseline` true when the hash is of the text as it was
         when the record was made for an older story (jobs/stampstories.py), not of the text the model read. Written by jobs/promote_stories.py for new stories.
A place with a story and no `story` record is a warning until every older story has its baseline, then an error (STORY_RECORD_IS_ERROR)."""
import datetime, hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
FILE = ('data', 'place_inputs.json'); SKIP = ('links.json', 'order.json', 'species.json', 'bounds.json')
STORY_RECORD_IS_ERROR = False


def digest(obj):
    """A short stable hash of any JSON value."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()[:12]


def text_hash(s):
    """A short hash of a text (the research text a story was written from), line ends and outer space ignored."""
    return hashlib.sha256('\n'.join((s or '').replace('\r\n', '\n').strip().split('\n')).encode('utf-8')).hexdigest()[:12]


def web_inputs(place):
    """The food web of a place file, as {nodes, links, n, l}: node id with species id, and the eating links."""
    nodes = sorted([n.get('id'), n.get('sp') or ''] for n in (place.get('nodes') or []) if isinstance(n, dict))
    links = sorted([str(x[0]), str(x[1])] for x in (place.get('raw') or []) if isinstance(x, (list, tuple)) and len(x) >= 2)
    return {'nodes': digest(nodes), 'links': digest(links), 'n': len(nodes), 'l': len(links)}


def places(root):
    d = os.path.join(root, 'data', 'places')
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith('.json') and f not in SKIP:
            try:
                with open(os.path.join(d, f), encoding='utf-8') as h: e = json.load(h)
            except (OSError, ValueError): continue
            if isinstance(e, dict) and e.get('nodes') is not None: yield f[:-5], e


class PlaceInputs:
    def __init__(self, root=ROOT):
        self.root = root; p = os.path.join(root, *FILE)
        try:
            with open(p, encoding='utf-8') as h: self.recs = json.load(h)
        except (OSError, ValueError): self.recs = {}

    def stamp_webs(self, now=None):
        """Record the web of every place whose nodes or links differ from the record (or have none); returns the ids changed. The date is when it changed, not when pack last ran."""
        today = (now or datetime.date.today()).isoformat(); changed = []; seen = set()
        for pid, e in places(self.root):
            seen.add(pid); w = web_inputs(e); old = (self.recs.get(pid) or {}).get('web') or {}
            if {k: old.get(k) for k in w} != w: self.recs.setdefault(pid, {})['web'] = dict(w, at=today); changed.append(pid)
        for pid in [i for i in self.recs if i not in seen]: self.recs.pop(pid)   # a place that no longer exists leaves no record
        return changed

    def set_story(self, pid, research_text, baseline=False, now=None):
        self.recs.setdefault(pid, {})['story'] = dict({'research': text_hash(research_text), 'at': (now or datetime.date.today()).isoformat()}, **({'baseline': True} if baseline else {}))

    def commit(self):
        p = os.path.join(self.root, *FILE); os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8') as h:
            h.write('{\n' + ',\n'.join(json.dumps(k, ensure_ascii=False) + ':' + json.dumps(self.recs[k], ensure_ascii=False, sort_keys=True, separators=(',', ':')) for k in sorted(self.recs)) + '\n}\n')

    def stale_webs(self):
        """(place id, why) for each place whose food web no longer matches its record; 'no record' when it has none. Sorted."""
        out = []
        for pid, e in places(self.root):
            old = (self.recs.get(pid) or {}).get('web')
            if not old: out.append((pid, 'no record')); continue
            w = web_inputs(e)
            if {k: old.get(k) for k in w} != w: out.append((pid, 'nodes changed' if old.get('nodes') != w['nodes'] else 'links changed'))
        return out

    def check(self):
        """(errors, warnings). Errors: a food web that no longer matches its record, a record that is not a web or story record, a record for no place. Warnings: a story with no story record yet."""
        errs, warns = [], []
        if not os.path.exists(os.path.join(self.root, *FILE)): return errs, warns   # nothing to check before the file exists
        ids = {pid for pid, _ in places(self.root)}
        for pid, why in self.stale_webs(): errs.append('%s: food web %s since its record in data/place_inputs.json (run: python3 build/species.py pack)' % (pid, why))
        for pid, r in sorted(self.recs.items()):
            if pid not in ids: errs.append('data/place_inputs.json: %s is not a place' % pid); continue
            w = r.get('web')
            if w is not None and not {'nodes', 'links', 'n', 'l', 'at'} <= set(w): errs.append('%s: web record is incomplete' % pid)
            s = r.get('story')
            if s is not None and not {'research', 'at'} <= set(s): errs.append('%s: story record is incomplete' % pid)
        nostory = []
        for pid, e in places(self.root):
            if e.get('story') and not (self.recs.get(pid) or {}).get('story'): nostory.append(pid)
        if nostory: (errs if STORY_RECORD_IS_ERROR else warns).append('%d place(s) have a story and no record of the research text it came from, first %s (jobs/stampstories.py)' % (len(nostory), ', '.join(nostory[:5])))
        return errs, warns


def stamp(root=ROOT):
    r = PlaceInputs(root); before = json.dumps(r.recs, sort_keys=True); changed = r.stamp_webs()
    if json.dumps(r.recs, sort_keys=True) != before or not os.path.exists(os.path.join(root, *FILE)): r.commit()
    return changed


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'check'
    if cmd == 'stamp': print('%d food web record(s) written' % len(stamp()))
    else:
        e, w = PlaceInputs().check(); print('\n'.join(['error ' + x for x in e] + ['warn  ' + x for x in w]) or 'ok'); sys.exit(1 if e else 0)
