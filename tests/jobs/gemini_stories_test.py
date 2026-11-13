#!/usr/bin/env python3
import io, json, os, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import gemini_stories as g

SRC = 'Lake Park is in Utah, USA. It covers 7,927 km2 and is 1,500 m high. Elk and Moose live here. Established in 1962.'


class CheckTests(unittest.TestCase):
    def test_a_draft_with_only_source_facts_passes(self):
        self.assertIsNone(g.check({'story': 'Lake Park is in Utah, USA and covers 7,927 km2.', 'matters': 'Elk and Moose live here.'}, SRC))

    def test_word_limits(self):
        self.assertIn('story has', g.check({'story': ' '.join(['word'] * 61), 'matters': 'ok'}, SRC))
        self.assertIn('matters has', g.check({'story': 'ok', 'matters': ' '.join(['word'] * 41)}, SRC))
        self.assertIsNone(g.check({'story': ' '.join(['the'] * 60), 'matters': ' '.join(['the'] * 40)}, SRC))

    def test_a_number_not_in_the_source_is_rejected(self):
        self.assertIn('1963', g.check({'story': 'It was set up in 1963.', 'matters': 'Elk live here.'}, SRC))
        self.assertIsNone(g.check({'story': 'It was set up in 1962.', 'matters': 'Elk live here.'}, SRC))

    def test_an_invented_name_is_rejected_but_a_sentence_start_is_not(self):
        r = g.check({'story': 'It shelters Wolves and Bears.', 'matters': 'Elk live here.'}, SRC)
        self.assertIn('Wolves', r)
        self.assertIsNone(g.check({'story': 'Utah has it. Moose live here.', 'matters': 'Elk live here.'}, SRC))

    def test_empty_is_rejected(self):
        self.assertIsNotNone(g.check({'story': '', 'matters': 'x'}, SRC))


class AskTests(unittest.TestCase):
    class Resp:
        def __init__(self, obj): self.b = json.dumps({'candidates': [{'content': {'parts': [{'text': json.dumps(obj)}]}}], 'usageMetadata': {'promptTokenCount': 9, 'candidatesTokenCount': 4}}).encode()
        def read(self): return self.b

    def test_key_is_in_a_header_and_the_answer_is_read(self):
        seen = {}
        def fake(req, timeout=0): seen['r'] = req; return self.Resp({'story': 'a', 'matters': 'b'})
        with mock.patch.object(g.fetch, 'urlopen', fake):
            r = g.ask('N', 'W', 'K', SRC, 'SECRETKEY')
        self.assertEqual(r['draft']['story'], 'a'); self.assertNotIn('SECRETKEY', seen['r'].full_url)
        self.assertNotIn(b'SECRETKEY', seen['r'].data)

    def test_a_429_with_a_long_delay_stops_the_run_and_a_short_one_is_waited_for(self):
        import urllib.error
        long429 = lambda req, timeout=0: (_ for _ in ()).throw(urllib.error.HTTPError('u', 429, 'x', {}, io.BytesIO(b'{"retryDelay": "3000s"}')))
        with mock.patch.object(g.fetch, 'urlopen', long429), self.assertRaises(g.QuotaStop): g.ask('N', 'W', 'K', SRC, 'k')
        calls = []
        def short_then_ok(req, timeout=0):
            calls.append(1)
            if len(calls) == 1: raise urllib.error.HTTPError('u', 429, 'x', {}, io.BytesIO(b'{"retryDelay": "2s"}'))
            return self.Resp({'story': 'a', 'matters': 'b'})
        with mock.patch.object(g.fetch, 'urlopen', short_then_ok), mock.patch.object(g.time, 'sleep', lambda s: None):
            self.assertEqual(g.ask('N', 'W', 'K', SRC, 'k')['draft']['story'], 'a')
        self.assertEqual(len(calls), 2)

    def test_a_503_is_retried_after_a_pause_and_then_given_up(self):
        import urllib.error
        calls = []
        def busy_then_ok(req, timeout=0):
            calls.append(1)
            if len(calls) < 3: raise urllib.error.HTTPError('u', 503, 'x', {}, io.BytesIO(b'{}'))
            return self.Resp({'story': 'a', 'matters': 'b'})
        with mock.patch.object(g.fetch, 'urlopen', busy_then_ok), mock.patch.object(g.time, 'sleep', lambda s: None):
            self.assertEqual(g.ask('N', 'W', 'K', SRC, 'k')['draft']['story'], 'a')
        always = lambda req, timeout=0: (_ for _ in ()).throw(urllib.error.HTTPError('u', 503, 'x', {}, io.BytesIO(b'{}')))
        with mock.patch.object(g.fetch, 'urlopen', always), mock.patch.object(g.time, 'sleep', lambda s: None), self.assertRaises(g.Overloaded): g.ask('N', 'W', 'K', SRC, 'k')

    def test_retry_delay_reads_the_google_message_and_assumes_long_when_missing(self):
        self.assertEqual(g.retry_delay(b'{"retryDelay": "32s"}'), 33); self.assertEqual(g.retry_delay(b'nothing'), 3600)


class RunTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.res = os.path.join(self.d, 'res'); self.out = os.path.join(self.d, 'out'); self.data = os.path.join(self.d, 'data')
        os.makedirs(os.path.join(self.res, 'research')); os.makedirs(self.data); os.makedirs(self.out)
        for pid, story in (('aa', ''), ('bb', ''), ('cc', ''), ('dd', 'has a story'), ('ee', '')):
            json.dump({'id': pid, 'name': 'Place ' + pid, 'country': 'X', 'kind': 'Forest', 'story': story}, open(os.path.join(self.data, pid + '.json'), 'w'))
            if pid != 'ee': open(os.path.join(self.res, 'research', pid + '.md'), 'w').write(SRC)   # ee has no research file

    def test_only_places_with_research_and_no_story_are_chosen_in_id_order(self):
        self.assertEqual([t[0] for t in g.todo(self.res, self.out, False, self.data)], ['aa', 'bb', 'cc'])

    def run_main(self, answers, limit='15'):
        it = iter(answers)
        def fake_ask(name, where, kind, source, key):
            a = next(it)
            if a == 'QUOTA': raise g.QuotaStop('x')
            if a == 'BUSY': raise g.Overloaded('HTTP 503')
            return a
        todo_real = g.todo
        with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'k'}), mock.patch.object(sys, 'argv', ['x', self.res, self.out, limit]), \
                mock.patch.object(g, 'ask', fake_ask), mock.patch.object(g, 'GAP', 0), \
                mock.patch.object(g, 'todo', lambda r, o, a: todo_real(r, o, a, self.data)):
            g.main()

    def ok(self, s='Lake Park is in Utah, USA.'): return dict(draft={'story': s, 'matters': 'Elk live here.'}, tokens={'promptTokenCount': 5, 'candidatesTokenCount': 3})

    def test_a_quota_stop_keeps_the_drafts_and_the_next_run_resumes(self):
        self.run_main([self.ok(), 'QUOTA'])
        self.assertTrue(os.path.exists(os.path.join(self.out, 'aa.json'))); self.assertFalse(os.path.exists(os.path.join(self.out, 'bb.json')))
        self.run_main([self.ok(), self.ok()])
        self.assertTrue(all(os.path.exists(os.path.join(self.out, p + '.json')) for p in ('aa', 'bb', 'cc')))
        self.assertIn('Place aa', open(os.path.join(self.out, 'REVIEW-01.md')).read())

    def test_a_busy_place_is_skipped_and_the_run_stops_after_three_in_a_row(self):
        self.run_main(['BUSY', self.ok(), self.ok()])
        self.assertTrue(all(os.path.exists(os.path.join(self.out, p + '.json')) for p in ('bb', 'cc'))); self.assertFalse(os.path.exists(os.path.join(self.out, 'aa.json')))
        self.run_main(['BUSY', 'BUSY', 'BUSY'])   # a fourth place would have raised StopIteration: the run stopped before asking it

    def test_a_failed_check_is_kept_as_rejected_and_not_asked_again(self):
        self.run_main([self.ok('Lake Park was founded in 1999.'), self.ok(), self.ok()])
        self.assertTrue(os.path.exists(os.path.join(self.out, 'rejected', 'aa.json'))); self.assertFalse(os.path.exists(os.path.join(self.out, 'aa.json')))
        self.assertEqual([t[0] for t in g.todo(self.res, self.out, False, self.data)], [])
        self.assertEqual([t[0] for t in g.todo(self.res, self.out, True, self.data)], ['aa'])

    def test_the_limit_and_the_hard_cap_apply_and_no_place_file_is_changed(self):
        before = {f: open(os.path.join(self.data, f)).read() for f in os.listdir(self.data)}
        self.run_main([self.ok(), self.ok(), self.ok()], limit='1')
        self.assertEqual(sorted(p for p in os.listdir(self.out) if p.endswith('.json')), ['aa.json'])
        self.assertEqual(before, {f: open(os.path.join(self.data, f)).read() for f in os.listdir(self.data)})
        self.assertLessEqual(g.MAX_ROWS, 150)

    def test_limit_zero_means_all_left_and_the_review_is_split_into_pages(self):
        for i in range(17):
            pid = 'p%02d' % i
            json.dump({'id': pid, 'name': 'Place ' + pid, 'story': '', 'matters': ''}, open(os.path.join(self.data, pid + '.json'), 'w'))
            open(os.path.join(self.res, 'research', pid + '.md'), 'w').write(SRC)
        self.run_main([self.ok() for _ in range(20)], limit='0')
        files = sorted(f for f in os.listdir(self.out) if f.startswith('REVIEW'))
        self.assertEqual(files, ['REVIEW-01.md', 'REVIEW-02.md', 'REVIEW.md'])
        self.assertIn('REVIEW-02.md', open(os.path.join(self.out, 'REVIEW.md')).read())


if __name__ == '__main__': unittest.main()
