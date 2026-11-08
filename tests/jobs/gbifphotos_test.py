#!/usr/bin/env python3
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import gbifphotos as g

CC_BY = 'http://creativecommons.org/licenses/by/4.0/'
CC0 = 'http://creativecommons.org/publicdomain/zero/1.0/'


def rec(key=1, basis='HUMAN_OBSERVATION', url='https://img.example.org/a.jpg', lic=CC_BY, creator='Ann Lee', **more):
    return {'key': key, 'basisOfRecord': basis, 'media': [{'type': 'StillImage', 'identifier': url, 'license': lic, 'creator': creator}], **more}


class GbifPhotosTests(unittest.TestCase):
    def test_only_cc0_and_cc_by_are_kept(self):
        self.assertEqual(g.licence_of({'license': CC_BY}), ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'))
        self.assertEqual(g.licence_of({'license': CC0})[0], 'CC0 1.0')
        self.assertEqual(g.licence_of({'license': 'CC_BY_4_0'})[0], 'CC BY 4.0')
        self.assertEqual(g.licence_of({'license': 'https://creativecommons.org/licenses/by/3.0'})[0], 'CC BY 3.0')
        for lic in ('', None, 'http://creativecommons.org/licenses/by-nc/4.0/', 'CC_BY_NC_4_0', 'http://creativecommons.org/licenses/by-sa/4.0/',
                    'http://creativecommons.org/licenses/by-nd/4.0/', 'All rights reserved'):
            self.assertIsNone(g.licence_of({'license': lic}), lic)

    def test_usable_observation_is_kept_with_its_credit(self):
        self.assertEqual(g.candidates([rec(7)]), [(7, 'https://img.example.org/a.jpg', 'Ann Lee', 'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0')])

    def test_inaturalist_is_dropped_in_every_form(self):
        for r in (rec(datasetKey=g.INAT_DATASET), rec(institutionCode='iNaturalist'), rec(references='https://www.inaturalist.org/observations/1'),
                  rec(url='https://inaturalist-open-data.s3.amazonaws.com/photos/1/large.jpg')):
            self.assertEqual(g.candidates([r]), [])

    def test_specimen_sheets_are_dropped(self):
        for b in ('PRESERVED_SPECIMEN', 'FOSSIL_SPECIMEN', 'MATERIAL_SAMPLE', 'UNKNOWN', None):
            self.assertEqual(g.candidates([rec(basis=b)]), [], b)
        for b in ('MACHINE_OBSERVATION', 'LIVING_SPECIMEN', 'OBSERVATION'):
            self.assertEqual(len(g.candidates([rec(basis=b)])), 1, b)

    def test_a_photo_without_a_named_author_is_dropped(self):
        for c in ('', None, 'Unknown', 'anonymous', '   '):
            self.assertEqual(g.candidates([rec(creator=c)]), [], c)
        r = rec(creator=None); r['media'][0]['rightsHolder'] = 'Museum X'
        self.assertEqual(g.candidates([r])[0][2], 'Museum X')

    def test_only_safe_https_links_are_fetched(self):
        for u in ('http://img.example.org/a.jpg', 'ftp://x.org/a.jpg', 'https://127.0.0.1/a.jpg', 'https://[::1]/a.jpg', 'https://localhost/a.jpg',
                  'https://user:pw@img.example.org/a.jpg', 'https://intranet/a.jpg', '', None, 'file:///etc/passwd'):
            self.assertFalse(g.safe_url(u), u)
        self.assertTrue(g.safe_url('https://img.example.org/a.jpg?x=1'))

    def test_not_a_still_image_is_dropped_and_one_picture_per_occurrence(self):
        r = rec(); r['media'].insert(0, {'type': 'MovingImage', 'identifier': 'https://img.example.org/v.mp4', 'license': CC_BY, 'creator': 'A'})
        r['media'].append({'type': 'StillImage', 'identifier': 'https://img.example.org/b.jpg', 'license': CC_BY, 'creator': 'A'})
        self.assertEqual([c[1] for c in g.candidates([r])], ['https://img.example.org/a.jpg'])


if __name__ == '__main__':
    unittest.main()
