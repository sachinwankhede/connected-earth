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


    def test_drop_pictures_writes_valid_missing_entries(self):
        with tempfile.TemporaryDirectory() as t:
            os.makedirs(os.path.join(t, 'photos/places'))
            json.dump({'Raymond': {'f': 'x.jpg'}, 'Keep': {'f': 'k.jpg'}}, open(os.path.join(t, 'photos/places/places.json'), 'w'))
            json.dump({}, open(os.path.join(t, 'photos/places/missing.json'), 'w'))
            open(os.path.join(t, 'photos/places/x.jpg'), 'w').write('x')
            self.assertEqual(fc.drop_pictures(t), ['Raymond'])
            self.assertFalse(os.path.exists(os.path.join(t, 'photos/places/x.jpg')))
            self.assertEqual(list(json.load(open(os.path.join(t, 'photos/places/places.json')))), ['Keep'])
            e = json.load(open(os.path.join(t, 'photos/places/missing.json')))['Raymond']
            self.assertGreaterEqual(e['attempts'], 1)
            self.assertGreater(e['expiresAt'], e['checkedAt'])
            self.assertEqual(e['status'], 'nophoto')


class PadusTests(unittest.TestCase):
    """#767: the second source, PAD-US by name inside the place's own state."""
    def feat(self, name, x0, y0, x1, y1): return {'attributes': {'Unit_Nm': name, 'GIS_Acres': 10}, 'geometry': {'rings': [[[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]]}}
    def place(self, **kw): return dict({'id': 'p', 'name': 'Harriman State Park', 'place': 'New York, USA', 'country': '840', 'states': ['01'], 'lat': 5, 'lon': 25}, **kw)
    def getter(self, feats, seen=None):
        def get(url):
            if seen is not None: seen.append(url)
            return {'features': feats}
        return get

    def test_the_query_is_limited_to_the_places_state_and_the_best_name_wins(self):
        import urllib.parse
        seen = []; g = self.getter([self.feat('Harriman State Park', 2, 2, 4, 4), self.feat('Harriman Trail Corridor', 8, 8, 9, 9)], seen)
        r = fc.padus_coords(self.place(), GEO, g)
        self.assertEqual((r[0], r[1], r[2]), (3.0, 3.0, 'Harriman State Park'))
        q = urllib.parse.unquote_plus(seen[0]); self.assertIn("State_Nm='NY'", q); self.assertIn("LIKE '%HARRIMAN%'", q)

    def test_the_biggest_piece_gives_the_centre(self):
        f = self.feat('Harriman State Park', 1, 1, 2, 2); f['geometry']['rings'].append([[4, 4], [8, 4], [8, 8], [4, 8], [4, 4]])
        self.assertEqual(fc.padus_coords(self.place(), GEO, self.getter([f]))[:2], (6.0, 6.0))

    def test_a_weak_name_match_a_centre_outside_the_state_or_no_state_is_refused(self):
        self.assertIsNone(fc.padus_coords(self.place(), GEO, self.getter([self.feat('Harriman Wildlife Corridor Access', 2, 2, 4, 4)])), 'too few shared words')
        self.assertIsNone(fc.padus_coords(self.place(), GEO, self.getter([self.feat('Harriman State Park', 22, 2, 24, 4)])), 'centre outside the place\'s state')
        self.assertIsNone(fc.padus_coords(self.place(place='Lake Michigan, USA'), GEO, self.getter([self.feat('Harriman State Park', 2, 2, 4, 4)])), 'not a state')
        self.assertIsNone(fc.padus_coords(self.place(states=['01', '02']), GEO, self.getter([self.feat('Harriman State Park', 2, 2, 4, 4)])), 'several states')
        self.assertIsNone(fc.padus_coords(self.place(), GEO, lambda u: None))

    def test_fix_uses_wikipedia_first_then_padus_and_says_which(self):
        with tempfile.TemporaryDirectory() as t:
            for pid, wiki in (('a', True), ('b', False), ('c', False)):
                json.dump(self.place(id=pid, name='Park ' + pid, imgwiki='W' + pid, place='New York, USA'), open(os.path.join(t, pid + '.json'), 'w'))
            def get(url):
                if 'titles=' in url and url.endswith('Wa'): return {'query': {'pages': {'1': {'coordinates': [{'lat': 6.0, 'lon': 4.0}]}}}}
                return {'query': {'pages': {'1': {}}}}
            pad = lambda d, g: (1.0, 2.0, 'Park b') if d['id'] == 'b' else None
            fixed, unresolved = fc.fix(t, GEO, get, pad)
            self.assertEqual([(f[0], f[3]) for f in fixed], [('a', 'Wikipedia'), ('b', 'PAD-US "Park b"')]); self.assertEqual(unresolved, ['c'])
            self.assertEqual(json.load(open(os.path.join(t, 'b.json')))['lat'], 1.0)


if __name__ == '__main__':
    unittest.main()
