import json, os, sys, tempfile, unittest, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'jobs'))
import fiximgwiki as f

def place(d, pid, lat, lon, title):
    open(os.path.join(d, pid + '.json'), 'w').write(json.dumps(dict(id=pid, name=pid, lat=lat, lon=lon, imgwiki=title), ensure_ascii=False) + '\n')

def api(pages):
    """A stub of the Wikipedia API: {title: (lat, lon) | None | 'disambiguation' | 'missing'}."""
    def get(url):
        t = urllib.parse.unquote(url.rsplit('titles=', 1)[1]); v = pages.get(t, 'missing')
        if v == 'missing': return {'query': {'pages': {'-1': {'title': t, 'missing': ''}}}}
        p = {'title': t}
        if v == 'disambiguation': p['pageprops'] = {'disambiguation': ''}
        elif v: p['coordinates'] = [{'lat': v[0], 'lon': v[1]}]
        return {'query': {'pages': {'1': p}}}
    return get

class FixTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        place(self.d, 'idharriman', 44.4045, -111.557, 'Harriman State Park'); place(self.d, 'nyharriman', 41.2305, -74.093, 'Harriman State Park')
        place(self.d, 'neponca', 42.6215, -96.7214, 'Ponca State Park'); place(self.d, 'sdponca', 42.6184, -96.7228, 'Ponca State Park')
        place(self.d, 'gulf', 28.8, -91.0, 'Gulf Islands National Seashore'); place(self.d, 'usgulfislandsnationalsea', 30.23, -88.752, 'Gulf Islands National Seashore')
    def pages(self): return {'Harriman State Park (Idaho)': (44.40, -111.56), 'Harriman State Park (New York)': (41.23, -74.09), 'Gulf of Mexico': (25.0, -90.0)}
    def test_each_place_gets_its_own_title_and_only_imgwiki_changes(self):
        done, unresolved, owner = f.run(self.d, api(self.pages()))
        self.assertEqual({x[0]: x[2] for x in done}, {'idharriman': 'Harriman State Park (Idaho)', 'nyharriman': 'Harriman State Park (New York)', 'gulf': 'Gulf of Mexico'})
        d = json.load(open(os.path.join(self.d, 'idharriman.json'))); self.assertEqual((d['imgwiki'], d['lat'], d['name']), ('Harriman State Park (Idaho)', 44.4045, 'idharriman'))
        self.assertTrue(open(os.path.join(self.d, 'idharriman.json')).read().endswith('\n'))
        self.assertEqual(owner, []); self.assertEqual(json.load(open(os.path.join(self.d, 'sdponca.json')))['imgwiki'], 'Ponca State Park')   # run() never removes a place
    def test_dry_changes_nothing(self):
        done, _, _ = f.run(self.d, api(self.pages()), dry=True); self.assertEqual(len(done), 3)
        self.assertEqual(json.load(open(os.path.join(self.d, 'idharriman.json')))['imgwiki'], 'Harriman State Park')
    def test_a_title_is_refused_when_missing_ambiguous_far_or_taken(self):
        pages = {'Harriman State Park (Idaho)': 'disambiguation', 'Harriman State Park (New York)': (44.40, -111.56), 'Harriman State Park': (41.23, -74.09), 'Gulf of Mexico': None}
        done, unresolved, _ = f.run(self.d, api(pages)); why = dict(unresolved)
        self.assertEqual(done, [])
        self.assertIn('disambiguation', why['idharriman']); self.assertIn('no coordinates', why['gulf'])
        self.assertIn('km from the place', why['nyharriman'])   # the first candidate is about 3000 km away
        self.assertIn('already the title of idharriman', why['nyharriman'])   # the second is right but Idaho still holds it (it found no title of its own)
    def test_two_places_cannot_take_the_same_title(self):
        done, unresolved, _ = f.run(self.d, api({'Harriman State Park (Idaho)': (44.40, -111.56), 'Harriman State Park (New York)': (44.40, -111.56), 'Harriman State Park': (44.40, -111.56)}))
        self.assertEqual([x[0] for x in done], ['idharriman']); self.assertIn('nyharriman', dict(unresolved))
    def test_a_place_that_already_has_its_own_title_is_left(self):
        place(self.d, 'idharriman', 44.4045, -111.557, 'Harriman State Park (Idaho)'); place(self.d, 'nyharriman', 41.2305, -74.093, 'Harriman State Park (New York)')
        done, _, _ = f.run(self.d, api(self.pages())); self.assertEqual([x[0] for x in done], ['gulf'])
class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.r = tempfile.mkdtemp(); self.d = os.path.join(self.r, 'data', 'places'); os.makedirs(self.d); os.makedirs(os.path.join(self.r, 'data', 'order'))
        self.o = os.path.join(self.r, 'data', 'order', '0000-main.json')
        for pid, lat, lon in (('neponca', 42.6215, -96.7214), ('sdponca', 42.6184, -96.7228)):
            open(os.path.join(self.d, pid + '.json'), 'w').write(json.dumps(dict(id=pid, name='Ponca State Park', lat=lat, lon=lon)))
        json.dump(['a', 'neponca', 'sdponca', 'b'], open(self.o, 'w')); os.makedirs(os.path.join(self.r, 'data', 'outlines'))
        for pid in ('neponca', 'sdponca'): open(os.path.join(self.r, 'data', 'outlines', pid + '.json'), 'w').write('[]')
    def test_a_verified_duplicate_goes_with_its_order_entry(self):
        removed, refused = f.remove_duplicates(self.r, dry=True); self.assertEqual([x[:2] for x in removed], [('sdponca', 'neponca')])
        self.assertTrue(os.path.exists(os.path.join(self.d, 'sdponca.json'))); self.assertIn('sdponca', json.load(open(self.o)))   # dry changes nothing
        removed, refused = f.remove_duplicates(self.r); self.assertEqual(refused, [])
        self.assertEqual(sorted(os.listdir(os.path.join(self.r, 'data', 'outlines'))), ['neponca.json']); self.assertEqual(sorted(os.listdir(self.d)), ['neponca.json']); self.assertEqual(json.load(open(self.o)), ['a', 'neponca', 'b'])
        self.assertEqual(f.remove_duplicates(self.r), ([], []))   # idempotent
    def test_refused_when_the_names_differ_or_the_places_are_far_apart(self):
        d = json.load(open(os.path.join(self.d, 'sdponca.json'))); d['name'] = 'Other'; json.dump(d, open(os.path.join(self.d, 'sdponca.json'), 'w'))
        removed, refused = f.remove_duplicates(self.r); self.assertEqual(removed, []); self.assertIn('differs', refused[0][1])
        d['name'] = 'Ponca State Park'; d['lat'] = 44.0; json.dump(d, open(os.path.join(self.d, 'sdponca.json'), 'w'))
        removed, refused = f.remove_duplicates(self.r); self.assertEqual(removed, []); self.assertIn('km from neponca', refused[0][1])
        self.assertTrue(os.path.exists(os.path.join(self.d, 'sdponca.json')))
    def test_refused_when_the_place_that_stays_is_missing(self):
        os.remove(os.path.join(self.d, 'neponca.json')); removed, refused = f.remove_duplicates(self.r); self.assertEqual(removed, []); self.assertIn('does not exist', refused[0][1])
if __name__ == '__main__': unittest.main()
