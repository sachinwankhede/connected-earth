"""wm.py: one polite client for Wikimedia (Wikipedia API, REST summaries, thumbnails).
One request at a time, a minimum gap between requests, waits as long as Retry-After says on 429/503 (plus jitter),
and keeps the gap longer after a throttle. Never gives up on throttling, only on repeated real errors."""
import json, random, time, urllib.error, urllib.request
UA = {'User-Agent': 'ConnectedEarth/1.0 (sachinw_80@yahoo.com)'}
GAP = 2.0          # seconds between requests while things are fine
_last = [0.0]; _gap = [GAP]

def _pace():
    wait = _last[0] + _gap[0] - time.time()
    if wait > 0: time.sleep(wait)
    _last[0] = time.time()

def get(url, raw=False, tries=6):
    errs = 0; throttles = 0
    while True:
        _pace()
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
            _gap[0] = max(GAP, _gap[0] * 0.9)          # ease back toward the normal gap
            return b if raw else json.loads(b)
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                throttles += 1
                if throttles >= tries: raise RuntimeError('too many throttles for ' + url[:100])
                ra = e.headers.get('Retry-After')
                retry_after = int(ra) if ra and ra.isdigit() else 15
                if retry_after > 300: raise RuntimeError('retry-after exceeds bounded wait for ' + url[:100])
                wait = retry_after + random.uniform(1, 5)
                _gap[0] = min(30.0, _gap[0] * 1.5 + 1)  # slow down after a throttle
                time.sleep(wait); continue
            if e.code == 404: return None
            errs += 1
        except Exception:
            errs += 1
        if errs >= tries: raise RuntimeError('too many errors for ' + url[:100])
        time.sleep(5 * errs)
