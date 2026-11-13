#!/usr/bin/env python3
import io, json, os, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import gemini_batch as g


class Resp:
    def __init__(self, text, usage=None): self.b = json.dumps({'candidates': [{'content': {'parts': [{'text': text}]}}], 'usageMetadata': usage or {'promptTokenCount': 10, 'candidatesTokenCount': 5}}).encode()
    def read(self): return self.b


class AskTests(unittest.TestCase):
    ROW = dict(id='x', title='T', text='Moves in autumn.', when='Autumn')

    def test_key_goes_in_a_header_not_the_url_and_the_answer_is_read(self):
        seen = {}
        def fake(req, timeout=0): seen['req'] = req; return Resp('{"months":[9,10],"basis":"autumn"}')
        with mock.patch.object(g.fetch, 'urlopen', fake):
            r = g.ask(self.ROW, 'SECRETKEY')
        self.assertEqual(r['answer']['months'], [9, 10]); self.assertEqual(r['tokens']['promptTokenCount'], 10)
        self.assertNotIn('SECRETKEY', seen['req'].full_url); self.assertEqual(seen['req'].get_header('X-goog-api-key'), 'SECRETKEY')

    def test_an_error_does_not_echo_the_key(self):
        import urllib.error
        def fake(req, timeout=0): raise urllib.error.HTTPError('u', 429, 'x', {}, io.BytesIO(b'quota'))
        with mock.patch.object(g.fetch, 'urlopen', fake):
            r = g.ask(self.ROW, 'SECRETKEY')
        self.assertEqual(r['error'], 'HTTP 429'); self.assertNotIn('SECRETKEY', json.dumps(r))

    def test_unreadable_answer_is_an_error(self):
        with mock.patch.object(g.fetch, 'urlopen', lambda req, timeout=0: Resp('not json')):
            self.assertEqual(g.ask(self.ROW, 'k')['error'], 'unreadable answer')


class ValidTests(unittest.TestCase):
    def test_months_must_be_1_to_12_and_basis_present(self):
        self.assertIsNone(g.valid({'months': [1, 12], 'basis': 'x'}))
        self.assertIsNone(g.valid({'months': [], 'basis': 'no season in the text'}))
        self.assertIsNotNone(g.valid({'months': [0], 'basis': 'x'}))
        self.assertIsNotNone(g.valid({'months': ['3'], 'basis': 'x'}))
        self.assertIsNotNone(g.valid({'months': [3], 'basis': ' '}))


class CapsTests(unittest.TestCase):
    def test_the_row_cap_and_the_listed_journeys_exist(self):
        self.assertLessEqual(len(g.JOURNEYS[:g.MAX_ROWS]), 5)
        for j in g.JOURNEYS: self.assertTrue(g.load(j)['title'], j)

    def test_no_key_stops_the_run(self):
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit): g.main()


if __name__ == '__main__': unittest.main()
