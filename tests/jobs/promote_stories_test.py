import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'jobs'))
import promote_stories as ps


class T(unittest.TestCase):
    def test_promote(self):
        with tempfile.TemporaryDirectory() as t:
            dr, da = os.path.join(t, 'd'), os.path.join(t, 'p')
            os.mkdir(dr); os.mkdir(da)
            for pid, extra in (('a', {}), ('b', {'story': 'old'})):
                json.dump(dict({'id': pid, 'name': pid}, **extra), open(os.path.join(da, pid + '.json'), 'w'))
            for pid in ('a', 'b', 'c'):
                json.dump({'id': pid, 'story': 'S' + pid, 'matters': 'M' + pid}, open(os.path.join(dr, pid + '.json'), 'w'))
            done, skipped = ps.promote(dr, da)
            self.assertEqual(done, ['a'])
            self.assertEqual(sorted(skipped), ['b.json', 'c.json'])
            self.assertEqual(json.load(open(os.path.join(da, 'a.json')))['story'], 'Sa')
            self.assertEqual(json.load(open(os.path.join(da, 'b.json')))['story'], 'old')


if __name__ == '__main__':
    unittest.main()
