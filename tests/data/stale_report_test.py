"""#887 step 5: the stale report counts derived items and those that record their inputs, and notes files and records that disagree."""
import json, os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import stale_report

def put(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))

class Report(unittest.TestCase):
    def run_in(self, root):
        old = stale_report.ROOT; stale_report.ROOT = root
        try: return stale_report.report()
        finally: stale_report.ROOT = old

    def test_counts_and_notes(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/outlines/a.json', {'n': 1}); put(r, 'data/outlines/b.json', {'n': 1})
            put(r, 'data/outline_records.json', {'a': {'inputs': {'lat': 1, 'lon': 2, 'name': 'a'}}, 'c': {}})
            a = {'story': 'x', 'nodes': [{'id': 'g', 'sp': 's'}], 'raw': []}
            put(r, 'data/places/a.json', a); put(r, 'data/places/b.json', {'story': 'y', 'nodes': [{'id': 'g', 'sp': 's'}]})
            sys.path.insert(0, os.path.join(ROOT, 'lib')); import place_inputs
            put(r, 'data/place_inputs.json', {'a': {'web': dict(place_inputs.web_inputs(a), at='d'), 'story': {'research': 'h', 'at': 'd'}}})
            rows, notes = self.run_in(r)
            self.assertEqual(rows, [('outlines', 2, 1, rows[0][3]), ('stories', 2, 1, rows[1][3]), ('food webs', 2, 1, rows[2][3])])
            self.assertEqual(len(notes), 3)   # b has no record, c has no file, c names no place

    def test_empty_root_is_fine(self):
        with tempfile.TemporaryDirectory() as r:
            os.makedirs(os.path.join(r, 'data/places'))
            rows, notes = self.run_in(r)
            self.assertEqual([x[1:3] for x in rows], [(0, 0)] * 3); self.assertEqual(notes, [])

if __name__ == '__main__': unittest.main()
