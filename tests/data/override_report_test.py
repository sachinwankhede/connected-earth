import os, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import override_report as o

TAB = {'coy': {'sid': 'coy', 'sk': 'taxon', 'name': 'Coyote', 'wiki': 'Canis latrans', 'tl': 4, 'ic': 'coyote'},
       'wolf': {'sid': 'wolf', 'sk': 'taxon', 'name': 'Gray wolf', 'wiki': 'Wolf', 'tl': 4, 'ic': 'wolf'},
       'sun': {'sid': 'sun', 'sk': 'resource', 'name': 'Sunlight', 'wiki': 'Sunbeam', 'cat': 'abiotic', 'tl': 0, 'ic': 'sun'},
       'rainy': {'sid': 'rainy', 'sk': 'resource', 'name': 'Wet season', 'wiki': 'Wet season', 'cat': 'abiotic', 'tl': 0, 'ic': 'rain'}}
P, N = o.indexes(TAB)
def c(node, sid='coy'): return o.classify(node, TAB[sid], sid, P, N)

class Classify(unittest.TestCase):
    def test_a_page_a_row_has_is_a_repoint_to_that_row(self):
        self.assertEqual(c({'wiki': 'wolf'}), ('repoint', 'wolf', 'wolf'))   # capitals ignored
    def test_a_page_no_row_has_is_a_new_row_candidate(self):
        self.assertEqual(c({'wiki': 'Eastern coyote', 'name': 'Eastern coyote'}), ('new-row', None, 'Eastern coyote'))
    def test_a_name_only_override_with_no_row_of_that_name_goes_to_the_nearest_row(self):
        self.assertEqual(c({'name': 'Prairie wolf'}), ('nearest', None, None))
    def test_a_name_only_override_matching_another_row_is_a_repoint(self):
        self.assertEqual(c({'name': 'gray wolf'}), ('repoint', 'wolf', 'gray wolf'))
    def test_the_rows_own_page_or_name_is_not_an_override_to_fix(self):
        self.assertIsNone(c({'wiki': 'Canis_latrans'})); self.assertIsNone(c({'name': 'coyote'})); self.assertIsNone(c({'id': 'x'}))
    def test_kinds_never_match_each_other(self):
        self.assertEqual(c({'wiki': 'Sunbeam'})[0], 'new-row')   # a taxon node naming a resource page: no taxon row has it
    def test_a_resource_candidate_carries_its_category_and_no_latin(self):
        rows = [('p', 'n', 'sun', 'resource', False, True, 'new-row', None, 'Zodiacal light'), ('q', 'n', 'sun', 'resource', False, True, 'new-row', None, 'zodiacal light')]
        self.assertEqual(o.candidates(rows, TAB), [{'wiki': 'Zodiacal light', 'kind': 'resource', 'name': 'Zodiacal light', 'tl': 0, 'ic': 'sun', 'cat': 'abiotic'}])
    def test_a_taxon_candidate_asks_for_its_latin_name(self):
        rows = [('p', 'n', 'coy', 'taxon', True, True, 'new-row', None, 'Eastern coyote')]
        self.assertEqual(o.candidates(rows, TAB), [{'wiki': 'Eastern coyote', 'kind': 'taxon', 'name': 'Eastern coyote', 'tl': 4, 'ic': 'coyote', 'latin': ''}])
    def test_a_page_several_rows_share_is_ambiguous_not_new(self):
        tab = dict(TAB, dup={'sid': 'dup', 'sk': 'taxon', 'name': 'Other', 'wiki': 'Wolf'}); P2, N2 = o.indexes(tab)
        self.assertEqual(o.classify({'wiki': 'Wolf'}, tab['coy'], 'coy', P2, N2), ('ambiguous', None, 'Wolf'))
        self.assertEqual(o.classify({'wiki': 'Wolf'}, tab['wolf'], 'wolf', P2, N2), None)   # the node's own row has it, and so does one other: its own page, nothing to fix
    def test_a_node_whose_own_row_shares_the_page_with_another_is_a_repoint_to_that_one_only_when_the_other_is_alone(self):
        tab = dict(TAB, dup={'sid': 'dup', 'sk': 'taxon', 'name': 'Other', 'wiki': 'Wolf'}); P2, N2 = o.indexes(tab)
        self.assertEqual(o.classify({'wiki': 'Wolf'}, tab['wolf'], 'wolf', P2, N2), None)

class NameClasses(unittest.TestCase):
    """#1038 (#1047): the first report, kept as `--classes` (#1077 had replaced it)."""
    def test_classes(self):
        self.assertEqual(o.name_class('Cattails', 'Cattail'), 'spelling'); self.assertEqual(o.name_class('Beavertail cactus', 'Beaver-tail cactus'), 'spelling')
        self.assertEqual(o.name_class('Leopard', 'Javan leopard'), 'form'); self.assertEqual(o.name_class('Brittlebush', 'White brittlebush'), 'form')
        self.assertEqual(o.name_class('Fungi and bacteria', 'Fungi and soil microbes'), 'group'); self.assertEqual(o.name_class('Peat', 'Peat & bog'), 'group')
        self.assertEqual(o.name_class('Argali', 'Marco Polo sheep'), 'other'); self.assertEqual(o.name_class('Cardinal catchfly', 'Indian-pink'), 'other')

if __name__ == '__main__': unittest.main()
