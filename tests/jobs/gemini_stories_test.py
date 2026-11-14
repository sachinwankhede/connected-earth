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
        def fake_ask(name, where, kind, source, key, model=None):
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

    def test_an_unknown_model_is_refused_before_any_request(self):
        with mock.patch.object(g, 'MODEL', 'gemini-9-ultra'), mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'k'}), mock.patch.object(sys, 'argv', ['x', self.res, self.out]), self.assertRaises(SystemExit): g.main()

    def chain_run(self, quota_for, chain='gemini-3.5-flash-lite,gemini-3.1-flash-lite'):
        asked = []
        def fake_ask(name, where, kind, source, key, model=None):
            asked.append((name, model))
            if model in quota_for: raise g.QuotaStop('x')
            return self.ok()
        todo_real = g.todo
        with mock.patch.dict(os.environ, {'GEMINI_API_KEY': 'k'}), mock.patch.object(sys, 'argv', ['x', self.res, self.out, '15']), mock.patch.object(g, 'MODEL', chain), \
                mock.patch.object(g, 'ask', fake_ask), mock.patch.object(g, 'GAP', 0), mock.patch.object(g, 'todo', lambda r, o, a: todo_real(r, o, a, self.data)):
            g.main()
        return asked

    def test_when_a_model_is_out_of_quota_the_next_one_takes_the_same_place_and_is_recorded(self):
        asked = self.chain_run({'gemini-3.5-flash-lite'})
        self.assertEqual(asked[:2], [('Place aa', 'gemini-3.5-flash-lite'), ('Place aa', 'gemini-3.1-flash-lite')])
        self.assertNotIn('gemini-3.5-flash-lite', [m for _, m in asked[2:]])   # not asked again this run
        self.assertEqual(json.load(open(os.path.join(self.out, 'aa.json')))['model'], 'gemini-3.1-flash-lite')
        self.assertTrue(all(os.path.exists(os.path.join(self.out, p + '.json')) for p in ('aa', 'bb', 'cc')))

    def test_when_every_model_is_out_the_run_stops_and_an_unknown_one_in_the_list_is_refused(self):
        asked = self.chain_run({'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite'})
        self.assertEqual(len(asked), 2); self.assertFalse(os.path.exists(os.path.join(self.out, 'aa.json')))
        with self.assertRaises(SystemExit): self.chain_run(set(), 'gemini-3.5-flash-lite,gemini-9-ultra')

    def test_the_prompt_asks_for_fewer_words_than_the_limits_and_bans_coordinates(self):
        self.assertIn('at most %d words' % (g.STORY_WORDS - 10), g.SYSTEM); self.assertIn('at most %d words' % (g.WHY_WORDS - 6), g.SYSTEM)
        self.assertIn('Never write latitude or longitude', g.SYSTEM); self.assertEqual(g.PROMPT_VERSION, 'stories-2')

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


class GeminiApiTests(unittest.TestCase):
    """The shared calling module lib/gemini_api.py (#772). Kept in this file because it is already listed in ci.yml (owner-merged)."""
    def test_chain_hands_over_resets_busy_and_stops_when_all_are_out(self):
        import gemini_api as api
        c = api.Chain('a, b', ('a', 'b', 'c'))
        self.assertEqual((c.current, c.exhausted), ('a', False))
        c.busy_row = 2
        self.assertIn('trying b', c.out('quota')); self.assertEqual((c.current, c.busy_row), ('b', 0))
        self.assertNotIn('trying', c.out('busy')); self.assertTrue(c.exhausted); self.assertEqual(c.out_of, ['a', 'b'])

    def test_chain_refuses_unknown_or_empty(self):
        import gemini_api as api
        with self.assertRaises(ValueError): api.Chain('a,zzz', ('a',))
        with self.assertRaises(ValueError): api.Chain(' , ', ('a',))

    def test_request_body_has_system_only_when_given(self):
        import gemini_api as api
        b = api.request_body('SYS', 'hello', {'type': 'OBJECT'}, temperature=0.2, max_out=50)
        self.assertEqual(b['systemInstruction']['parts'][0]['text'], 'SYS'); self.assertEqual(b['generationConfig']['maxOutputTokens'], 50)
        self.assertNotIn('systemInstruction', api.request_body(None, 'hello', {}))

    def test_generate_reads_the_answer_without_retries_for_other_errors_and_can_skip_busy_retries(self):
        import gemini_api as api, urllib.error
        ok = lambda req, timeout=0: AskTests.Resp({'x': 1})
        with mock.patch.object(api.fetch, 'urlopen', ok):
            r = api.generate('m', {}, 'k'); self.assertEqual(r['answer'], {'x': 1}); self.assertEqual(r['tokens']['promptTokenCount'], 9)
        bad = lambda req, timeout=0: (_ for _ in ()).throw(urllib.error.HTTPError('u', 400, 'x', {}, io.BytesIO(b'no')))
        with mock.patch.object(api.fetch, 'urlopen', bad): self.assertEqual(api.generate('m', {}, 'k')['error'], 'HTTP 400')
        calls = []
        def busy(req, timeout=0): calls.append(1); raise urllib.error.HTTPError('u', 503, 'x', {}, io.BytesIO(b'{}'))
        with mock.patch.object(api.fetch, 'urlopen', busy), mock.patch.object(api.time, 'sleep', lambda s: None), self.assertRaises(api.Overloaded): api.generate('m', {}, 'k', busy_waits=())
        self.assertEqual(len(calls), 1)


