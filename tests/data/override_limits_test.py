"""#887 step 7: a place node repeating its species row's name in other capitals, or more nodes with their own name or wiki than the limit, fail the data check."""
import json, os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build')); sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import species, validate_data, cleanoverrides

SP = {'corvus-corax': {'sid': 'corvus-corax', 'latin': 'Corvus corax', 'name': 'Common raven', 'wiki': 'Common raven'}}

def place(root, nodes):
    os.makedirs(os.path.join(root, 'data/places'), exist_ok=True)
    json.dump({'id': 'x', 'nodes': nodes}, open(os.path.join(root, 'data/places/x.json'), 'w'))

class Overrides(unittest.TestCase):
    def test_same_name(self):
        self.assertTrue(species.same_name('Common Raven', 'Common raven'))
        self.assertTrue(species.same_name('Common-raven', 'Common raven'))
        self.assertFalse(species.same_name('Raven', 'Common raven'))
        self.assertFalse(species.same_name('Common raven', 'Common raven'))
        self.assertFalse(species.same_name(None, 'Common raven'))

    def test_a_noise_name_fails_and_a_real_one_does_not(self):
        with tempfile.TemporaryDirectory() as r:
            place(r, [{'id': 'a', 'sp': 'corvus-corax', 'name': 'Common Raven'}])
            self.assertEqual(len(validate_data.override_errors(r, SP)), 1)
            place(r, [{'id': 'a', 'sp': 'corvus-corax', 'name': 'Northern raven'}])
            self.assertEqual(validate_data.override_errors(r, SP), [])

    def test_the_count_may_not_grow(self):
        old = validate_data.NAME_OVERRIDE_LIMIT, validate_data.WIKI_OVERRIDE_LIMIT
        try:
            validate_data.NAME_OVERRIDE_LIMIT = 0; validate_data.WIKI_OVERRIDE_LIMIT = 0
            with tempfile.TemporaryDirectory() as r:
                place(r, [{'id': 'a', 'sp': 'corvus-corax', 'name': 'Northern raven', 'wiki': 'Raven'}])
                self.assertEqual(len(validate_data.override_errors(r, SP)), 2)
        finally: validate_data.NAME_OVERRIDE_LIMIT, validate_data.WIKI_OVERRIDE_LIMIT = old

    def test_the_job_drops_only_noise(self):
        by = {'corvus-corax': SP['corvus-corax']}
        e = {'nodes': [{'id': 'a', 'sp': 'corvus-corax', 'name': 'Common Raven'}, {'id': 'b', 'sp': 'corvus-corax', 'name': 'Northern raven'}]}
        self.assertEqual(cleanoverrides.clean(e, by), 1)
        self.assertNotIn('name', e['nodes'][0]); self.assertEqual(e['nodes'][1]['name'], 'Northern raven')

if __name__ == '__main__': unittest.main()
