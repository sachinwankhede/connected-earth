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

    def test_abiotic_rows_are_not_looked_up(self):   # "Aquifer", "Nutrient", "Lake Titicaca" got photographs of the thing, not of a species
        import tempfile, json, os
        r = tempfile.mkdtemp(); d = os.path.join(r, 'data', 'species', 'rows', 'aq'); os.makedirs(d)
        json.dump({'latin': '', 'name': 'Aquifer water', 'cat': 'abiotic', 'wiki': 'Aquifer'}, open(os.path.join(d, 'aquifer-water.json'), 'w'))
        json.dump({'latin': 'Aquila chrysaetos', 'name': 'Golden eagle', 'wiki': 'Golden eagle'}, open(os.path.join(d, 'aquila-chrysaetos.json'), 'w'))
        json.dump({'latin': '', 'name': 'Lake', 'cat': 'abiotic', 'wiki': 'Lake_Edward'}, open(os.path.join(d, 'lake-edward.json'), 'w'))
        self.assertEqual(o.non_organisms(r), {'Aquifer', 'Lake Edward'})


if __name__ == '__main__':
    unittest.main()
