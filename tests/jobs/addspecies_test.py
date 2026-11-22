"""jobs/addspecies.py (docs/ADD-SPECIES.md): the job composes the sources through lib/species_rows.ensure; the sources are fakes here, so nothing is downloaded."""
import datetime, json, os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for d in ('jobs', 'lib', 'build'): sys.path.insert(0, os.path.join(ROOT, d))
import addspecies as A, species_rows as sr, creation_ledger as cl, species_photos, node_photos
from place_sources import Res

DAY = datetime.date(2026, 11, 22)
CREDIT = {'a': 'Jane Doe', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0', 'p': 'https://commons.wikimedia.org/wiki/File:X.jpg', 'wiki': 'X', 'page': 'https://en.wikipedia.org/wiki/X', 'u': 'a/b/X.jpg'}

class Fake:
    """Every source finds something unless told otherwise."""
    def __init__(self, **no): self.no = no; self.asked = []
    def picture(self, unit, kind):
        self.asked.append(('picture', unit['title']))
        if 'picture' in self.no: return None, ['wikipedia: no usable picture', 'gbif: refused (CC BY / BY-SA with no author)']
        return {'entry': dict(CREDIT, wiki=unit['title']), 'small': b'small-' + unit['sid'].encode(), 'copies': {'medium': b'm-' + unit['sid'].encode(), 'large': b'l-' + unit['sid'].encode()} if kind != 'resource' else {'medium': b'm-' + unit['sid'].encode()}, 'source': 'wikipedia', 'copy_note': ''}, ['wikipedia: found']
    def taxonomy(self, cand):
        self.asked.append(('taxonomy', cand['wiki']))
        return (None, 'no exact match') if 'taxonomy' in self.no else ({'kingdom': 'Animalia', 'rank': 'SPECIES', 'key': 77, 'match': 'exact', 'gname': 'x', 'src': 'gbif', 'at': '2026-11-22'}, '')
    def summary(self, title):
        self.asked.append(('summary', title))
        return (None, '', 'the page has no text') if 'summary' in self.no else ('The eastern coyote is a canid living in the east.', 'The eastern coyote is a canid living in the east. Second.', '')
    def conservation(self, latin):
        self.asked.append(('conservation', latin))
        return (None, 'no status on Wikidata') if 'conservation' in self.no else ({'c': 'LC', 'q': 'Q1'}, '')

def tree():
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, 'data', 'species', 'rows')); return d

def files(d): return sorted(os.path.relpath(os.path.join(b, f), d) for b, _, fs in os.walk(d) for f in fs)

TAXON = {'wiki': 'Eastern coyote', 'kind': 'taxon', 'latin': 'Canis latrans var', 'tl': 4, 'ic': 'coyote'}

