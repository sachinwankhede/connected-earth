#!/usr/bin/env python3
"""live_check.py URL BUILD_STAMP [--tries N] [--wait SECONDS]: check the published site after a deploy.
The live sw.js and index.html must carry the build stamp just built (sw.js holds it as V; the stamp is the first 8 hex digits of
the md5 of index.html), and a few key files must answer 200 with the right content. GitHub Pages can take a minute or two to switch
over, so it retries; exit 0 on the first full pass, exit 1 (with every problem listed) when the last try still fails."""
import hashlib, json, re, sys, time, urllib.request

# (path, what must hold). A callable gets the response bytes and returns an error string or None.
def has_text(t):
    return lambda b: None if t.encode() in b else 'does not contain ' + repr(t)

def json_with(check, label):
    def f(b):
        try: d = json.loads(b)
        except ValueError as e: return 'is not JSON: %s' % e
        try: ok = check(d)
        except Exception as e: return label + ' (%s)' % e
        return None if ok else label
    return f

FILES = [
    ('pilot/', has_text('Connected Earth')),
    ('api/places/main/index-world.json', json_with(lambda d: len(d) > 0, 'is empty')),
    ('api/places/main/cards-world.json', json_with(lambda d: len(d) > 0, 'is empty')),
    ('api/yellowstone.json', json_with(lambda d: len(d['nodes']) > 5, 'has no food web')),
    ('api/species/abies-balsamea.json', json_with(lambda d: len(d['t']) > 30, 'has no species text')),
    ('api/search/meta.json', json_with(lambda d: len(d) > 0, 'is empty')),
    ('api/ties/alabama.json', json_with(lambda d: len(d) > 0, 'is empty')),
]

def fetch(url):
    # A changing query string and no-cache headers, so a CDN copy of the old deploy is not read by mistake.
    req = urllib.request.Request('%s?cb=%d' % (url, time.time() * 1000), headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache', 'User-Agent': 'connected-earth-live-check'})
    with urllib.request.urlopen(req, timeout=20) as r:
        if r.status != 200: raise ValueError('status %d' % r.status)
        return r.read()

def problems(base, stamp):
    out = []
    def get(path):
        try: return fetch(base + path)
        except Exception as e: out.append('%s: %s' % (path or 'index.html', e)); return None
    sw = get('sw.js')
    if sw is not None:
        m = re.search(rb'const V = "([0-9a-f]+)"', sw)
        live = m.group(1).decode() if m else None
        if live != stamp: out.append('sw.js carries build %s, expected %s' % (live, stamp))
    html = get('')
    if html is not None:
        if b'Connected Earth' not in html: out.append('index.html does not contain "Connected Earth"')
        live = hashlib.md5(html).hexdigest()[:8]
        if live != stamp: out.append('index.html is build %s, expected %s' % (live, stamp))
    for path, check in FILES:
        b = get(path)
        if b is not None:
            err = check(b)
            if err: out.append('%s: %s' % (path, err))
    return out

def main(argv):
    if len(argv) < 2: sys.exit(__doc__)
    base, stamp = argv[0].rstrip('/') + '/', argv[1]
    tries = int(argv[argv.index('--tries') + 1]) if '--tries' in argv else 18
    wait = float(argv[argv.index('--wait') + 1]) if '--wait' in argv else 10
    for i in range(1, tries + 1):
        found = problems(base, stamp)
        if not found:
            print('Live site OK: %s build %s (try %d)' % (base, stamp, i)); return 0
        print('try %d/%d: not ready: %s' % (i, tries, '; '.join(found)))
        if i < tries: time.sleep(wait)
    for p in found: print('::error::live site: ' + p)
    print('::error::The live site is not the build just deployed (%s): %s' % (stamp, base))
    return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
