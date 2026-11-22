"""docs/ADD-SPECIES.md: identity before writing, whole-or-nothing add, and the refusal ledger. Nothing calls lib/species_rows.py yet; these tests are what keeps its rules from drifting."""
import datetime, json, os, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import species_rows as sr, creation_ledger as cl, contracts

DAY = datetime.date(2026, 11, 22)

def row(latin, name, wiki, sk='taxon', **kw):
    r = {'latin': latin, 'name': name, 'tl': 2, 'wiki': wiki, 'desc': 'd', 'ic': 'x', 'sid': kw.pop('sid', None) or sr.species.slug(latin or name), 'sk': sk, 'about': 'About.'}
    r.update(kw); return r

def good(cand, sid):
    """a gather that finds everything and writes nothing until commit() is called"""
    wrote = []
    steps = {s: {'result': 'found', 'detail': 'fake'} for s in ('picture', 'taxonomy', 'summary', 'conservation')}
    return steps, row(cand['latin'], cand['name'], cand['wiki'], sk=cand['kind']), lambda: wrote.append(sid)

class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); os.makedirs(os.path.join(self.d, 'data', 'species', 'rows'))
        self.rows = sr.SpeciesRows(self.d); self.ledger = cl.Ledger('species', self.d)
        self.rows.create(row('canis latrans', 'Coyote', 'Coyote'))
        self.rows.create(row('', 'Sunlight', 'Sunlight', sk='resource', cat='abiotic', tl=0, sid='sunlight'))

class Identify(Base):
    def test_same_page_is_the_same_row_even_with_other_capitals_or_underscores(self):
        self.assertEqual(self.rows.identify('coyote', 'taxon', 'canis latrans')['sid'], 'canis-latrans')
        self.assertEqual(self.rows.identify('Sun_light', 'resource', '', 'Sun light')['status'], 'new')
        self.assertEqual(self.rows.identify('Sunlight', 'resource', '', 'Sunlight')['by'], 'wiki')

    def test_a_page_is_unique_per_kind_not_across_kinds(self):
        self.assertEqual(self.rows.identify('Sunlight', 'taxon', 'sunlightus')['status'], 'new')

    def test_same_gbif_key_is_the_same_row(self):
        self.rows.taxonomy['canis-latrans'] = {'key': 5219243}; self.rows._index()
        i = self.rows.identify('Prairie wolf', 'taxon', 'canis lupus latrans', gbif=5219243)
        self.assertEqual((i['status'], i['sid'], i['by']), ('exists', 'canis-latrans', 'gbif'))

    def test_same_id_is_never_a_second_row(self):
        i = self.rows.identify('Some other page', 'taxon', 'Canis latrans')
        self.assertEqual((i['status'], i['sid'], i['by']), ('exists', 'canis-latrans', 'id'))

    def test_two_tests_naming_different_rows_is_a_conflict_naming_both(self):
        self.rows.create(row('canis lupus', 'Wolf', 'Wolf')); self.rows.taxonomy['canis-lupus'] = {'key': 1}; self.rows._index()
        i = self.rows.identify('Coyote', 'taxon', 'canis lupus', gbif=1)
        self.assertEqual((i['status'], i['sids']), ('conflict', ['canis-latrans', 'canis-lupus']))

class Create(Base):
    def test_refuses_a_row_that_breaks_the_model_and_writes_nothing(self):
        before = species_files(self.d)
        for bad in (row('canis latrans', 'Dup', 'Dup2'),                                  # sid already a row
                    row('x y', 'X', 'X', about=''),                                      # no summary
                    row('a b', 'A', 'Coyote'),                                           # page of another row of this kind
                    row('', 'Rain', 'Rain', sk='resource', tl=0, sid='rain'),            # resource without cat
                    row('c d', 'C', 'C', sid='wrong-id'),                                # sid is not the slug of the Latin name
                    row('e f', 'E', 'E', extra=1)):                                      # field the schema refuses
            with self.assertRaises(ValueError): self.rows.create(bad)
        self.assertEqual(species_files(self.d), before)

    def test_a_resource_row_goes_to_the_nodes_folder(self):
        self.assertTrue(os.path.exists(os.path.join(self.d, 'data', 'nodes', 'rows', 'su', 'sunlight.json')))

    def test_a_written_row_passes_the_row_schema(self):
        try: import jsonschema
        except ImportError: self.skipTest('jsonschema not installed')
        schema = json.load(open(os.path.join(ROOT, 'build', 'schemas', 'species-row.schema.json')))
        jsonschema.validate(json.load(open(os.path.join(self.d, 'data', 'species', 'rows', 'ca', 'canis-latrans.json'))), schema)

def species_files(d):
    return sorted(os.path.join(b, f) for b, _, fs in os.walk(d) for f in fs)

