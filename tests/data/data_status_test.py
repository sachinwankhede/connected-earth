"""#887 step 8: build/data_status.py gives one row per kind of data with its status, and a problem makes the row 'attention'."""
import json, os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'lib'))
import data_status as ds

def put(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))

class T(unittest.TestCase):
    def test_row_verdicts(self):
        self.assertEqual(ds.row('x', 10, 10)['verdict'], 'fine')
        r = ds.row('x', 10, 8, 2, invalid=1, due_=2, doubts=3); self.assertEqual(r['verdict'], 'attention'); self.assertEqual(len(r['notes']), 3)
        self.assertEqual(ds.row('x', 10, 8, 2)['verdict'], 'fine')   # a recorded miss that is not due is waiting, not a problem

    def test_unknown_author_and_due(self):
        self.assertEqual(ds.unknown({'a': {'a': 'Unknown author'}, 'b': {'a': 'Jo'}, 'c': {'a': ' unknown '}}), 2)
        import photo_registry as pr
        self.assertEqual(ds.due({'old': {'status': 'nophoto', 'attempts': 1, 'checkedAt': '2020-01-01T00:00:00+00:00', 'expiresAt': '2020-02-01T00:00:00+00:00'}}), 1)
        self.assertEqual(ds.due({'new': pr.negative_entry('nophoto')}), 0)

    def test_every_kind_has_a_row_and_a_broken_one_is_reported(self):
        with tempfile.TemporaryDirectory() as r:
            put(r, 'data/places/a.json', {'id': 'a', 'nodes': [{'id': 'g', 'sp': 's'}], 'raw': [], 'story': 'x'})
            rs = ds.rows(r); names = [x['dataset'] for x in rs]
            self.assertEqual(names, ['Place pictures', 'Species pictures', 'Journey pictures', 'Node pictures', 'Outlines', 'Food webs', 'Stories'])
            self.assertIn('| Stories | 1 of 1 |', ds.table(rs)); self.assertEqual([x for x in rs if x['dataset'] == 'Stories'][0]['verdict'], 'fine')

    def test_real_data_reads(self):
        rs = ds.rows(ROOT); self.assertEqual(len(rs), 7); self.assertTrue(all('verdict' in x for x in rs))

if __name__ == '__main__': unittest.main()
