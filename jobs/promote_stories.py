#!/usr/bin/env python3
"""promote_stories.py: copy owner-approved Gemini story drafts into place files (#196).

Usage: promote_stories.py <drafts dir> [--data data/places]
Each draft is <id>.json with `story` and `matters`. A place that already has a story is left alone.
Prints one line per place and a total. Place files keep their compact JSON format.
"""
import json, os, sys


def promote(drafts, data):
    done, skipped = [], []
    for name in sorted(os.listdir(drafts)):
        if not name.endswith('.json'):
            continue
        d = json.load(open(os.path.join(drafts, name)))
        pid, story, why = d.get('id'), d.get('story'), d.get('matters')
        path = os.path.join(data, '%s.json' % pid)
        if not (pid and story and why and os.path.exists(path)):
            skipped.append(name)
            continue
        raw = open(path).read()
        p = json.loads(raw)
        if 'story' in p or 'matters' in p:
            skipped.append(name)
            continue
        p['story'], p['matters'] = story, why
        open(path, 'w').write(json.dumps(p, ensure_ascii=False) + ('\n' if raw.endswith('\n') else ''))
        done.append(pid)
    return done, skipped


if __name__ == '__main__':
    data = sys.argv[sys.argv.index('--data') + 1] if '--data' in sys.argv else 'data/places'
    done, skipped = promote(sys.argv[1], data)
    for i in done:
        print('promoted', i)
    print('%d promoted, %d skipped %s' % (len(done), len(skipped), skipped))
