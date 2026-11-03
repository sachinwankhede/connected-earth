"""Place order as append-only files and journeys one file each (#277): the new layout reads back as the old one, promotion and state jobs never edit an existing order file."""
import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build'))
import journeydata as J

def put(root, rel, obj):
    p = os.path.join(root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(obj, open(p, 'w'))

def old_tree(root):
    for i, st in (('a', None), ('b', None), ('c', 'pilot'), ('d', 'pilot')):
        put(root, 'data/places/%s.json' % i, {'id': i, **({'stage': st} if st else {})})
    put(root, 'data/journeys/links.json', {'couple': 0.5, 'src': {'k': 1}, 'order': ['b', 'a'], 'cross': [
        {'id': 'zz', 'type': 'species', 'title': 'Z', 'text': 't', 'ends': []}, {'id': 'aa', 'type': 'species', 'title': 'A', 'text': 't', 'ends': []}]})
    put(root, 'data/journeys/pilot-order.json', ['d', 'c'])

class Layouts(unittest.TestCase):
    def setUp(self): self.d = tempfile.TemporaryDirectory(); self.r = self.d.name; old_tree(self.r)
    def tearDown(self): self.d.cleanup()
    def test_old_layout_reads(self):
        self.assertEqual(J.order(self.r), (['b', 'a'], ['d', 'c']))
        self.assertEqual([c['id'] for c in J.journeys(self.r)], ['zz', 'aa'])   # card order is the array order
        self.assertEqual(J.links(self.r)['couple'], 0.5)
    def test_split_reads_back_the_same(self):
        before = (J.order(self.r), J.journeys(self.r), J.config(self.r), J.links(self.r))
        J.split(self.r)
        self.assertFalse(os.path.exists(os.path.join(self.r, 'data/journeys/links.json'))); self.assertFalse(os.path.exists(os.path.join(self.r, 'data/journeys/pilot-order.json')))
        self.assertEqual((J.order(self.r), J.journeys(self.r), J.config(self.r), J.links(self.r)), before)
        self.assertEqual(J.order_problems(self.r), [])
    def test_promotion_keeps_the_position_and_new_files_come_last(self):
        J.split(self.r)
        put(self.r, 'data/places/c.json', {'id': 'c'})                       # promoted: only the stage is dropped
        self.assertEqual(J.order(self.r), (['b', 'a', 'c'], ['d']))          # c keeps its place in the sequence
        put(self.r, 'data/places/e.json', {'id': 'e', 'stage': 'pilot'})
        name = J.add_segment(self.r, ['e', 'a'], 'state-XX')                 # 'a' is already known and is left out
        self.assertRegex(name, r'^\d{8}T\d{6}-state-XX\.json$')
        self.assertEqual(J.order(self.r), (['b', 'a', 'c'], ['d', 'e']))
        self.assertIsNone(J.add_segment(self.r, ['e'], 'state-XX'))          # nothing new: no file
    def test_problems_are_reported(self):
        J.split(self.r)
        put(self.r, 'data/places/new.json', {'id': 'new'}); put(self.r, 'data/order/0002-x.json', ['a', 'ghost'])
        text = ' | '.join(J.order_problems(self.r))
        for want in ("'new' is in no file", "'ghost' in 0002-x.json has no place file", "'a' is in both 0000-main.json and 0002-x.json"): self.assertIn(want, text)

if __name__ == '__main__': unittest.main()