class Job(unittest.TestCase):
    def test_a_taxon_is_added_with_all_its_files_and_the_row(self):
        d = tree(); res, stopped = A.run([TAXON], Fake(), d, dry=False, now=DAY, log=lambda *a: None)
        self.assertEqual((res[0]['status'], res[0]['id'], stopped), ('added', 'canis-latrans-var', None))
        sid = 'canis-latrans-var'
        self.assertTrue(os.path.exists(os.path.join(d, 'data', 'species', 'rows', 'ca', sid + '.json')))
        self.assertIn(sid, json.load(open(os.path.join(d, 'data', 'species', 'taxonomy.json'))))
        self.assertEqual(json.load(open(os.path.join(d, 'data', 'species', 'conservation.json')))[sid]['c'], 'LC')
        self.assertIn('Eastern coyote', json.load(open(os.path.join(d, 'data', 'species', 'about.json'))))
        w = species_photos.SpeciesPhotos(d); self.assertTrue(w.has(sid) and w.has_medium(sid) and w.has_large(sid)); self.assertEqual(w.check(), [])
        row = json.load(open(os.path.join(d, 'data', 'species', 'rows', 'ca', sid + '.json')))
        self.assertEqual((row['sk'], row['tl'], row['ic'], row['src'], row['at'], row['about'][:9]), ('taxon', 4, 'coyote', 'addspecies', '2026-11-22', 'The easte'))
        try:
            import jsonschema
            for kind, rec in (('species-row', row), ('taxonomy', {sid: json.load(open(os.path.join(d, 'data', 'species', 'taxonomy.json')))[sid]}), ('ledger', {})):
                jsonschema.validate(rec, json.load(open(os.path.join(ROOT, 'build', 'schemas', kind + '.schema.json'))))   # what the job writes is what the schemas accept
        except ImportError: pass
        self.assertEqual(sr.SpeciesRows(d).identify('Eastern coyote', 'taxon', 'Canis latrans var')['status'], 'exists')   # a second run finds it

    def test_a_missing_picture_refuses_runs_every_step_and_writes_only_the_ledger(self):
        d = tree(); f = Fake(picture=1, taxonomy=1)
        res, _ = A.run([TAXON], f, d, dry=False, now=DAY, log=lambda *a: None)
        self.assertEqual((res[0]['status'], res[0]['reason']), ('refused', 'picture'))
        self.assertEqual([s for s, _ in f.asked], ['picture', 'taxonomy', 'summary', 'conservation'])   # every step ran
        self.assertEqual(files(d), ['data/ledger/species.json'])
        rec = cl.Ledger('species', d).get('Eastern coyote')
        self.assertEqual({k: v['result'] for k, v in rec['steps'].items()}, {'identity': 'found', 'picture': 'missing', 'taxonomy': 'missing', 'summary': 'found', 'conservation': 'found'})
        self.assertIn('gbif: refused', rec['steps']['picture']['detail'])   # the ledger says which source refused and why: the priority list for the next source

    def test_no_summary_refuses_and_no_conservation_does_not(self):
        d = tree(); self.assertEqual(A.run([TAXON], Fake(summary=1), d, dry=False, now=DAY, log=lambda *a: None)[0][0]['reason'], 'summary')
        d = tree(); self.assertEqual(A.run([TAXON], Fake(conservation=1), d, dry=False, now=DAY, log=lambda *a: None)[0][0]['status'], 'added')

    def test_dry_run_writes_nothing(self):
        d = tree(); before = files(d); res, _ = A.run([TAXON, dict(TAXON, wiki='Other', latin='Other one')], Fake(), d, dry=True, now=DAY, log=lambda *a: None)
        self.assertEqual([r['status'] for r in res], ['added', 'added']); self.assertEqual(files(d), before)

    def test_a_resource_row_gets_a_node_picture_and_no_taxonomy(self):
        d = tree(); f = Fake(); c = {'wiki': 'Rain', 'kind': 'resource', 'cat': 'abiotic', 'ic': 'rain'}
        res, _ = A.run([c], f, d, dry=False, now=DAY, log=lambda *a: None)
        self.assertEqual((res[0]['status'], res[0]['id']), ('added', 'rain'))
        self.assertNotIn(('taxonomy', 'Rain'), f.asked); self.assertNotIn(('conservation', ''), f.asked)
        self.assertTrue(os.path.exists(os.path.join(d, 'data', 'nodes', 'rows', 'ra', 'rain.json')))
        n = node_photos.NodePhotos(d); self.assertTrue(n.has('rain')); self.assertEqual(n.check(), [])
        self.assertFalse(os.path.exists(os.path.join(d, 'data', 'species', 'taxonomy.json')))

    def test_a_known_species_is_not_looked_up_again(self):
        d = tree(); A.run([TAXON], Fake(), d, dry=False, now=DAY, log=lambda *a: None); f = Fake()
        res, _ = A.run([TAXON], f, d, dry=False, now=DAY, log=lambda *a: None)
        self.assertEqual((res[0]['status'], f.asked), ('exists', []))

    def test_a_stopped_source_ends_the_run_and_writes_nothing(self):
        class Boom(Fake):
            def picture(self, unit, kind): raise A.Stopped('wikipedia: too many throttles')
        d = tree(); res, stopped = A.run([TAXON, dict(TAXON, wiki='B', latin='B b')], Boom(), d, dry=False, now=DAY, log=lambda *a: None)
        self.assertEqual((res, bool(stopped), files(d)), ([], True, []))

    def test_one_bad_candidate_does_not_block_the_others_and_limit_counts_candidates(self):
        d = tree(); res, _ = A.run([{'wiki': 'x', 'kind': 'thing'}, {'wiki': 'y', 'kind': 'taxon'}, TAXON], Fake(), d, dry=True, now=DAY, log=lambda *a: None)
        self.assertEqual([r['status'] for r in res], ['refused', 'refused', 'added']); self.assertIn('kind must be', res[0]['reason']); self.assertIn('trophic level', res[1]['reason'])
        self.assertEqual(len(A.run([TAXON, dict(TAXON, wiki='B', latin='B b')], Fake(), tree(), dry=True, limit=1, log=lambda *a: None)[0]), 1)

    def test_the_summary_rules_are_the_ones_species_about_applies(self):
        self.assertEqual(A.summary_of('The coyote (Canis latrans) is a species of canine native to North America and far beyond.')[2], '')
        self.assertIn('not about', A.summary_of('Coyote may refer to: the animal, a film and a town in many places.')[2])
        self.assertIn('too short', A.summary_of('A small one.')[2]); self.assertIn('no text', A.summary_of('')[2])

