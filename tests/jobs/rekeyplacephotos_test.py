#!/usr/bin/env python3
import json, os, shutil, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'jobs'))
import rekeyplacephotos as r

def row(sha, f): return {'f': f, 'a': 'Someone', 'l': 'CC BY 4.0', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg', 'sha256': sha}

class MigrateTests(unittest.TestCase):
    def setUp(self):
        self.ids = {'Alpha Park': ['alpha'], 'Beta Park': ['beta'], 'Harriman State Park': ['nyharriman', 'idharriman'], 'Gone Park': ['gone']}
        self.pics = {'Alpha Park': row('a', 'alpha.jpg'), 'Beta Park': row('b', 'old-name.jpg'), 'Harriman State Park': row('h', 'nyharriman.jpg'), 'Orphan': row('o', 'o.jpg')}
        self.miss = {'Gone Park': {'status': 'nophoto', 'attempts': 1}, 'Harriman State Park': {'status': 'nophoto'}, 'Nowhere': {'status': 'nophoto'}}
        self.large = {'Alpha Park': 'alpha.webp', 'Beta Park': 'beta-old.webp', 'Harriman State Park': 'nyharriman.webp'}
        self.ledgers = {'nearby': {'Alpha Park': '2026-11-15', 'Harriman State Park': '2026-11-14'}, 'commons': {'Alpha Park': '2026-11-12', 'Gone Park': '2026-11-11'}}
        self.new = r.migrate(self.pics, self.miss, self.large, self.ledgers, self.ids)

    def test_rows_are_keyed_by_id_with_the_title_as_a_field_and_the_file_named_by_the_id(self):
        self.assertEqual(sorted(self.new['pics']), ['alpha', 'beta']); self.assertEqual(self.new['pics']['beta']['wiki'], 'Beta Park'); self.assertEqual(self.new['pics']['beta']['f'], 'beta.jpg')
        self.assertIn(('photos/places/old-name.jpg', 'photos/places/beta.jpg'), self.new['moves']); self.assertIn(('photos/places-lg/beta-old.webp', 'photos/places-lg/beta.webp'), self.new['moves'])
        self.assertEqual(self.new['large'], {'alpha': 'alpha.webp', 'beta': 'beta.webp'})

    def test_a_shared_title_loses_its_picture_and_each_place_is_recorded_missing(self):
        self.assertEqual(self.new['shared'], {'Harriman State Park': ['idharriman', 'nyharriman']})
        self.assertEqual(self.new['delete'], ['photos/places-lg/nyharriman.webp', 'photos/places/nyharriman.jpg'])
        for pid in ('idharriman', 'nyharriman'): self.assertEqual(self.new['miss'][pid]['status'], 'nophoto')
        self.assertNotIn('nyharriman', self.new['pics'])

    def test_missing_rows_and_ledgers_follow_their_place_and_unplaced_or_shared_rows_are_dropped(self):
        self.assertEqual(self.new['miss']['gone']['attempts'], 1); self.assertNotIn('Nowhere', self.new['miss'])
        self.assertEqual(self.new['tried'], {'alpha': {'nearby': '2026-11-15', 'commons': '2026-11-12'}, 'gone': {'commons': '2026-11-11'}})
        self.assertEqual(self.new['unplaced'], ['Orphan']); self.assertEqual(self.new['dropped']['ledger:shared'], 1); self.assertEqual(self.new['dropped']['missing:unplaced'], 1)

    def test_the_round_trip_returns_every_unshared_row(self):
        self.assertEqual(r.proof(self.pics, self.new, set(self.new['shared']) | set(self.new['unplaced'])), [])
        self.new['pics']['alpha']['a'] = 'Changed'; self.assertEqual(len(r.proof(self.pics, self.new, set(self.new['shared']) | set(self.new['unplaced']))), 1)

class RunTests(unittest.TestCase):
    def test_a_full_run_leaves_files_and_lists_in_agreement_and_a_second_run_does_nothing(self):
        d = tempfile.mkdtemp(); w = lambda rel, data: (os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True), open(os.path.join(d, rel), 'wb' if isinstance(data, bytes) else 'w').write(data))
        for pid, t in (('alpha', 'Alpha Park'), ('beta', 'Beta Park'), ('nyh', 'Harriman'), ('idh', 'Harriman')): w('data/places/%s.json' % pid, json.dumps({'id': pid, 'imgwiki': t}))
        pics = {'Alpha Park': row('a', 'alpha.jpg'), 'Beta Park': row('b', 'old.jpg'), 'Harriman': row('h', 'nyh.jpg')}
        w('photos/places/places.json', json.dumps(pics)); w('photos/places/missing.json', '{}'); w('photos/places_large.json', json.dumps({'Alpha Park': 'alpha.webp', 'Beta Park': 'oldl.webp', 'Harriman': 'nyh.webp'}))
        w('photos/places_nearby_tried.json', json.dumps({'Beta Park': '2026-11-01'}))
        for f in ('alpha.jpg', 'old.jpg', 'nyh.jpg', 'orphan.jpg'): w('photos/places/' + f, b'J')
        for f in ('alpha.webp', 'oldl.webp', 'nyh.webp'): w('photos/places-lg/' + f, b'W')
        self.assertEqual(r.main(d, True), 0); self.assertTrue(os.path.exists(os.path.join(d, 'photos/places/old.jpg')))   # dry run writes nothing
        self.assertEqual(r.main(d), 0)
        j = lambda rel: json.load(open(os.path.join(d, rel)))
        self.assertEqual(sorted(j('photos/places/places.json')), ['alpha', 'beta']); self.assertEqual(sorted(j('photos/places/missing.json')), ['idh', 'nyh'])
        self.assertEqual(j('photos/places_tried.json'), {'beta': {'nearby': '2026-11-01'}}); self.assertFalse(os.path.exists(os.path.join(d, 'photos/places_nearby_tried.json')))
        self.assertEqual(sorted(os.listdir(os.path.join(d, 'photos/places'))), ['alpha.jpg', 'beta.jpg', 'missing.json', 'places.json'])
        self.assertEqual(sorted(os.listdir(os.path.join(d, 'photos/places-lg'))), ['alpha.webp', 'beta.webp'])
        self.assertEqual(r.main(d), 0)   # already by id

if __name__ == '__main__': unittest.main()