class LlmInterfaceTests(unittest.TestCase):
    """lib/llm.py (#779 step a), the provider interface over gemini_api. Kept in this file because it is already listed in ci.yml (owner-merged)."""
    class Fake:
        def __init__(self, script): self.script = list(script); self.seen = []; self.models = ('a', 'b')
        def generate(self, model, system, text, schema, key, temperature=0, max_out=600, **kw):
            self.seen.append(model); x = self.script.pop(0)
            if isinstance(x, Exception): raise x
            return dict(x)

    def test_the_gemini_adapter_builds_the_request_and_is_registered(self):
        import llm, gemini_api
        p = llm.get('gemini'); self.assertIsInstance(p, llm.GeminiProvider)
        got = {}
        def fake(model, body, key, **kw): got.update(model=model, body=body, key=key); return {'answer': {'ok': 1}}
        with mock.patch.object(gemini_api, 'generate', fake):
            r = p.generate(p.models[0], 'SYS', 'hi', {'type': 'OBJECT'}, 'K', temperature=0.3, max_out=70)
        self.assertEqual(r, {'answer': {'ok': 1}}); self.assertEqual((got['key'], got['model']), ('K', p.models[0]))
        self.assertEqual(got['body']['systemInstruction']['parts'][0]['text'], 'SYS'); self.assertEqual(got['body']['generationConfig']['maxOutputTokens'], 70)
        with self.assertRaises(ValueError): llm.get('nope')
        with self.assertRaises(ValueError): llm.chain_for(p, 'not-a-model')

    def test_the_error_classes_are_the_ones_in_gemini_api(self):
        import llm, gemini_api
        self.assertIs(llm.QuotaStop, gemini_api.QuotaStop); self.assertIs(llm.Overloaded, gemini_api.Overloaded)

    def test_complete_names_the_model_and_drops_one_that_is_out_of_quota(self):
        import llm
        f = self.Fake([llm.QuotaStop('daily'), {'answer': {'x': 1}}]); c = llm.Chain('a,b', f.models); lines = []
        r = llm.complete(f, c, None, 't', {}, 'k', log=lines.append)
        self.assertEqual((r['answer'], r['model'], f.seen), ({'x': 1}, 'b', ['a', 'b'])); self.assertEqual(len(lines), 1); self.assertIn('MODEL OUT: a', lines[0])

    def test_complete_drops_a_model_only_after_busy_items_in_a_row_and_a_success_resets_the_count(self):
        import llm
        busy = llm.Overloaded('HTTP 503')
        f = self.Fake([busy, busy, {'answer': 1}, busy, busy, busy, {'answer': 2}]); c = llm.Chain('a,b', f.models)
        self.assertEqual(llm.complete(f, c, None, 't', {}, 'k')['error'], 'busy')
        self.assertEqual(llm.complete(f, c, None, 't', {}, 'k')['error'], 'busy')
        self.assertEqual(llm.complete(f, c, None, 't', {}, 'k')['model'], 'a'); self.assertEqual(c.busy_row, 0)
        self.assertEqual(llm.complete(f, c, None, 't', {}, 'k')['error'], 'busy'); self.assertEqual(llm.complete(f, c, None, 't', {}, 'k')['error'], 'busy')
        r = llm.complete(f, c, None, 't', {}, 'k'); self.assertEqual((r['answer'], r['model']), (2, 'b')); self.assertEqual(c.out_of, ['a'])

    def test_complete_says_no_model_left_and_keeps_a_bad_answer_without_dropping_the_model(self):
        import llm
        f = self.Fake([{'error': 'unreadable answer'}, llm.QuotaStop('q'), llm.QuotaStop('q')]); c = llm.Chain('a,b', f.models)
        r = llm.complete(f, c, None, 't', {}, 'k'); self.assertEqual((r['error'], r['model'], c.out_of), ('unreadable answer', 'a', []))
        self.assertEqual(llm.complete(f, c, None, 't', {}, 'k'), {'error': 'no model left'}); self.assertTrue(c.exhausted)


