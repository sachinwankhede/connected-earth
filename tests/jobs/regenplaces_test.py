#!/usr/bin/env python3
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import regenplaces as r

PLACE = {'id': 'riraymond', 'name': 'Raymond', 'short': 'Raymond', 'place': 'Rhode Island, USA', 'states': ['44'], 'kind': 'Forest', 'lat': 41.98, 'lon': -71.64, 'auto': True,
         'notes': 'Built automatically. The species are the most often recorded in GBIF within about 1.5 km of the park location (location from PAD-US boundary).'}

class T(unittest.TestCase):
    def test_a_place_becomes_the_park_record_the_draft_step_reads(self):
        p, why = r.park_from_place(PLACE)
        self.assertIsNone(why); self.assertEqual(p, dict(id='riraymond', name='Raymond', short='Raymond', states=['Rhode Island'], kind='Forest', lat=41.98, lon=-71.64, radius=1.5, points=None))
        q, _ = r.park_from_place(dict(PLACE, place='Florida Keys, Florida, USA', notes=PLACE['notes'].replace('1.5', '3.0'))); self.assertEqual((q['states'], q['radius']), (['Florida'], 3.0))

    def test_places_that_cannot_be_rebuilt_this_way_are_refused_with_a_reason(self):
        for change, why in (({'auto': False}, 'not an automatic place'), ({'states': ['44', '25']}, 'not exactly one state'), ({'notes': 'none'}, 'no radius in its notes')):
            p, w = r.park_from_place(dict(PLACE, **change)); self.assertIsNone(p); self.assertEqual(w, why)

    def test_species_names_skip_the_environment_items(self):
        self.assertEqual(r.species_names({'nodes': [{'name': 'Moose'}, {'sp': 'x'}, {'name': 'Sunlight', 'cat': 'env'}]}), ['Moose', 'x'])

class DraftUserAgentTests(unittest.TestCase):
    def test_every_request_names_the_site_because_globi_refuses_the_default_user_agent(self):
        import tempfile
        from unittest import mock
        os.environ.setdefault('WORK', tempfile.mkdtemp())
        import draft
        seen = []
        with mock.patch.object(draft.fetch, 'fetch_text', side_effect=lambda u, **kw: seen.append(kw) or 'ok'):
            self.assertEqual(draft.getu('https://api.globalbioticinteractions.org/interaction?x=1'), 'ok')
        self.assertEqual(seen[0]['headers'], draft.UA); ua = draft.UA['User-Agent']
        self.assertIn('https://connected-earth-5ps.pages.dev/', ua); self.assertNotIn('@', ua); self.assertNotIn('github.com', ua)

if __name__ == '__main__': unittest.main()
