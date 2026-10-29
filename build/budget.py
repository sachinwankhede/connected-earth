#!/usr/bin/env python3
"""budget.py: fail if the built pages or data grow past agreed sizes (bytes, uncompressed). Raise a limit on purpose, in this file."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMITS = {'index.html': 3_600_000, 'pilot/index.html': 4_200_000, 'data/species.json': 4_000_000}
WEB_MAX = 250_000      # one place's web file
WEBS_TOTAL = 25_000_000       # fetched one at a time, so only the deploy size grows
OUTLINE_MAX = 400_000   # one park's outline file (fetched when the park opens)
OUTLINES_TOTAL = 20_000_000
bad = 0
def size(p): return os.path.getsize(os.path.join(ROOT, p))
for p, lim in LIMITS.items():
    n = size(p); ok = n <= lim; bad += not ok
    print('%-22s %9d / %9d %s' % (p, n, lim, 'ok' if ok else 'OVER'))
ws = [(f, size('webs/' + f)) for f in os.listdir(os.path.join(ROOT, 'webs'))]
tot = sum(n for _, n in ws); big = max(ws, key=lambda x: x[1])
os_ = [(f, size('data/outlines/' + f)) for f in os.listdir(os.path.join(ROOT, 'data', 'outlines'))]
obig = max(os_, key=lambda x: x[1]); otot = sum(n for _, n in os_)
for label, n, lim in (('webs total', tot, WEBS_TOTAL), ('largest web ' + big[0], big[1], WEB_MAX), ('outlines total', otot, OUTLINES_TOTAL), ('largest outline ' + obig[0], obig[1], OUTLINE_MAX)):
    ok = n <= lim; bad += not ok
    print('%-22s %9d / %9d %s' % (label, n, lim, 'ok' if ok else 'OVER'))
sys.exit(1 if bad else 0)
