"""#887 step 5b: lib/place_inputs.py records the food web (and story) inputs of a place; a web that changed without a new stamp fails."""
import json, os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import place_inputs as pi

def tree(places):
    r = tempfile.mkdtemp(); os.makedirs(os.path.join(r, 'data', 'places'))
    for k, v in places.items(): json.dump(v, open(os.path.join(r, 'data', 'places', k + '.json'), 'w'))
    return r

def place(extra=None, links=(('a', 'b'),)):
    return dict({'id': 'p', 'nodes': [{'id': 'a', 'sp': 'sa'}, {'id': 'b', 'sp': 'sb'}], 'raw': [list(x) for x in links]}, **(extra or {}))

class T(unittest.TestCase):
    def test_stamp_then_check_is_clean_and_idempotent(self):
        r = tree({'p': place()}); self.assertEqual(pi.stamp(r), ['p']); self.assertEqual(pi.PlaceInputs(r).check(), ([], [])); self.assertEqual(pi.stamp(r), [])
        w = pi.PlaceInputs(r).recs['p']['web']; self.assertEqual((w['n'], w['l']), (2, 1))

    def test_a_changed_web_fails_until_stamped(self):
        r = tree({'p': place()}); pi.stamp(r)
        json.dump(place(links=(('a', 'b'), ('b', 'a'))), open(os.path.join(r, 'data', 'places', 'p.json'), 'w'))
        errs, _ = pi.PlaceInputs(r).check(); self.assertEqual(len(errs), 1); self.assertIn('links changed', errs[0]); self.assertIn('pack', errs[0])
        self.assertEqual(pi.stamp(r), ['p']); self.assertEqual(pi.PlaceInputs(r).check()[0], [])
        json.dump(place(extra={'nodes': [{'id': 'a', 'sp': 'sa'}, {'id': 'c', 'sp': 'sc'}]}), open(os.path.join(r, 'data', 'places', 'p.json'), 'w'))
        self.assertIn('nodes changed', pi.PlaceInputs(r).check()[0][0])

    def test_order_does_not_matter_and_other_fields_do_not_count(self):
        a = place(); b = place(extra={'story': 'new words', 'name': 'x'}); b['nodes'].reverse()
        self.assertEqual(pi.web_inputs(a), pi.web_inputs(b))

    def test_record_for_no_place_and_missing_story_record(self):
        r = tree({'p': place({'story': 'A story.'})}); pi.stamp(r); x = pi.PlaceInputs(r); x.recs['gone'] = {'web': {}}; x.commit()
        errs, warns = pi.PlaceInputs(r).check(); self.assertTrue(any('gone' in e for e in errs)); self.assertTrue(any('story' in w for w in warns))
        x = pi.PlaceInputs(r); x.recs.pop('gone'); x.set_story('p', 'research text\r\n', baseline=True); x.commit()
        self.assertEqual(pi.PlaceInputs(r).check(), ([], [])); self.assertEqual(pi.text_hash('research text'), pi.text_hash(' research text\n'))
        self.assertTrue(pi.PlaceInputs(r).recs['p']['story']['baseline'])

    def test_a_place_that_is_gone_leaves_no_record(self):
        r = tree({'p': place(), 'q': place()}); pi.stamp(r); os.remove(os.path.join(r, 'data', 'places', 'q.json')); pi.stamp(r); self.assertEqual(sorted(pi.PlaceInputs(r).recs), ['p'])

if __name__ == '__main__': unittest.main()
