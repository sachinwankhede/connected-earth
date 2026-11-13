import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'jobs'))
import fixcoords as fc

SQ = lambda x0, y0, x1, y1: {'type': 'Polygon', 'coordinates': [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}
GEO = {'01': SQ(0, 0, 10, 10), '02': SQ(20, 0, 30, 10)}


class T(unittest.TestCase):
    def test_near(self):
        self.assertTrue(fc.near_states(5, 5, ['01'], GEO))
        self.assertTrue(fc.near_states(5, 10.05, ['01'], GEO))      # within tolerance (coast)
        self.assertFalse(fc.near_states(5, 25, ['01'], GEO))
        self.assertTrue(fc.near_states(5, 25, ['01', '02'], GEO))

    def _place(self, dd, pid, lat, lon, **kw):
        d = dict({'id': pid, 'name': pid, 'country': '840', 'states': ['01'], 'lat': lat, 'lon': lon}, **kw)
        json.dump(d, open(os.path.join(dd, pid + '.json'), 'w'))

    def test_audit_and_fix(self):
        with tempfile.TemporaryDirectory() as t:
            self._place(t, 'ok', 5, 5)
            self._place(t, 'bad', 5, 25, imgwiki='Bad Park')
            self._place(t, 'lost', 5, 25, imgwiki='Lost Park')
            self._place(t, 'wrongstate', 5, 25, imgwiki='Wrong Park')
            self.assertEqual([d['id'] for f, d in fc.audit(t, GEO)], ['bad', 'lost', 'wrongstate'])
            answers = {'Bad Park': (6.0, 4.0), 'Wrong Park': (5.0, 25.0)}   # Wrong Park's article is in the other state: refused
            def get(url):
                title = __import__('urllib.parse').parse.unquote(url.rsplit('titles=', 1)[1])
                c = answers.get(title)
                return {'query': {'pages': {'1': {'coordinates': [{'lat': c[0], 'lon': c[1]}]} if c else {}}}}
            fixed, unresolved = fc.fix(t, GEO, get)
            self.assertEqual([f[0] for f in fixed], ['bad'])
            self.assertEqual(sorted(unresolved), ['lost', 'wrongstate'])
            d = json.load(open(os.path.join(t, 'bad.json')))
            self.assertEqual((d['lat'], d['lon']), (6.0, 4.0))
            self.assertEqual(json.load(open(os.path.join(t, 'ok.json')))['lon'], 5)


    def test_committed_geo_loads(self):
        root = os.path.join(os.path.dirname(__file__), '..', '..')
        geo = {s['id']: s['g'] for s in json.load(open(os.path.join(root, 'data/geo/geo.json')))['states']}
        self.assertIn('25', geo)                                       # Massachusetts
        self.assertTrue(fc.near_states(42.3, -71.5, ['25'], geo))
        self.assertFalse(fc.near_states(43.77, -79.71, ['25'], geo))    # the wrong Wells State Park point (Ontario)
        fc.audit(os.path.join(root, 'data/places'), geo)               # runs on the committed data


if __name__ == '__main__':
    unittest.main()
