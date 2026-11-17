#!/usr/bin/env python3
"""lib/author_repair.py: repair of 'unknown author' credits (#887). A fake `get` stands in for Wikimedia, Openverse and GBIF: no network. Each writer (place, species, journey) is run in a temp root."""
import datetime, json, os, sys, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import author_repair as ar, place_photos as pp, species_photos as sp, journey_photos as jp

TODAY = datetime.date(2026, 11, 17)
def commons(artist='', licence='CC BY-SA 4.0', credit='', user=''):
    meta = {'LicenseShortName': {'value': licence}, 'LicenseUrl': {'value': 'https://creativecommons.org/licenses/by-sa/4.0'}}
    if artist: meta['Artist'] = {'value': artist}
    if credit: meta['Credit'] = {'value': credit}
    return {'query': {'pages': {'1': {'imageinfo': [{'extmetadata': meta}], 'revisions': [{'user': user}]}}}}

class Fake:
    """get(url) -> the answer for the first key found in the url; records every url asked."""
    def __init__(self, answers): self.answers = answers; self.urls = []
    def __call__(self, url):
        self.urls.append(url)
        for k, v in self.answers.items():
            if k in url:
                if isinstance(v, Exception): raise v
                return v
        return None

def row(page='File:Some_file.jpg', a='Unknown author', l='Public domain'):
    return dict(a=a, l=l, lu='', p='https://commons.wikimedia.org/wiki/' + page, f='x', sha256='s')

def seed(kind, rows):
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, 'photos'))
    name = {'place': 'places/places.json', 'species': 'species_pictures.json', 'journey': 'journey_pictures.json'}[kind]
    os.makedirs(os.path.dirname(os.path.join(d, 'photos', name)), exist_ok=True)
    with open(os.path.join(d, 'photos', name), 'w') as fh: json.dump(rows, fh)
    return d, {'place': pp.PlacePhotos, 'species': sp.SpeciesPhotos, 'journey': jp.JourneyPhotos}[kind]

class RepairTests(unittest.TestCase):
    def test_found_on_commons_returns_the_artist_and_licence(self):
        c = ar.repair(row(), Fake({'Some': commons('<a href="x">Jane Doe</a>')}))
        self.assertEqual(c, {'a': 'Jane Doe', 'l': 'CC BY-SA 4.0', 'lu': 'https://creativecommons.org/licenses/by-sa/4.0'})
    def test_own_work_uses_the_uploader(self):
        c = ar.repair(row(), Fake({'Some': commons(credit='Own work', user='Uploader1', licence='CC0')}))
        self.assertEqual((c['a'], c['l']), ('Uploader1', 'CC0'))
    def test_not_found_is_none(self):
        self.assertIsNone(ar.repair(row(), Fake({'Some': commons('Unknown author')})))
        self.assertIsNone(ar.repair(row(), Fake({})))
    def test_licence_refused_is_none(self):
        for lic in ('CC BY-NC 4.0', 'GFDL', 'CC BY-ND 2.0', ''): self.assertIsNone(ar.repair(row(), Fake({'Some': commons('Jane Doe', lic)})), lic)
    def test_a_named_author_is_not_looked_up(self):
        f = Fake({}); self.assertIsNone(ar.repair(row(a='Jane Doe'), f)); self.assertEqual(f.urls, [])
    def test_legacy_unknown_spellings_count(self):
        for a in ('Unknown', 'UNKNOWN AUTHOR', 'unknown author', 'Anonymous', '<a@b.co>'): self.assertTrue(ar.is_unknown({'a': a}), a)
    def test_openverse_and_gbif(self):
        o = row(); o['p'] = 'https://openverse.org/image/0123abcd-0123-0123-0123-0123456789ab'
        self.assertEqual(ar.repair(o, Fake({'api.openverse.org': {'creator': 'Ann', 'license': 'by', 'license_version': '4.0'}}))['a'], 'Ann')
        self.assertIsNone(ar.repair(o, Fake({'api.openverse.org': {'creator': 'Ann', 'license': 'by-nc', 'license_version': '4.0'}})))
        g = row(); g['p'] = 'https://www.gbif.org/occurrence/42'
        rec = lambda lic: {'media': [{'creator': 'Bob', 'license': lic}]}
        self.assertEqual(ar.repair(g, Fake({'occurrence/42': rec('http://creativecommons.org/licenses/by/4.0/')}))['l'], 'CC BY 4.0')
        self.assertIsNone(ar.repair(g, Fake({'occurrence/42': rec('http://creativecommons.org/licenses/by-sa/4.0/')})))   # GBIF allows CC0 and CC BY only
    def test_inaturalist_and_other_hosts_are_left_alone(self):
        for p in ('https://www.inaturalist.org/photos/9', 'https://example.com/x', 'http://commons.wikimedia.org/wiki/File:A.jpg', ''):
            r = row(); r['p'] = p; f = Fake({}); self.assertIsNone(ar.repair(r, f)); self.assertEqual(f.urls, [])

