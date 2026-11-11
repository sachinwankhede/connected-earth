#!/usr/bin/env python3
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import openversephotos as o

ID = '0a1b2c3d-0000-4000-8000-000000000001'


def res(title='Panthera onca in the wild', lic='by', ver='4.0', creator='Ann Lee', rid=ID, **more):
    return {'id': rid, 'title': title, 'license': lic, 'license_version': ver, 'creator': creator, 'provider': 'flickr', 'source': 'flickr',
            'foreign_landing_url': 'https://www.flickr.com/photos/1/2', 'url': 'https://live.staticflickr.com/a.jpg', 'tags': [], **more}


class OpenversePhotosTests(unittest.TestCase):
    def test_only_four_licences_are_kept(self):
        self.assertEqual(o.licence_of(res(lic='by', ver='4.0')), ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0'))
        self.assertEqual(o.licence_of(res(lic='by-sa', ver='2.0'))[0], 'CC BY-SA 2.0')
        self.assertEqual(o.licence_of(res(lic='cc0', ver='1.0'))[0], 'CC0 1.0')
        self.assertEqual(o.licence_of(res(lic='pdm', ver='1.0'))[0], 'Public domain')
        for lic in ('by-nc', 'by-nd', 'by-nc-sa', 'by-nc-nd', '', None, 'sampling+'):
            self.assertIsNone(o.licence_of(res(lic=lic)), lic)
        self.assertIsNone(o.licence_of(res(lic='by', ver='')))

    def test_usable_result_is_kept_with_creator_and_own_thumbnail(self):
        self.assertEqual(o.candidates([res()], 'Panthera onca'),
                         [(ID, 'https://api.openverse.org/v1/images/%s/thumb/' % ID, 'Ann Lee', 'CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0')])

    def test_the_latin_name_must_be_in_title_or_tags(self):
        self.assertEqual(o.candidates([res(title='A cat')], 'Panthera onca'), [])
        self.assertEqual(len(o.candidates([res(title='A cat', tags=[{'name': 'panthera onca'}])], 'Panthera onca')), 1)

    def test_inaturalist_and_collections_are_dropped(self):
        for r in (res(provider='inaturalist'), res(source='inaturalist'), res(url='https://inaturalist-open-data.s3.amazonaws.com/photos/1/large.jpg'),
                  res(title='Panthera onca herbarium sheet'), res(foreign_landing_url='https://collections.example.org/1'), res(title='Panthera onca museum skull')):
            self.assertEqual(o.candidates([r], 'Panthera onca'), [], r)

    def test_a_named_creator_is_required(self):
        for c in ('', None, 'Unknown', 'anonymous'):
            self.assertEqual(o.candidates([res(creator=c)], 'Panthera onca'), [], c)

    def test_bad_ids_are_dropped(self):
        self.assertEqual(o.candidates([res(rid='../x')], 'Panthera onca'), [])


if __name__ == '__main__':
    unittest.main()
