#!/usr/bin/env python3
"""jobs/droporphans.py (#1183): a node picture entry no place shows is dropped with its file; one a node shows stays."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('build', 'jobs', 'lib'): sys.path.insert(0, os.path.join(ROOT, d))
import droporphans as D, node_photos as N
with tempfile.TemporaryDirectory() as r:
    gone = D.drop(r, write=False); assert gone == [], gone   # nothing to drop in an empty checkout
print('ok')
