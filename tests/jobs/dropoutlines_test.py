#!/usr/bin/env python3
"""#977: jobs/dropoutlines.py puts a place on the missing list, and bounds.py (PAD-US) then skips it so the same unit is not fetched again."""
import json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import dropoutlines, outline_records as orc

def tree():
    root = tempfile.mkdtemp(); os.makedirs(os.path.join(root, 'data', 'outlines'))
    rec = orc.OutlineRecords(root)
    for pid in ('a', 'b'):
        json.dump({'n': 'x', 'r': [[0, 0, 1, 0, 1, 1, 0, 0]]}, open(os.path.join(root, 'data', 'outlines', pid + '.json'), 'w')); rec.record(pid, 'padus')
    rec.commit(); return root

class T(unittest.TestCase):
    def test_drop_removes_file_and_record_and_lists_the_place(self):
        r = tree(); self.assertEqual(dropoutlines.main(['a', 'zzz'], root=r), ['a'])
        rec = orc.OutlineRecords(r)
        self.assertFalse(os.path.exists(os.path.join(r, 'data', 'outlines', 'a.json'))); self.assertFalse(rec.has('a')); self.assertTrue(rec.is_missing('a'))
        self.assertTrue(rec.has('b') and not rec.is_missing('b')); self.assertEqual(rec.check(), [])

    def test_dry_changes_nothing(self):
        r = tree(); self.assertEqual(dropoutlines.main(['a'], root=r, dry=True), ['a'])
        self.assertTrue(os.path.exists(os.path.join(r, 'data', 'outlines', 'a.json'))); self.assertTrue(orc.OutlineRecords(r).has('a'))

    def test_pad_us_skips_a_place_on_the_missing_list(self):
        import importlib.util
        r = tree(); dropoutlines.main(['a'], root=r)
        src = open(os.path.join(ROOT, 'jobs', 'bounds.py')).read()
        self.assertIn("if on_missing_list(e['id'])", src)
        ns = {'__name__': 'x', 'os': os, 'sys': sys}
        exec(src[src.index('_missing={}'):src.index("if __name__=='__main__':")], ns)
        self.assertTrue(ns['on_missing_list']('a', root=r)); self.assertFalse(ns['on_missing_list']('b', root=r))

if __name__ == '__main__': unittest.main()