class AiTaskRunnerTests(unittest.TestCase):
    """jobs/ai_task.py (#779 step a), the generic runner. Kept in this file because it is already listed in ci.yml (owner-merged)."""
    def setUp(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
        import ai_task, llm
        self.t, self.llm = ai_task, llm; self.out = tempfile.mkdtemp()
        class Toy(ai_task.Task):
            name = 'toy'; prompt_version = 'toy-1'
            def items(s, i, o, again): return [ai_task.Item(x, x.upper(), 'ask ' + x, 'src ' + x) for x in ('a', 'b', 'c', 'd') if not os.path.exists(os.path.join(o, x + '.json')) and (again or not os.path.exists(os.path.join(o, 'rejected', x + '.json')))]
            def check(s, ans, src, it=None): return 'too long' if len(ans.get('v', '')) > 3 else None
            def review(s, o): s.reviewed = True
        self.Toy = Toy
    def run_task(self, script, limit=0, again=False, models='m1,m2'):
        f = LlmInterfaceTests.Fake(script); f.models = ('m1', 'm2'); task = self.Toy(); lines = []
        n = self.t.run(task, 'in', self.out, limit, again, self.llm.Chain(models, f.models), 'k', provider=f, gap=0, log=lines.append, sleep=lambda s: None)
        return n, f, task, lines
    ok = staticmethod(lambda v: {'answer': {'v': v}, 'tokens': {'promptTokenCount': 5, 'candidatesTokenCount': 2}})

    def test_accepted_and_rejected_drafts_are_written_with_the_run_fields_and_counted(self):
        n, f, task, lines = self.run_task([self.ok('ab '), self.ok('toolong')], limit=2)
        self.assertEqual((n['accepted'], n['rejected'], n['tokens_in'], n['tokens_out']), (1, 1, 10, 4)); self.assertTrue(task.reviewed)
        a = json.load(open(os.path.join(self.out, 'a.json'))); self.assertEqual((a['v'], a['id'], a['name'], a['model'], a['prompt']), ('ab', 'a', 'A', 'm1', 'toy-1'))
        r = json.load(open(os.path.join(self.out, 'rejected', 'b.json'))); self.assertEqual(r['rejected'], 'too long')

    def test_the_next_run_resumes_and_again_asks_rejected_items_once_more(self):
        self.run_task([self.ok('ab'), self.ok('toolong')], limit=2)
        n, f, task, lines = self.run_task([self.ok('c1'), self.ok('d1')]); self.assertEqual((n['accepted'], f.seen), (2, ['m1', 'm1']))   # a is done, b was rejected: c and d only
        n, f, task, lines = self.run_task([self.ok('b1')], again=True); self.assertEqual((n['accepted'], f.seen), (1, ['m1']))

    def test_a_model_out_of_quota_hands_over_and_all_out_stops_cleanly_keeping_what_was_written(self):
        q = self.llm.QuotaStop('daily')
        n, f, task, lines = self.run_task([self.ok('x1'), q, self.ok('y1'), q])
        self.assertEqual((n['accepted'], n['stopped'], f.seen), (2, True, ['m1', 'm1', 'm2', 'm2'])); self.assertTrue(any('STOP: every model is out' in l for l in lines))
        self.assertTrue(os.path.exists(os.path.join(self.out, 'a.json')) and os.path.exists(os.path.join(self.out, 'b.json')))

    def test_a_busy_item_is_skipped_and_the_limit_is_respected(self):
        n, f, task, lines = self.run_task([self.llm.Overloaded('HTTP 503'), self.ok('ok')], limit=2)
        self.assertEqual((n['skipped'], n['accepted']), (1, 1)); self.assertFalse(os.path.exists(os.path.join(self.out, 'a.json')))

    def test_the_stories_task_lists_places_like_the_job_and_builds_its_prompt_from_the_research(self):
        d = tempfile.mkdtemp(); res = os.path.join(d, 'research'); os.makedirs(res); pl = os.path.join(d, 'places'); os.makedirs(pl)
        json.dump({'id': 'p1', 'name': 'Lake Park', 'country': 'Utah', 'kind': 'park'}, open(os.path.join(pl, 'p1.json'), 'w')); open(os.path.join(res, 'p1.md'), 'w').write(SRC)
        task = self.t.Stories()
        with mock.patch.object(g, 'todo', lambda r, o, a: g.todo.__wrapped__(r, o, a, pl) if hasattr(g.todo, '__wrapped__') else [('p1', 'Lake Park', 'Utah', 'park')]):
            its = task.items(d, self.out, False)
        self.assertEqual([i.id for i in its], ['p1']); self.assertIn('SOURCE TEXT:\n' + SRC, its[0].text); self.assertEqual(its[0].source, SRC)
        self.assertEqual((task.system, task.prompt_version), (g.SYSTEM, g.PROMPT_VERSION)); self.assertIsNone(task.check({'story': 'Lake Park is in Utah, USA.', 'matters': 'Elk live here.'}, SRC))


class JudgeTaskTests(unittest.TestCase):
    """The judge task in jobs/ai_task.py (#779 step b). Kept in this file because it is already listed in ci.yml (owner-merged)."""
    def setUp(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
        import ai_task, llm
        self.t, self.llm = ai_task, llm; self.d = tempfile.mkdtemp(); self.res = os.path.join(self.d, 'research'); os.makedirs(self.res)
        self.out = os.path.join(self.d, 'out'); os.makedirs(self.out)
    def draft(self, pid, story, matters='Elk live here.', model='gemini-3.5-flash-lite'):
        json.dump({'id': pid, 'name': pid.upper(), 'story': story, 'matters': matters, 'model': model}, open(os.path.join(self.out, pid + '.json'), 'w')); open(os.path.join(self.res, pid + '.md'), 'w').write(SRC)
    def run_judge(self, script, again=False):
        f = LlmInterfaceTests.Fake(script); f.models = ('gemini-3.1-flash-lite', 'gemini-3.8-flash'); lines = []
        n = self.t.run(self.t.Judge(), self.d, self.out, 0, again, self.llm.Chain(','.join(f.models), f.models), 'k', provider=f, gap=0, log=lines.append, sleep=lambda s: None)
        return n, f
    ok = staticmethod(lambda: {'answer': {'verdict': 'ok', 'problems': [], 'reason': 'supported'}, 'tokens': {}})
    flag = staticmethod(lambda: {'answer': {'verdict': 'flag', 'problems': ['"1963" is not in the source'], 'reason': 'invented date'}, 'tokens': {}})

    def test_passes_and_flags_are_filed_apart_with_the_writer_model_and_only_flags_are_listed_for_reading(self):
        self.draft('a', 'Lake Park is in Utah.'); self.draft('b', 'It was set up in 1963 in Utah.')
        n, f = self.run_judge([self.ok(), self.flag()])
        self.assertEqual((n['accepted'], n['rejected']), (1, 1))
        ok = json.load(open(os.path.join(self.out, 'judge', 'a.json'))); fl = json.load(open(os.path.join(self.out, 'judge', 'rejected', 'b.json')))
        self.assertEqual((ok['verdict'], ok['writer_model'], ok['model']), ('ok', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite')); self.assertIn('1963', fl['rejected'])
        md = open(os.path.join(self.out, 'JUDGE-FLAGGED.md')).read(); self.assertIn('`b`', md); self.assertNotIn('`a`', md); self.assertIn('1 passed, 1 flagged', md)
        self.assertTrue(os.path.exists(os.path.join(self.out, 'a.json')))   # the drafts themselves are untouched

    def test_the_prompt_carries_the_draft_and_the_source_and_a_judged_draft_is_not_asked_again(self):
        self.draft('a', 'Lake Park is in Utah.')
        item = self.t.Judge().items(self.d, self.out, False)[0]
        n, f = self.run_judge([self.ok()]); n2, f2 = self.run_judge([]); self.assertEqual((n['accepted'], f2.seen), (1, []))
        self.assertIn('STORY: Lake Park is in Utah.', item.text); self.assertIn('SOURCE TEXT:\n' + SRC, item.text)

    def test_near_duplicate_drafts_are_flagged_by_the_text_comparison_even_when_the_model_says_ok(self):
        same = 'Lake Park is in Utah and it covers a large area of high dry land with elk.'
        self.draft('a', same); self.draft('b', same); self.draft('c', 'Moose wade in cold ponds near Lake Park in the north.')
        n, f = self.run_judge([self.ok(), self.ok(), self.ok()])
        self.assertEqual((n['accepted'], n['rejected']), (1, 2)); self.assertIn('near-duplicate of the draft for b', json.load(open(os.path.join(self.out, 'judge', 'rejected', 'a.json')))['rejected'])

    def test_only_flagging_models_differ_from_the_writer_by_default_and_the_branch_is_the_drafts_branch(self):
        j = self.t.Judge(); self.assertNotIn(self.t.Stories().models[0], j.models); self.assertEqual((j.branch, self.t.Stories().branch), ('gemini-stories', 'gemini-stories'))


class StoryBatchTests(unittest.TestCase):
    """jobs/story_batch.py (#779 step c). Kept in this file because it is already listed in ci.yml (owner-merged)."""
    def setUp(self):
        import story_batch; self.sb = story_batch
        self.d = tempfile.mkdtemp(); self.dr = os.path.join(self.d, 'drafts'); self.da = os.path.join(self.d, 'places'); os.makedirs(self.da); os.makedirs(os.path.join(self.dr, 'judge', 'rejected')); os.makedirs(os.path.join(self.dr, 'rejected'))
    def put(self, path, obj): os.makedirs(os.path.dirname(path), exist_ok=True); json.dump(obj, open(path, 'w'))
    def draft(self, pid, judged=None, story_in_place=False, place=True):
        self.put(os.path.join(self.dr, pid + '.json'), {'id': pid, 'name': pid.upper(), 'story': 'S ' + pid, 'matters': 'M ' + pid, 'model': 'w'})
        if place: self.put(os.path.join(self.da, pid + '.json'), dict({'id': pid, 'name': pid}, **({'story': 'old'} if story_in_place else {})))
        if judged == 'ok': self.put(os.path.join(self.dr, 'judge', pid + '.json'), {'id': pid, 'verdict': 'ok', 'model': 'j'})
        if judged == 'flag': self.put(os.path.join(self.dr, 'judge', 'rejected', pid + '.json'), {'id': pid, 'name': pid.upper(), 'rejected': 'invented date', 'model': 'j'})

    def test_only_judge_passed_drafts_for_places_without_a_story_are_chosen_in_id_order_up_to_n(self):
        self.draft('a', 'ok'); self.draft('b', 'flag'); self.draft('c'); self.draft('d', 'ok', story_in_place=True); self.draft('e', 'ok', place=False); self.draft('f', 'ok'); self.draft('g', 'ok')
        chosen, flagged, c = self.sb.select(self.dr, self.da, 2)
        self.assertEqual([x['id'] for x in chosen], ['a', 'f']); self.assertEqual(list(flagged), ['b'])
        self.assertEqual((c['drafts'], c['passed'], c['flagged'], c['unjudged'], c['qualified'], c['has_story'], c['missing_place']), (7, 5, 1, 1, 3, 1, 1))

    def test_a_pass_file_does_not_count_when_a_flag_file_also_exists(self):
        self.draft('a', 'ok'); self.put(os.path.join(self.dr, 'judge', 'rejected', 'a.json'), {'id': 'a', 'rejected': 'x'})
        self.assertEqual(self.sb.select(self.dr, self.da, 5)[0], [])

    def test_the_spot_check_is_ten_evenly_spaced_items_or_all_when_fewer(self):
        mk = lambda n: [{'id': 'p%02d' % i} for i in range(n)]
        self.assertEqual(len(self.sb.spot_ids(mk(25))), 10); self.assertEqual(self.sb.spot_ids(mk(25))[0], 'p00'); self.assertEqual(len(set(self.sb.spot_ids(mk(25)))), 10); self.assertEqual(len(self.sb.spot_ids(mk(4))), 4)

    def test_main_writes_the_stories_and_a_body_with_counts_flags_sources_and_the_spot_check_and_exits_3_when_nothing_qualifies(self):
        import io, contextlib
        self.draft('a', 'ok'); self.draft('b', 'flag'); body = os.path.join(self.d, 'body.md')
        with mock.patch.object(sys, 'argv', ['x', self.dr, '--data', self.da, '--n', '5', '--body', body]), contextlib.redirect_stdout(io.StringIO()): self.sb.main()
        self.assertEqual(json.load(open(os.path.join(self.da, 'a.json')))['story'], 'S a'); self.assertNotIn('story', json.load(open(os.path.join(self.da, 'b.json'))))
        b = open(body).read(); self.assertIn('**1 stories**', b); self.assertIn('invented date', b); self.assertIn('Sources and licences', b); self.assertIn('10-item spot check', b); self.assertIn('- [ ] **A**', b); self.assertIn('Part of #779', b)
        with mock.patch.object(sys, 'argv', ['x', self.dr, '--data', self.da]), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as e: self.sb.main()
        self.assertEqual(e.exception.code, 3)


if __name__ == '__main__': unittest.main()
