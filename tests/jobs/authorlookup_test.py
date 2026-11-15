#!/usr/bin/env python3
import os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import authorlookup as a

P = 'https://commons.wikimedia.org/wiki/File:'

class CandidateTests(unittest.TestCase):
    def test_only_by_and_by_sa_pictures_with_an_unknown_author_are_candidates(self):
        places = {'A': {'a': 'Unknown author', 'l': 'CC BY-SA 3.0', 'p': P + 'A.jpg'}, 'B': {'a': 'Unknown author', 'l': 'Public domain', 'p': P + 'B.jpg'},
                  'C': {'a': 'Jane Doe', 'l': 'CC BY 4.0', 'p': P + 'C.jpg'}, 'D': {'a': '', 'l': 'CC BY 2.5', 'p': P + 'D%2C_x.jpg'}, 'E': {'a': 'Unknown', 'l': 'CC BY 2.0', 'p': 'https://example.org/x'}}
        species = {'Achyrachaena mollis': {'a': 'Unknown', 'l': 'CC BY 2.5', 'p': P + 'Ach.jpg'}, 'Z': {'a': 'Anonymous', 'l': 'CC BY-SA 4.0', 'p': P + 'Z.jpg'}}
        got = [(c['kind'], c['key'], c['file']) for c in a.candidates(places, species)]
        self.assertEqual(got, [('place', 'A', 'A.jpg'), ('place', 'D', 'D,_x.jpg'), ('species', 'Achyrachaena mollis', 'Ach.jpg'), ('species', 'Z', 'Z.jpg')])

class ClassifyTests(unittest.TestCase):
    def meta(self, artist='', credit='', attribution=''):
        return {k: {'value': v} for k, v in (('Artist', artist), ('Credit', credit), ('Attribution', attribution)) if v}
    def test_an_artist_now_on_the_page_wins(self):
        self.assertEqual(a.classify(self.meta(artist='<a href="x">Jane Doe</a>'), 'Uploader'), ('artist', 'Jane Doe'))
    def test_the_attribution_field_comes_next(self):
        self.assertEqual(a.classify(self.meta(attribution='Photo by J. Roe'), 'Uploader'), ('attribution', 'Photo by J. Roe'))
    def test_the_uploader_is_used_only_when_the_credit_says_own_work(self):
        self.assertEqual(a.classify(self.meta(credit='Own work'), 'Uploader'), ('own-work', 'Uploader'))
        self.assertEqual(a.classify(self.meta(credit='<a>Flickr</a>'), 'Uploader'), ('none', ''))   # an uploader is not always the author
        self.assertEqual(a.classify(self.meta(credit='Own work'), ''), ('none', ''))
    def test_an_unknown_artist_is_not_an_author(self):
        self.assertEqual(a.classify(self.meta(artist='Unknown author'), ''), ('none', ''))

class RunTests(unittest.TestCase):
    def test_lookup_reads_the_first_revision_user_and_the_credit(self):
        j = {'query': {'pages': {'1': {'imageinfo': [{'extmetadata': {'Credit': {'value': 'Own work'}}}], 'revisions': [{'user': 'Someone'}]}}}}
        with mock.patch.object(a.wm, 'get', return_value=j) as g:
            self.assertEqual(a.lookup('A b.jpg'), ('own-work', 'Someone'))
        self.assertIn('commons.wikimedia.org', g.call_args[0][0]); self.assertIn('File%3AA%20b.jpg', g.call_args[0][0])
        with mock.patch.object(a.wm, 'get', return_value=None): self.assertEqual(a.lookup('gone.jpg'), ('none', ''))
    def test_the_report_counts_by_kind_and_class(self):
        rows = [dict(kind='place', key='A', file='A.jpg', licence='CC BY 4.0', author='Unknown author', **{'class': 'artist', 'name': 'Jane'}),
                dict(kind='species', key='S', file='S.jpg', licence='CC BY-SA 3.0', author='Unknown', **{'class': 'none', 'name': ''})]
        text = a.report(rows)
        self.assertIn('| place | 1 | 1 | 0 | 0 | 0 |', text); self.assertIn('| species | 1 | 0 | 0 | 0 | 1 |', text); self.assertIn('| place | A | CC BY 4.0 | Unknown author | artist | Jane |', text)

if __name__ == '__main__': unittest.main()
