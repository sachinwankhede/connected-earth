#!/usr/bin/env python3
"""#1038: jobs/cleanspelling.py drops a node name only for a listed (row, node) spelling pair; group nodes and other names stay."""
import os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import cleanspelling as c

def test_clean():
    by = {'a': {'name': 'Cattails'}, 'b': {'name': 'Gray wolf'}, 'c': {'name': 'Fungi and bacteria'}}
    eco = {'nodes': [{'sp': 'a', 'name': 'Cattail'}, {'sp': 'b', 'name': 'Arctic wolf'}, {'sp': 'c', 'name': 'Fungi & bacteria'}, {'sp': 'b', 'name': 'Grey wolf'}, {'sp': 'a'}]}
    assert c.clean(eco, by) == 2
    assert [n.get('name') for n in eco['nodes']] == [None, 'Arctic wolf', 'Fungi & bacteria', None, None]
    assert c.clean(eco, by) == 0

if __name__ == '__main__': test_clean(); print('ok')
