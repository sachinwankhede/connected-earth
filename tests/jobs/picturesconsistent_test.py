#!/usr/bin/env python3
"""#1183: the four picture jobs (species, places, journeys, nodes) behave the same: the same flags, the resume contract (`more: N`, exit 3), one {id: {source: date}} ledger with the 30-day hold, a failed larger copy held
like a source, the node ledger migrated by its writer, and the orphan list. Fake sources only: no network."""
import contextlib, datetime, io, json, os, sys, tempfile, time, unittest, unittest.mock
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'jobs')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'build'))
import nodepictures as nj, journeypictures as jj, speciespictures as sj, placepictures as pj, node_photos as np, journey_photos as jp, species_photos as sp, place_photos as pp, contracts
import nodepictures_test as nt, journeypictures_test as jt
from speciespictures_test import new_root, unit as sunit

DAY = datetime.date(2026, 11, 25)
def jpg(): return nt.jpeg()
def when(day): return datetime.datetime(day.year, day.month, day.day, tzinfo=datetime.timezone.utc)

def run_main(mod, argv, root, strategies):
    """The job's main() with fake sources, output captured: (exit code, printed text)."""
    old = mod.STRATEGIES; mod.STRATEGIES = strategies; out = io.StringIO(); t = [-60]
    def clock(): t[0] += 60; return t[0]   # a fake clock: every reading is a minute later, so `--minutes 1` stops after the first item
    try:
        with contextlib.redirect_stdout(out), unittest.mock.patch.object(time, 'monotonic', clock): code = mod.main(argv, root=root)
    finally: mod.STRATEGIES = old
    return code, out.getvalue()


class SameFlagsAndExitCodes(unittest.TestCase):
    def test_every_job_takes_the_same_flags_and_a_default_budget_of_120_minutes(self):
        import inspect
        for mod in (sj, pj, jj, nj):
            src = inspect.getsource(mod.main)
            for flag in ("'--strategy'", "'--limit'", "'--minutes', 120", "'--max-mb'", "'--again'", "'--dry'", "'--repair-limit'"): self.assertIn(flag, src, '%s lacks %s' % (mod.__name__, flag))

    def test_the_node_job_stops_on_its_budget_says_more_and_exits_3_then_finishes_with_0(self):
        d = nt.tree(); mk = lambda: [nt.strategy('wikipedia')]
        code, out = run_main(nj, ['--minutes', '1', '--repair-limit', '0'], d, mk())
        self.assertEqual(code, 3); self.assertIn('more: 1', out)
        code, out = run_main(nj, ['--repair-limit', '0'], d, mk())   # continues with what is untried
        self.assertEqual(code, 0); self.assertIn('more: 0', out)
        self.assertEqual(sorted(np.NodePhotos(d).tried), ['soil', 'sunbeam'])

    def test_the_journey_job_stops_on_its_budget_says_more_and_exits_3_then_finishes_with_0(self):
        d = jt.tree([('osprey', 'species', 'Osprey'), ('knot', 'species', 'Red knot')]); mk = lambda: [jt.strategy('wikipedia')]
        code, out = run_main(jj, ['--minutes', '1', '--repair-limit', '0'], d, mk())
        self.assertEqual(code, 3); self.assertIn('more: 1', out)
        code, out = run_main(jj, ['--repair-limit', '0'], d, mk())
        self.assertEqual(code, 0); self.assertIn('more: 0', out)
        self.assertEqual(sorted(jp.JourneyPhotos(d).tried), ['knot', 'osprey'])

    def test_a_source_that_stops_exits_2_and_an_unknown_strategy_exits_1(self):
        d = nt.tree()
        def find(todo):
            raise RuntimeError('throttled')
            yield
        rule = [s for s in nj.STRATEGIES if s[0] == 'commons'][0]
        code, out = run_main(nj, ['--repair-limit', '0'], d, [('commons', find, rule[2], rule[3])]); self.assertEqual(code, 2)
        self.assertEqual(run_main(nj, ['--strategy', 'nope'], d, nj.STRATEGIES)[0], 1); self.assertEqual(run_main(jj, ['--strategy', 'nope'], d, jj.STRATEGIES)[0], 1)


