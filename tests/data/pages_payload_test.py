#!/usr/bin/env python3
"""The deploy stages the site with build/pages_payload.py: it must pass on a fresh build, so a change to the data folders cannot break the deploy unnoticed (it did on 3 Nov, #320)."""
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if not (os.path.exists(os.path.join(ROOT, 'index.html')) and os.path.isdir(os.path.join(ROOT, 'api', 'places', 'main'))):
    print('skipped: the build has not run'); sys.exit(0)
r = subprocess.run([sys.executable, os.path.join(ROOT, 'build', 'pages_payload.py')], capture_output=True, text=True)
assert r.returncode == 0, 'pages_payload.py failed: ' + (r.stdout + r.stderr)[-400:]
print('ok')