class Ensure(Base):
    cand = {'wiki': 'Eastern coyote', 'kind': 'taxon', 'latin': 'canis latrans var', 'name': 'Eastern coyote'}

    def test_adds_when_every_required_step_is_found_and_writes_the_files_before_the_row(self):
        order = []
        def gather(c, sid):
            s, r, _ = good(c, sid); return s, r, lambda: order.append(('files', os.path.exists(os.path.join(self.d, 'data', 'species', 'rows', sid[:2], sid + '.json'))))
        res = self.rows.ensure(self.cand, gather, self.ledger, DAY)
        self.assertEqual((res['status'], res['id'], res['reason'], res['dry']), ('added', 'canis-latrans-var', None, False))
        self.assertEqual(order, [('files', False)])   # the files were written while the row did not yet exist
        self.assertIn('canis-latrans-var', self.rows.tab)

    def test_idempotent_second_call_returns_exists_and_never_calls_gather(self):
        self.rows.ensure(self.cand, good, self.ledger, DAY)
        def boom(*a): raise AssertionError('gather must not run for a known species')
        res = self.rows.ensure(self.cand, boom, self.ledger, DAY)
        self.assertEqual((res['status'], res['id']), ('exists', 'canis-latrans-var'))

    def test_a_missing_picture_refuses_records_every_step_and_adds_no_row(self):
        def gather(c, sid):
            s, r, f = good(c, sid); s['picture'] = {'result': 'missing', 'detail': 'no licensed picture'}; s['taxonomy'] = {'result': 'missing', 'detail': 'no match'}; return s, r, f
        n = len(self.rows.tab); res = self.rows.ensure(self.cand, gather, self.ledger, DAY)
        self.assertEqual((res['status'], res['reason'], res['id']), ('refused', 'picture', None))
        self.assertEqual(len(self.rows.tab), n)
        rec = self.ledger.get('Eastern coyote')
        self.assertEqual((rec['reason'], rec['steps']['taxonomy']['result'], rec['attempts'], rec['hold_until']), ('picture', 'missing', 1, '2027-02-20'))   # every step is recorded, not only the first failure

    def test_conservation_is_optional(self):
        def gather(c, sid):
            s, r, f = good(c, sid); s['conservation'] = {'result': 'missing', 'detail': 'none on Wikidata'}; return s, r, f
        self.assertEqual(self.rows.ensure(self.cand, gather, self.ledger, DAY)['status'], 'added')

    def test_a_resource_needs_no_taxonomy(self):
        c = {'wiki': 'Rain', 'kind': 'resource', 'name': 'Rain'}
        def gather(c, sid):
            return {'picture': {'result': 'found'}, 'summary': {'result': 'found'}, 'taxonomy': {'result': 'skipped'}}, row('', 'Rain', 'Rain', sk='resource', cat='abiotic', tl=0, sid=sid), lambda: None
        self.assertEqual(self.rows.ensure(c, gather, self.ledger, DAY)['id'], 'rain')

    def test_a_conflict_is_refused_with_both_rows_named(self):
        self.rows.create(row('canis lupus', 'Wolf', 'Wolf')); self.rows.taxonomy['canis-lupus'] = {'key': 1}; self.rows._index()
        res = self.rows.ensure({'wiki': 'Coyote', 'kind': 'taxon', 'latin': 'canis lupus', 'gbif': 1}, good, self.ledger, DAY)
        self.assertEqual((res['status'], res['reason']), ('refused', 'conflict'))
        self.assertIn('canis-latrans, canis-lupus', self.ledger.get('Coyote')['steps']['identity']['detail'])

    def test_a_dry_call_writes_nothing_and_says_what_would_happen(self):
        before = species_files(self.d); res = self.rows.ensure(self.cand, good, self.ledger, DAY, dry=True)
        self.assertEqual((res['status'], res['dry']), ('added', True)); self.assertEqual(species_files(self.d), before)
        def nopic(c, sid):
            s, r, f = good(c, sid); s['picture'] = {'result': 'missing'}; return s, r, f
        self.assertEqual(self.rows.ensure({**self.cand, 'wiki': 'Other', 'latin': 'a b'}, nopic, self.ledger, DAY, dry=True)['status'], 'refused')
        self.assertEqual(species_files(self.d), before)   # a dry refusal is not recorded either

    def test_adding_a_refused_species_later_clears_its_ledger_entry(self):
        def nopic(c, sid):
            s, r, f = good(c, sid); s['picture'] = {'result': 'missing'}; return s, r, f
        self.rows.ensure(self.cand, nopic, self.ledger, DAY); self.assertIsNotNone(self.ledger.get('Eastern coyote'))
        self.rows.ensure(self.cand, good, self.ledger, DAY)
        self.assertIsNone(cl.Ledger('species', self.d).get('Eastern coyote'))

class LedgerTests(unittest.TestCase):
    def test_hold_due_and_attempts(self):
        d = tempfile.mkdtemp(); L = cl.Ledger('species', d); st = {'picture': {'result': 'missing', 'detail': 'x'}}
        L.record('A', st, 'picture', DAY); L.record('A', st, 'picture', DAY + datetime.timedelta(days=100)); L.record('B', st, 'summary', DAY); L.commit()
        L = cl.Ledger('species', d)
        self.assertEqual(L.get('A')['attempts'], 2)
        self.assertEqual(L.due(DAY + datetime.timedelta(days=95)), ['B'])
        self.assertEqual(L.by_reason(), {'picture': 1, 'summary': 1})
        with self.assertRaises(ValueError): L.record('C', {'picture': {'result': 'maybe'}}, 'picture', DAY)
        with self.assertRaises(ValueError): L.record('C', st, '', DAY)

    def test_contracts_name_the_steps_each_kind_needs(self):
        self.assertIn('picture', contracts.SPECIES_REQUIRED['taxon']); self.assertNotIn('conservation', sum(contracts.SPECIES_REQUIRED.values(), ()))
        self.assertEqual(contracts.SPECIES_OPTIONAL, ('conservation',))

if __name__ == '__main__': unittest.main()