class NodeLedger(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); os.makedirs(os.path.join(self.d, 'photos'))
        with open(os.path.join(self.d, 'photos', 'node_missing.json'), 'w') as f: json.dump({'soil': {'status': 'nophoto', 'attempts': 1, 'checkedAt': '2026-11-10T01:00:00+00:00', 'expiresAt': '2026-12-10T01:00:00+00:00'}}, f)

    def test_with_no_ledger_file_the_hold_is_read_from_the_missing_record_and_reading_writes_nothing(self):
        w = np.NodePhotos(self.d); self.assertEqual(w.tried, {'soil': {'wikipedia': '2026-11-10', 'commons': '2026-11-10'}})
        self.assertFalse(os.path.exists(os.path.join(self.d, 'photos', 'node_tried.json'))); self.assertEqual(w.check(), [])

    def test_seed_writes_the_ledger_once_and_a_later_read_uses_the_file(self):
        self.assertEqual(np.seed_tried(self.d), 1); self.assertEqual(np.seed_tried(self.d), 0)
        self.assertEqual(json.load(open(os.path.join(self.d, 'photos', 'node_tried.json'))), {'soil': {'commons': '2026-11-10', 'wikipedia': '2026-11-10'}})
        w = np.NodePhotos(self.d); w.note_tried('rain', 'commons', now=when(datetime.date(2026, 11, 20))); w.commit()
        self.assertEqual(np.NodePhotos(self.d).tried['rain'], {'commons': '2026-11-20'})

    def test_put_clears_the_ledger_and_a_stored_picture_cannot_be_noted_as_tried(self):
        w = np.NodePhotos(self.d); w.put('soil', nt.row('soil'), jpg()); self.assertNotIn('soil', w.tried)
        with self.assertRaises(ValueError): w.note_tried('soil', 'commons')
        w.note_copy_tried('soil', now=when(datetime.date(2026, 11, 20)))
        self.assertTrue(w.copy_held('soil', DAY)); self.assertFalse(w.copy_held('soil', DAY + datetime.timedelta(days=contracts.SOURCE_RETRY_DAYS)))

    def test_the_author_repair_ledger_entry_works_like_the_other_kinds(self):
        w = np.NodePhotos(self.d); w.put('soil', nt.row('soil'), jpg()); w.note_repair_tried('soil'); self.assertIn('author-repair', w.tried['soil'])
        w.set_credit('soil', dict(a='A Name', l='CC BY 4.0', lu='x')); self.assertNotIn('soil', w.tried)

    def test_a_malformed_ledger_is_a_check_error_for_every_kind(self):
        for w in (np.NodePhotos(self.d), jp.JourneyPhotos(self.d), pp.PlacePhotos(self.d), sp.SpeciesPhotos(self.d)):
            w.tried = {'a': {'commons': 'yesterday'}, 'b': {}}; errs = w.check()
            self.assertEqual(sum('has no date' in e for e in errs), 1, type(w).__name__); self.assertEqual(sum('non-empty' in e for e in errs), 1)

    def test_orphans_lists_the_entries_no_place_shows_and_deletes_nothing(self):
        w = np.NodePhotos(self.d); w.put('rain', nt.row('rain'), jpg()); w.note_tried('hail', 'commons'); before = (dict(w.pics), dict(w.miss_), dict(w.tried))
        self.assertEqual(w.orphans({'rain'}), [('node_missing.json', 'soil'), ('node_tried.json', 'hail'), ('node_tried.json', 'soil')])
        self.assertEqual(w.orphans({'rain', 'soil', 'hail'}), []); self.assertEqual((w.pics, w.miss_, w.tried), before)

    def test_concepts_are_the_ids_and_titles_the_places_show(self):
        self.assertEqual(np.concepts(nt.tree()), {'sunbeam': 'Sunbeam', 'soil': 'Soil'})