class StepTests(unittest.TestCase):
    """The same four cases through each writer's own set_credit / note_repair_tried / commit."""
    def run_kind(self, kind):
        d, W = seed(kind, {'found': row('File:Found.jpg'), 'nobody': row('File:Nobody.jpg'), 'noncom': row('File:Noncom.jpg'), 'named': row(a='Jane Doe'), 'held': row('File:Held.jpg')})
        w = W(d); w.tried['held'] = {'author-repair': (TODAY - datetime.timedelta(days=10)).isoformat()}
        f = Fake({'Found.jpg': commons('Jane Roe', 'CC BY 4.0'), 'Nobody.jpg': commons('Unknown'), 'Noncom.jpg': commons('Jo', 'CC BY-NC 4.0'), 'Held.jpg': commons('Held Author')})
        s, stopped = ar.repair_step(w, today=TODAY, get=f, log=lambda m: None); w.commit(); w2 = W(d)
        self.assertFalse(stopped); self.assertEqual((s['fixed'], s['none'], s['held'], s['looked']), (1, 2, 1, 3))
        self.assertEqual(w2.pics['found']['a'], 'Jane Roe'); self.assertEqual(w2.pics['found']['l'], 'CC BY 4.0'); self.assertEqual(w2.pics['found']['sha256'], 's')   # the rest of the row stays
        for k in ('nobody', 'noncom'):
            self.assertEqual(w2.pics[k]['a'], 'Unknown author'); self.assertEqual(w2.pics[k]['l'], 'Public domain'); self.assertEqual(w2.tried[k]['author-repair'], TODAY.isoformat())
        self.assertEqual(w2.pics['held']['a'], 'Unknown author'); self.assertFalse(any('Held.jpg' in u for u in f.urls))   # held: not even asked
        self.assertNotIn('found', w2.tried); self.assertEqual(w2.pics['named']['a'], 'Jane Doe')
        # a second run the same day asks nobody: every unknown is held now
        f2 = Fake({}); s2, _ = ar.repair_step(w2, today=TODAY, get=f2, log=lambda m: None); self.assertEqual(f2.urls, []); self.assertEqual(s2['held'], 3)
        # after the window the held ones are asked again
        later = TODAY + datetime.timedelta(days=91); f3 = Fake({}); ar.repair_step(w2, today=later, get=f3, log=lambda m: None); self.assertEqual(len(f3.urls), 3)
    def test_place(self): self.run_kind('place')
    def test_species(self): self.run_kind('species')
    def test_journey(self): self.run_kind('journey')

    def test_limit_budget_and_throttle_stop_the_step(self):
        d, W = seed('place', {c: row('File:%s.jpg' % c) for c in 'abcd'}); w = W(d)
        s, _ = ar.repair_step(w, today=TODAY, limit=2, get=Fake({}), log=lambda m: None); self.assertEqual((s['looked'], s['later']), (2, 2))
        s, st = ar.repair_step(w, today=TODAY, late=lambda: True, get=Fake({}), log=lambda m: None); self.assertTrue(st); self.assertEqual(s['looked'], 0)
        d, W = seed('place', {c: row('File:%s.jpg' % c) for c in 'ab'}); w = W(d)
        s, st = ar.repair_step(w, today=TODAY, get=Fake({'a.jpg': RuntimeError('throttled')}), log=lambda m: None)
        self.assertTrue(st); self.assertEqual(w.tried, {})   # a throttle records no hold: the row is tried again next run
    def test_dry_run_asks_nobody_and_writes_nothing(self):
        d, W = seed('species', {'a': row()}); w = W(d); f = Fake({})
        s, _ = ar.repair_step(w, today=TODAY, dry=True, get=f); self.assertEqual(f.urls, []); self.assertEqual(w.tried, {})
    def test_writer_refuses_a_credit_without_a_name(self):
        d, W = seed('place', {'a': row()}); w = W(d)
        with self.assertRaises(ValueError): w.set_credit('a', {'a': 'Unknown author', 'l': 'CC0'})
        with self.assertRaises(ValueError): w.set_credit('nope', {'a': 'X', 'l': 'CC0'})

if __name__ == '__main__': unittest.main()