class Report(unittest.TestCase):
    def test_report_lists_added_refused_and_known(self):
        d = tree(); A.run([TAXON], Fake(), d, dry=False, now=DAY, log=lambda *a: None)
        res, stopped = A.run([TAXON, dict(TAXON, wiki='Nopic', latin='No pic'), dict(TAXON, wiki='New one', latin='New one')], Fake(picture=1), d, dry=True, now=DAY, log=lambda *a: None)
        md = A.report(res, True, 'x')
        for part in ('(dry run: nothing written)', 'would add 0, already there 1, refused 2', '**a source stopped the run:** x', '**Already there:** Eastern coyote', 'Nopic: **picture**', 'Refusals by reason: picture 2'): self.assertIn(part, md)
        res, _ = A.run([dict(TAXON, wiki='Fine', latin='Fine one')], Fake(), d, dry=True, now=DAY, log=lambda *a: None)
        self.assertIn('wikipedia (CC BY 4.0, Jane Doe) | taxonomy found | summary found | conservation found', A.report(res, True))

    def test_main_writes_the_report_and_the_result_file(self):
        d = tree(); out = os.path.join(d, 'r.json'); rep = os.path.join(d, 'r.md')
        rc = A.main(['--titles', 'Canis one|Canis two', '--kind', 'taxon', '--tl', '4', '--dry', '--out', out, '--report', rep], root=d, src=Fake())
        self.assertEqual(rc, 0); self.assertEqual(len(json.load(open(out))), 2); self.assertIn('would add 2', open(rep).read())

class RealSourcesWithFakes(unittest.TestCase):
    """Sources.picture with fake source functions: the first accepted picture wins; a refusal is in the trail; an organism-only source skips a resource."""
    def make(self, sources, vet=None):
        s = A.Sources.__new__(A.Sources); s.get = None; s.sources = sources
        v = vet or (lambda e: (e, ''))
        class Spp:
            small = staticmethod(lambda raw: b'small'); make_copies = staticmethod(lambda e, need, get: ({k: b'x' for k in need}, ''))
        Spp.vet = staticmethod(v)
        s.spp = Spp; return s

    def test_first_accepted_wins_and_the_trail_lists_the_refusals(self):
        unit = {'sid': 'a', 'title': 'A', 'abiotic': False}
        found = lambda todo: [(todo[0], Res('found', dict(CREDIT), b'raw'))]
        miss = lambda todo: [(todo[0], Res('miss', why='no picture on the page', status='nophoto'))]
        s = self.make([('wikipedia', miss, lambda w, u: True, None), ('gbif', found, lambda w, u: True, None), ('openverse', found, lambda w, u: True, None)])
        got, trail = s.picture(unit, 'taxon')
        self.assertEqual((got['source'], sorted(got['copies']), trail), ('gbif', ['large', 'medium'], ['wikipedia: no picture on the page', 'gbif: found']))
        self.assertEqual(s.picture(dict(unit), 'resource')[0]['copies'].keys(), {'medium'})

    def test_an_author_refusal_goes_on_to_the_next_source(self):
        unit = {'sid': 'a', 'title': 'A', 'abiotic': False}; found = lambda todo: [(todo[0], Res('found', dict(CREDIT), b'raw'))]
        calls = []
        def vet(e): calls.append(1); return (None, 'CC BY / BY-SA with no author') if len(calls) == 1 else (e, '')
        s = self.make([('wikipedia', found, lambda w, u: True, None), ('commons', found, lambda w, u: True, None)], vet)
        got, trail = s.picture(unit, 'taxon'); self.assertEqual((got['source'], trail[0]), ('commons', 'wikipedia: refused (CC BY / BY-SA with no author)'))

    def test_nothing_found_returns_none_with_every_source_in_the_trail(self):
        miss = lambda todo: [(todo[0], Res('retry', why='the batch request failed'))]
        got, trail = self.make([('wikipedia', miss, lambda w, u: True, None), ('openverse', miss, lambda w, u: False, None)]).picture({'sid': 'a', 'title': 'A'}, 'taxon')
        self.assertEqual((got, trail), (None, ['wikipedia: the batch request failed', 'openverse: not for this kind']))

    def test_a_source_that_stops_raises_stopped(self):
        def boom(todo): raise RuntimeError('too many throttles')
        with self.assertRaises(A.Stopped): self.make([('wikipedia', boom, lambda w, u: True, None)]).picture({'sid': 'a', 'title': 'A'}, 'taxon')

if __name__ == '__main__': unittest.main()