class FailedCopiesAreHeldLikeASource(unittest.TestCase):
    def test_species_a_failed_copy_is_noted_held_for_30_days_and_due_again_after(self):
        d = new_root(); w = sp.SpeciesPhotos(d); w.put('s01', {'a': 'A B', 'l': 'CC BY 4.0', 'lu': 'x', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg', 'u': 'a/ab/X.jpg/330px-X.jpg', 'wiki': 'S'}, jpg()); w.commit()
        asked = []
        def bad(entry, need=('medium', 'large'), get=None): asked.append(need); return {}, 'no thumbnail'
        def go(days, **kw):
            w = sp.SpeciesPhotos(d); sj.acquire(w, [sunit('s01')], [], copies=bad, today=DAY + datetime.timedelta(days=days), log=lambda m: None, **kw)
        go(0); self.assertEqual(len(asked), 1); self.assertEqual(list(sp.SpeciesPhotos(d).tried['s01']), ['copy'])
        go(5); self.assertEqual(len(asked), 1, 'held: not offered')
        go(5, again=True); self.assertEqual(len(asked), 2)
        go(31); self.assertEqual(len(asked), 3)
        w = sp.SpeciesPhotos(d); both = ('medium', 'large')   # `more` is built from copy_files: a held copy is not due until its hold has expired
        self.assertEqual(len(sj.copy_files(w, both, DAY + datetime.timedelta(days=5), False)), 0)
        self.assertEqual(len(sj.copy_files(w, both, DAY + datetime.timedelta(days=40), False)), 1)
        self.assertEqual(len(sj.copy_files(w, both)), 1, 'no `today`: everything missing')

    def test_places_a_failed_larger_copy_is_noted_and_held(self):
        d = tempfile.mkdtemp(); w = pp.PlacePhotos(d); w.put('aa', {'a': 'A B', 'l': 'CC BY 4.0', 'lu': 'x', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg', 'f': 'aa.jpg', 'wiki': 'A'}, jpg()); w.commit(); asked = []
        def bad(e): asked.append(1); return None, 'no'
        for days, expect in ((0, 1), (3, 1), (31, 2)):
            w = pp.PlacePhotos(d)
            pj.acquire(w, [], [], only='large', large=bad, today=DAY + datetime.timedelta(days=days), log=lambda m: None)
            self.assertEqual(len(asked), expect)
        self.assertIn('copy', pp.PlacePhotos(d).tried['aa'])

    def test_journeys_a_failed_copy_is_noted_in_the_journey_ledger(self):
        d = jt.tree([('knot', 'species', 'Red knot')]); w = jj.Photos(d); w.put('knot', jt.row('knot'), jt.jpeg()); w.commit()
        w = jj.Photos(d); sj.acquire(w, jj.load_units(d), [], copies=lambda e, need=('large',), get=None: ({}, 'no thumbnail'), today=DAY, log=lambda m: None)
        self.assertEqual(list(jp.JourneyPhotos(d).tried['knot']), ['copy']); self.assertTrue(jp.JourneyPhotos(d).copy_held('knot', DAY))

    def test_nodes_have_no_copy_step_the_first_fetch_is_the_192_px_picture(self):
        d = nt.tree(); w = nj.Photos(d); units = nj.load_units(d); asked = []
        sj.acquire(w, units, [nt.strategy('wikipedia'), nt.strategy('commons', found={'soil'})], only='all', copies=lambda e, need=(), get=None: asked.append(need) or ({}, 'x'), today=DAY, log=lambda m: None)
        w = nj.Photos(d); self.assertTrue(w.has('soil')); self.assertNotIn('soil', w.tried.get('soil', {}).get('copy', '')); self.assertEqual(w.check(), []); self.assertEqual(asked, [])


class ValidatorWarnsAboutOrphans(unittest.TestCase):
    def test_the_validator_lists_node_orphans_as_a_warning_not_an_error(self):
        import inspect, validate_data
        src = inspect.getsource(validate_data.check)
        self.assertIn('npw.orphans(concept_ids)', src); self.assertIn("warns.append('photos/node_*.json", src)

if __name__ == '__main__': unittest.main()
