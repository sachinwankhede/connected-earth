#!/usr/bin/env python3
"""Rules of lib/species_sources.py (the species picture sources): GBIF, Openverse and the Commons file paths and download.
What they assert is unchanged from the tests of the old jobs/gbifphotos.py, openversephotos.py and hostphotos.py."""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lib"))
import species_sources as ss

CC_BY = 'http://creativecommons.org/licenses/by/4.0/'
CC0 = 'http://creativecommons.org/publicdomain/zero/1.0/'


def rec(key=1, basis='HUMAN_OBSERVATION', url='https://img.example.org/a.jpg', lic=CC_BY, creator='Ann Lee', **more):
    return {'key': key, 'basisOfRecord': basis, 'media': [{'type': 'StillImage', 'identifier': url, 'license': lic, 'creator': creator}], **more}


class GbifRuleTests(unittest.TestCase):
    def test_only_cc0_and_cc_by_are_kept(self):
        self.assertEqual(ss.gbif_licence_of({'license': CC_BY}), ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'))
        self.assertEqual(ss.gbif_licence_of({'license': CC0})[0], 'CC0 1.0')
        self.assertEqual(ss.gbif_licence_of({'license': 'CC_BY_4_0'})[0], 'CC BY 4.0')
        self.assertEqual(ss.gbif_licence_of({'license': 'https://creativecommons.org/licenses/by/3.0'})[0], 'CC BY 3.0')
        for lic in ('', None, 'http://creativecommons.org/licenses/by-nc/4.0/', 'CC_BY_NC_4_0', 'http://creativecommons.org/licenses/by-sa/4.0/',
                    'http://creativecommons.org/licenses/by-nd/4.0/', 'All rights reserved'):
            self.assertIsNone(ss.gbif_licence_of({'license': lic}), lic)

    def test_usable_observation_is_kept_with_its_credit(self):
        self.assertEqual(ss.gbif_candidates([rec(7)]), [(7, 'https://img.example.org/a.jpg', 'Ann Lee', 'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0')])

    def test_inaturalist_is_dropped_in_every_form(self):
        for r in (rec(datasetKey=ss.INAT_DATASET), rec(institutionCode='iNaturalist'), rec(references='https://www.inaturalist.org/observations/1'),
                  rec(url='https://inaturalist-open-data.s3.amazonaws.com/photos/1/large.jpg')):
            self.assertEqual(ss.gbif_candidates([r]), [])

    def test_specimen_sheets_are_dropped(self):
        for b in ('PRESERVED_SPECIMEN', 'FOSSIL_SPECIMEN', 'MATERIAL_SAMPLE', 'UNKNOWN', None):
            self.assertEqual(ss.gbif_candidates([rec(basis=b)]), [], b)
        for b in ('MACHINE_OBSERVATION', 'LIVING_SPECIMEN', 'OBSERVATION'):
            self.assertEqual(len(ss.gbif_candidates([rec(basis=b)])), 1, b)

    def test_herbarium_and_museum_records_labelled_as_observations_are_dropped(self):
        for r in (rec(basis='MACHINE_OBSERVATION', url='https://collections.nmnh.si.edu/media/?i=1', datasetName='NMNH Extant Biology'),
                  rec(url='https://iiif-manifest.oxalis.br.fgov.be/specimen/BR1/manifest', datasetName='Meise Botanic Garden Herbarium (BR)'),
                  rec(datasetName='Some Museum collection')):
            self.assertEqual(ss.gbif_candidates([r]), [])
        self.assertEqual(len(ss.gbif_candidates([rec(url='https://www.artsobservasjoner.no/MediaLibrary/a.jpg', datasetName='Artsobservasjoner')])), 1)

    def test_a_photo_without_a_named_author_is_dropped(self):
        for c in ('', None, 'Unknown', 'anonymous', '   '):
            self.assertEqual(ss.gbif_candidates([rec(creator=c)]), [], c)
        r = rec(creator=None); r['media'][0]['rightsHolder'] = 'Museum X'
        self.assertEqual(ss.gbif_candidates([r])[0][2], 'Museum X')

    def test_only_safe_https_links_are_fetched(self):
        for u in ('http://img.example.org/a.jpg', 'ftp://x.org/a.jpg', 'https://127.0.0.1/a.jpg', 'https://[::1]/a.jpg', 'https://localhost/a.jpg',
                  'https://user:pw@img.example.org/a.jpg', 'https://intranet/a.jpg', '', None, 'file:///etc/passwd'):
            self.assertFalse(ss.safe_url(u), u)
        self.assertTrue(ss.safe_url('https://img.example.org/a.jpg?x=1'))

    def test_not_a_still_image_is_dropped_and_one_picture_per_occurrence(self):
        r = rec(); r['media'].insert(0, {'type': 'MovingImage', 'identifier': 'https://img.example.org/v.mp4', 'license': CC_BY, 'creator': 'A'})
        r['media'].append({'type': 'StillImage', 'identifier': 'https://img.example.org/b.jpg', 'license': CC_BY, 'creator': 'A'})
        self.assertEqual([c[1] for c in ss.gbif_candidates([r])], ['https://img.example.org/a.jpg'])


ID = '0a1b2c3d-0000-4000-8000-000000000001'


def res(title='Panthera onca in the wild', lic='by', ver='4.0', creator='Ann Lee', rid=ID, **more):
    return {'id': rid, 'title': title, 'license': lic, 'license_version': ver, 'creator': creator, 'provider': 'flickr', 'source': 'flickr',
            'foreign_landing_url': 'https://www.flickr.com/photos/1/2', 'url': 'https://live.staticflickr.com/a.jpg', 'tags': [], **more}


class OpenverseRuleTests(unittest.TestCase):
    def test_only_four_licences_are_kept(self):
        self.assertEqual(ss.ov_licence_of(res(lic='by', ver='4.0')), ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'))
        self.assertEqual(ss.ov_licence_of(res(lic='by-sa', ver='2.0'))[0], 'CC BY-SA 2.0')
        self.assertEqual(ss.ov_licence_of(res(lic='cc0', ver='1.0'))[0], 'CC0 1.0')
        self.assertEqual(ss.ov_licence_of(res(lic='pdm', ver='1.0'))[0], 'Public domain')
        for lic in ('by-nc', 'by-nd', 'by-nc-sa', 'by-nc-nd', '', None, 'sampling+'):
            self.assertIsNone(ss.ov_licence_of(res(lic=lic)), lic)
        self.assertIsNone(ss.ov_licence_of(res(lic='by', ver='')))

    def test_usable_result_is_kept_with_creator_and_own_thumbnail(self):
        self.assertEqual(ss.openverse_candidates([res()], 'Panthera onca'),
                         [(ID, 'https://api.openverse.org/v1/images/%s/thumb/' % ID, 'Ann Lee', 'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0')])

    def test_the_latin_name_must_be_in_title_or_tags(self):
        self.assertEqual(ss.openverse_candidates([res(title='A cat')], 'Panthera onca'), [])
        self.assertEqual(len(ss.openverse_candidates([res(title='A cat', tags=[{'name': 'panthera onca'}])], 'Panthera onca')), 1)

    def test_inaturalist_and_collections_are_dropped(self):
        for r in (res(provider='inaturalist'), res(source='inaturalist'), res(url='https://inaturalist-open-data.s3.amazonaws.com/photos/1/large.jpg'),
                  res(title='Panthera onca herbarium sheet'), res(foreign_landing_url='https://collections.example.org/1'), res(title='Panthera onca museum skull')):
            self.assertEqual(ss.openverse_candidates([r], 'Panthera onca'), [], r)

    def test_a_named_creator_is_required(self):
        for c in ('', None, 'Unknown', 'anonymous'):
            self.assertEqual(ss.openverse_candidates([res(creator=c)], 'Panthera onca'), [], c)

    def test_bad_ids_are_dropped(self):
        self.assertEqual(ss.openverse_candidates([res(rid='../x')], 'Panthera onca'), [])


class CommonsPathTests(unittest.TestCase):
    def test_commons_file_from_each_path_shape(self):
        self.assertEqual(ss.commons_file("4/42/Opuntia%2C_b.jpg/330px-Opuntia%2C_b.jpg"), "Opuntia,_b.jpg")
        self.assertEqual(ss.commons_file("https://upload.wikimedia.org/wikipedia/commons/5/5c/Achnatherum_hymenoides_-_Ricegrass.jpg"), "Achnatherum_hymenoides_-_Ricegrass.jpg")
        self.assertEqual(ss.commons_file("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/A.jpg/330px-A.jpg"), "A.jpg")
        self.assertIsNone(ss.commons_file("https://thumb.wikimedia.org/wikipedia/en/thumb/0/07/Pallid_Bat.jpg/330px-Pallid_Bat.jpg"))

    def test_thumb_path(self):
        self.assertEqual(ss.thumb_path("4/42/A.jpg/330px-A.jpg"), "4/42/A.jpg/330px-A.jpg")
        self.assertEqual(ss.thumb_path("https://upload.wikimedia.org/wikipedia/commons/5/5c/A.jpg"), "5/5c/A.jpg/330px-A.jpg")
        self.assertEqual(ss.thumb_path("https://upload.wikimedia.org/wikipedia/commons/thumb/5/5c/A.jpg/330px-A.jpg"), "5/5c/A.jpg/330px-A.jpg")


class DownloadTests(unittest.TestCase):
    def run_download(self, u, answers):
        seen = []
        def fake(url, raw=False, tries=6):
            seen.append(url); a = answers.pop(0)
            if isinstance(a, Exception): raise a
            return a
        old = ss.wm.get; ss.wm.get = fake
        try: return ss.download(u), seen
        finally: ss.wm.get = old

    def test_a_thumbnail_path_downloads_the_thumbnail_only(self):
        raw, seen = self.run_download("4/42/A.jpg/330px-A.jpg", [b"x"])
        self.assertEqual((raw, seen), (b"x", [ss.BASE + "4/42/A.jpg/330px-A.jpg"]))

    def test_a_small_original_falls_back_to_the_original(self):
        u = "https://upload.wikimedia.org/wikipedia/commons/5/5c/A.jpg"
        raw, seen = self.run_download(u, [RuntimeError("400"), b"orig"])
        self.assertEqual((raw, seen), (b"orig", [ss.BASE + "5/5c/A.jpg/330px-A.jpg", u]))

    def test_a_large_original_still_uses_its_thumbnail(self):
        raw, seen = self.run_download("https://upload.wikimedia.org/wikipedia/commons/5/5c/A.jpg", [b"thumb"])
        self.assertEqual((raw, seen), (b"thumb", [ss.BASE + "5/5c/A.jpg/330px-A.jpg"]))


if __name__ == "__main__":
    unittest.main()
