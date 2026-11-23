#!/usr/bin/env python3
"""jobs/rowtitles.py --json: to_json keeps the status and proposed name of every row, and the reason only when the name is not already right (the data status page and validate_data read it)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import rowtitles as RT
res = [({'sid': 'a1'}, 'same', 'Nene', 'article title'), ({'sid': 'b2'}, 'change', 'Termite', 'article title'), ({'sid': 'c3'}, 'unresolved', None, 'page missing')]
out = RT.to_json(res, '2026-11-23')
assert out == {'asOf': '2026-11-23', 'rows': {'a1': ['same', 'Nene', ''], 'b2': ['change', 'Termite', 'article title'], 'c3': ['unresolved', '', 'page missing']}}, out
print('rowtitles json ok')
