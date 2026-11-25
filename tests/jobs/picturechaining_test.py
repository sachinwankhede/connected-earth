#!/usr/bin/env python3
"""#1183: chained picture runs. A run with a time budget stops cleanly and says `more: N` (exit 3); the next run continues with what is still untried; the last says 0; no source tries an item twice inside its hold.
Fake sources and a fake clock only: no network."""
import datetime, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import speciespictures as sj, species_photos as sp, runbudget
from speciespictures_test import new_root, unit, strategy, fake_copies

def always(name, found=(), miss=(), offered=None):
    """A fake source with a 30-day hold that applies to every species without a picture."""
    n, find, _, _ = strategy(name, found=found, miss=miss, offered=offered)
    return (n, find, lambda w, u: True, 30)

def ticking(step=60):
    t = [-step]
    def clock(): t[0] += step; return t[0]
    return clock

class ChainTests(unittest.TestCase):
    def setUp(self):
        self.d = new_root(); self.log = []; self.today = datetime.date(2026, 11, 25)
        self.sids = ['s%02d' % i for i in range(1, 9)]; self.units = [unit(s) for s in self.sids]
    def run_once(self, strategies, **kw):
        w = sp.SpeciesPhotos(self.d); report = {}   # a fresh writer, as every real run starts
        stats, stopped = sj.acquire(w, self.units, strategies, log=self.log.append, today=self.today, report=report, clock=ticking(), **kw)
        return report['more'], stopped, w

    def test_a_budgeted_run_stops_reports_more_and_the_chain_ends_with_none_and_no_repeats(self):
        offered = []; found = {'s02', 's05'}; miss = set(self.sids) - found
        mk = lambda: [always('commons', found=found, miss=miss, offered=offered)]
        runs = []
        for _ in range(20):
            more, stopped, w = self.run_once(mk(), minutes=2.5)
            runs.append(more); self.assertEqual(stopped, [])
            if not more: break
        self.assertGreater(runs[0], 0, 'the first run was stopped by its budget')
        self.assertEqual(runs[-1], 0); self.assertGreater(len(runs), 1)
        self.assertEqual(runs, sorted(runs, reverse=True)); self.assertEqual(len(set(runs)), len(runs), 'every run made progress')
        self.assertEqual(len(offered), len(set(offered)), 'no species is searched twice by the same source inside the hold')
        self.assertEqual(sorted(s for _, s in offered), self.sids)
        self.assertEqual(sorted(sp.SpeciesPhotos(self.d).pics), ['s02', 's05']); self.assertEqual(sp.SpeciesPhotos(self.d).check(), [])
        self.assertTrue(any('time budget' in l for l in self.log))

    def test_a_run_inside_the_hold_offers_nothing_and_reports_none(self):
        offered = []; mk = lambda: [always('commons', miss=set(self.sids), offered=offered)]
        self.run_once(mk()); n = len(offered); self.assertEqual(n, 8)
        more, _, _ = self.run_once(mk(), minutes=1); self.assertEqual((more, len(offered)), (0, n))
        self.today += datetime.timedelta(days=31)   # the hold has expired: due again
        self.run_once(mk()); self.assertEqual(len(offered), 2 * n)

    def test_a_transient_failure_is_not_counted_as_still_due_so_the_chain_cannot_loop(self):
        def find(todo):
            for u in todo: yield u, sj.Res('retry', why='the request failed')
        src = [('commons', find, lambda w, u: True, 30)]
        more, _, _ = self.run_once(src, minutes=2.5)   # tries three, stops
        self.assertEqual(more, len(self.sids) - 3)   # only the untried ones are due-and-untried

    def test_a_run_that_completes_with_the_copies_step_reports_none(self):
        more, _, _ = self.run_once([always('commons', found=set(self.sids))], minutes=None, copies=fake_copies)
        self.assertEqual(more, 0)

    def test_no_minutes_and_no_limit_tries_everything_in_one_run(self):
        offered = []; more, _, _ = self.run_once([always('commons', miss=set(self.sids), offered=offered)])
        self.assertEqual((more, len(offered)), (0, 8))

    def test_exit_codes(self):
        self.assertEqual(runbudget.exit_code([], 0), 0); self.assertEqual(runbudget.exit_code([], 5), 3)
        self.assertEqual(runbudget.exit_code(['commons'], 5), 2); self.assertEqual(runbudget.more_line(5), 'more: 5')

    def test_the_default_limit_is_all_and_the_default_budget_is_set(self):
        import inspect
        self.assertEqual(inspect.signature(sj.acquire).parameters['limit'].default, 0)
        self.assertIn("'--minutes', 120", inspect.getsource(sj.main))

if __name__ == '__main__': unittest.main()
