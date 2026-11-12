#!/usr/bin/env python3
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs")); sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
import inaturalistphotos as n, licences, fetch

B = 'https://inaturalist-open-data.s3.amazonaws.com/photos/'
def tp(pid=1, lic='cc-by', au='Ann Lee', url=None, **more):
    return {'photo': {'id': pid, 'license_code': lic, 'attribution_name': au, 'medium_url': url if url is not None else '%s%d/medium.jpg' % (B, pid), 'flags': [], **more}}

class INatTests(unittest.TestCase):
    def test_only_three_licences_are_kept(self):
        self.assertEqual(n.candidates({'taxon_photos': [tp(1, 'cc-by')]}), [(1, B + '1/medium.jpg', 'Ann Lee', 'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0')])
        self.assertEqual(n.candidates({'taxon_photos': [tp(2, 'cc-by-sa')]})[0][3], 'CC BY-SA 4.0')
        self.assertEqual(n.candidates({'taxon_photos': [tp(3, 'cc0')]})[0][3], 'CC0 1.0')
        for lic in ('cc-by-nc', 'cc-by-nd', 'cc-by-nc-sa', 'cc-by-nc-nd', None, '', 'pd'):
            self.assertEqual(n.candidates({'taxon_photos': [tp(4, lic)]}), [], lic)
    def test_first_usable_photos_in_order(self):
        t = {'taxon_photos': [tp(1, 'cc-by-nc'), tp(2, None), tp(3, 'cc-by'), tp(4, 'cc0')]}
        self.assertEqual([c[0] for c in n.candidates(t)], [3, 4])
    def test_a_named_photographer_is_required(self):
        for a in ('', None, 'Unknown', 'anonymous'): self.assertEqual(n.candidates({'taxon_photos': [tp(1, au=a)]}), [], a)
    def test_only_the_open_bucket_is_used(self):
        for u in ('https://static.inaturalist.org/photos/1/medium.jpg', B + '9/medium.jpg', 'http://inaturalist-open-data.s3.amazonaws.com/photos/1/medium.jpg', ''):
            self.assertEqual(n.candidates({'taxon_photos': [tp(1, url=u)]}), [], u)
    def test_flagged_photos_are_dropped(self):
        self.assertEqual(n.candidates({'taxon_photos': [tp(1, flags=[{'flag': 'copyright infringement'}])]}), [])
    def test_credit_names_its_source_itself(self):
        self.assertEqual(n.credit(7, 'Ann Lee', 'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'), {'a': 'Ann Lee', 'l': 'CC BY 4.0', 'lu': 'https://creativecommons.org/licenses/by/4.0', 'p': 'https://www.inaturalist.org/photos/7', 's': 'iNaturalist'})
    def test_nothing(self):
        self.assertEqual(n.candidates(None), []); self.assertEqual(n.candidates({}), [])
    def test_taxon_name_must_match_exactly(self):
        rs = [{'id': 5, 'name': 'Acer barbatum var. x', 'rank': 'variety'}, {'id': 6, 'name': 'Acer barbatus', 'rank': 'species'}, {'id': 7, 'name': 'acer barbatum', 'rank': 'species', 'is_active': True}]
        self.assertEqual(n.match_taxon(rs, 'Acer barbatum'), 7)
        self.assertIsNone(n.match_taxon(rs[:2], 'Acer barbatum')); self.assertIsNone(n.match_taxon(None, 'x'))
        self.assertEqual(n.match_taxon([{'id': 8, 'name': 'Acanthogammarus', 'rank': 'genus'}], 'Acanthogammarus'), 8)
        self.assertIsNone(n.match_taxon([{'id': 9, 'name': 'Rosa', 'rank': 'species', 'is_active': False}], 'Rosa'))
        self.assertIsNone(n.match_taxon([{'id': 10, 'name': 'Soil', 'rank': 'kingdom'}], 'Soil'))
    def test_hosts_are_on_the_allowed_list_and_licences_pass_the_rule(self):
        for h in ('api.inaturalist.org', 'inaturalist-open-data.s3.amazonaws.com', 'www.inaturalist.org'): fetch.check_url('https://%s/x' % h)
        with self.assertRaises(PermissionError): fetch.check_url('https://static.inaturalist.org/photos/1/medium.jpg')
        for l in ('CC0 1.0', 'CC BY 4.0', 'CC BY-SA 4.0'): self.assertTrue(licences.ok('iNaturalist', l), l)
        self.assertFalse(licences.ok('iNaturalist', 'CC BY-NC 4.0'))
if __name__ == '__main__': unittest.main()
