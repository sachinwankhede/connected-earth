#!/usr/bin/env python3
"""story_batch.py: turn the judged story drafts into ONE batch for a data pull request (#779 step c).
Usage: story_batch.py <drafts dir> [--data data/places] [--n 25] [--body batch-body.md]
  <drafts dir>  a checkout of the `gemini-stories` branch (the writer's <id>.json, the judge's judge/<id>.json and judge/rejected/<id>.json)
What goes in the batch: the first N drafts (id order) that the judge PASSED (judge/<id>.json exists, no judge/rejected/<id>.json), whose place file exists and has no story yet. A draft the judge flagged, one
the judge has not read yet, and one the checks rejected stay out and are only counted and listed in the pull request body. The chosen stories are written into the place files with promote_stories.promote (the
diff is the review: merging is the approval) and the body is written to --body: counts, the table of what is in, what the judge flagged and why, the sources and licences line, and the 10-item spot check
(`docs/PROMOTION.md`): ten evenly spaced stories to read against their research text. Exit 3 and no change when nothing qualifies. Nothing is fetched and no model is called."""
import os, sys, json, glob, tempfile, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import promote_stories

def load(d, sub=''):
    out = {}
    for f in sorted(glob.glob(os.path.join(d, sub, '*.json'))):
        with open(f, encoding='utf-8') as h: x = json.load(h)
        if 'id' in x: out[x['id']] = x
    return out

def select(drafts_dir, data_dir, n):
    """-> (chosen drafts in id order, flagged {id: record}, counts). A draft counts as passed only when the judge's pass file exists and its flag file does not."""
    drafts = {i: d for i, d in load(drafts_dir).items() if 'story' in d and 'matters' in d}
    passed, flagged = load(drafts_dir, 'judge'), load(drafts_dir, os.path.join('judge', 'rejected'))
    rejected = load(drafts_dir, 'rejected'); chosen = []; has_story = missing = 0
    for pid in sorted(drafts):
        if pid not in passed or pid in flagged: continue
        f = os.path.join(data_dir, pid + '.json')
        if not os.path.exists(f): missing += 1; continue
        with open(f, encoding='utf-8') as h: p = json.load(h)
        if p.get('story') or p.get('matters'): has_story += 1; continue
        chosen.append(dict(drafts[pid], judge=passed[pid]))
    unjudged = sorted(i for i in drafts if i not in passed and i not in flagged)
    return chosen[:n], flagged, dict(drafts=len(drafts), passed=len(passed), flagged=len(flagged), rejected=len(rejected), unjudged=len(unjudged), qualified=len(chosen), has_story=has_story, missing_place=missing)

def spot_ids(chosen, k=10):
    """k evenly spaced items (all of them when there are fewer)."""
    if len(chosen) <= k: return [d['id'] for d in chosen]
    return [chosen[int(i * len(chosen) / k)]['id'] for i in range(k)]

def words(s): return len(s.split())

def body(chosen, flagged, c):
    models = sorted({d.get('model', '') for d in chosen if d.get('model')}); jmodels = sorted({d['judge'].get('model', '') for d in chosen if d['judge'].get('model')})
    L = ['Part of #779 (story pipeline). Merging this pull request is the approval of these stories: the diff is the review.', '',
         '**%d stories** are in this batch (of %d that qualify). %d drafts so far: %d judge-passed, %d flagged by the judge (not here), %d rejected by the checks, %d not judged yet.' % (len(chosen), c['qualified'], c['drafts'], c['passed'], c['flagged'], c['rejected'], c['unjudged']), '',
         '## Sources and licences',
         'Each story and "why it matters" line was drafted by Gemini (%s) from the place\'s research text on the `research` branch (Wikipedia text, CC BY-SA 4.0, and the other hosts in `lib/allowed_sources.json`), and only from it: the checks refuse a number or a name that is not in that text, a story over 60 words and a why line over 40. A second model (%s) then read each story against the same text and passed it; the ones it flagged are not in this pull request. The judge and the writer share the research text, so an error in the source passes both.' % (', '.join(models) or 'n/a', ', '.join(jmodels) or 'n/a'), '',
         '## In this batch', '', '| place | id | story words | why words | writer | judge |', '|---|---|---|---|---|---|']
    L += ['| %s | `%s` | %d | %d | %s | %s |' % (d.get('name', d['id']), d['id'], words(d['story']), words(d['matters']), d.get('model', ''), d['judge'].get('model', '')) for d in chosen]
    L += ['', '## Flagged by the judge (not in this batch)']
    L += ['- `%s` %s: %s' % (i, r.get('name', ''), r.get('rejected', '')) for i, r in sorted(flagged.items())] or ['None.']
    ids = spot_ids(chosen); by = {d['id']: d for d in chosen}
    L += ['', '## 10-item spot check (`docs/PROMOTION.md`)', 'Read each against its research text (`research/<id>.md` on the `research` branch). More than one obviously wrong means the batch does not ship.', '']
    for i in ids: L += ['- [ ] **%s** (`%s`): %s %s' % (by[i].get('name', i), i, by[i]['story'], by[i]['matters']), '']
    return '\n'.join(L) + '\n'

def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('--'): print(__doc__); sys.exit(2)
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    data, n, out = opt('--data', 'data/places'), int(opt('--n', '25')), opt('--body', 'batch-body.md')
    chosen, flagged, c = select(a[0], data, n); print(json.dumps(c))
    if not chosen: print('nothing qualifies'); sys.exit(3)
    tmp = tempfile.mkdtemp()
    try:
        for d in chosen: json.dump({k: d[k] for k in ('id', 'story', 'matters')}, open(os.path.join(tmp, d['id'] + '.json'), 'w'), ensure_ascii=False)
        done, skipped = promote_stories.promote(tmp, data)
    finally: shutil.rmtree(tmp, ignore_errors=True)
    if skipped: print('skipped by promote:', skipped)
    chosen = [d for d in chosen if d['id'] in done]; open(out, 'w', encoding='utf-8').write(body(chosen, flagged, c))
    print('%d stories written into %s; body in %s' % (len(done), data, out))

if __name__ == '__main__': main()
