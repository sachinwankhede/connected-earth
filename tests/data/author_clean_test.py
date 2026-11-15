"""lib/author_clean.py: one stored form for a picture's author (#887)."""
import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
from author_clean import clean_author as c, is_dirty, is_unknown

class CleanTests(unittest.TestCase):
    def test_names_and_handles_are_unchanged(self):
        for a in ('Diego Delso', 'Geoff0522', '1brownsfan', 'Jacques Descloitres, MODIS Land Rapid Response Team, NASA/GSFC', 'Michael from Minnesota (@Michael)'):
            self.assertEqual(c(a), a); self.assertFalse(is_dirty(a))
    def test_a_web_address_in_brackets_leaves_no_dangling_bracket(self):   # the 15 Nov cleanauthors run wrote "JJ Harrison (" and "David Gubler ("
        self.assertEqual(c('JJ Harrison (https://www.jjharrison.com.au/)'), 'JJ Harrison')
        self.assertEqual(c('Kabelleger / David Gubler (http://www.bahnbilder.ch).'), 'Kabelleger / David Gubler')
        self.assertEqual(c('Jane Doe [www.example.org]'), 'Jane Doe'); self.assertEqual(c('Jane Doe (jane@example.org)'), 'Jane Doe')
        self.assertEqual(c('Michael from Minnesota (@Michael)'), 'Michael from Minnesota (@Michael)')   # a real bracket stays
        self.assertEqual(c('Sasata (edited by Noodle snacks'), 'Sasata (edited by Noodle snacks'); self.assertEqual(c('James Roberts (Jampp…'), 'James Roberts (Jampp…'); self.assertFalse(is_dirty('James Roberts (Jampp…'))   # a source's own truncation is not touched
        self.assertEqual(c('Aviceda at English Wikipedia\n\n(Original text: Tom (talk))'), 'Aviceda at English Wikipedia')
        self.assertEqual(c("Noodle snacks (https://www.jjharrison.com.au/)Bennett's Wallaby)"), "Noodle snacks Bennett's Wallaby")
    def test_email_is_no_author(self):
        self.assertEqual(c('toddander@gmail.com'), ''); self.assertFalse(is_unknown('toddander@gmail.com'))
        self.assertEqual(c('Jane Doe <jane@example.org>'), 'Jane Doe'); self.assertEqual(c('mailto me: jane@example.org'), 'mailto me')
    def test_uploader_sentence_becomes_the_name(self):
        self.assertEqual(c('The original uploader was Decumanus at English Wikipedia.'), 'Decumanus')
        self.assertEqual(c('en:User:SheepNotGoats Original uploader was SheepNotGoats at en.wikipedia'), 'SheepNotGoats')
        self.assertEqual(c('No machine-readable author provided. Miskatonic assumed (based on copyright claims).'), 'Miskatonic')
    def test_talk_stamp_boilerplate_and_urls_are_cut(self):
        self.assertEqual(c('Beeblebrox (talk) 06:06, 13 January 2009 (UTC)'), 'Beeblebrox')
        self.assertEqual(c('Jeff Noble Camera location33° 18′ 02.4″ N, 91° 16′ 39″ W View this and'), 'Jeff Noble')
        self.assertEqual(c('Aaron Fulkerson - http://www.ninje.com'), 'Aaron Fulkerson'); self.assertEqual(c('WV-Mike www.EpicRoadTrips.us'), 'WV-Mike')
        self.assertEqual(c('U.S. Army Corps of Engineers from USA; cropped by Beyond My Ken (talk)'), 'U.S. Army Corps of Engineers from USA; cropped by Beyond My Ken')
        self.assertEqual(c('<a href="x">Ann</a> &amp; Bob'), 'Ann & Bob')
    def test_unknown_forms_are_empty(self):
        for a in ('', None, 'Unknown', 'Unknown author', 'Unknown authorUnknown author', 'Anonymous', 'author unknown', '?', 'See file page'):
            self.assertEqual(c(a), ''); self.assertFalse(is_dirty(a))
    def test_dirty_means_clean_would_change_it(self):
        self.assertTrue(is_dirty('The original uploader was Elf at English Wikipedia.')); self.assertTrue(is_dirty('x@y.com')); self.assertFalse(is_dirty('  Ann   Lee '))

if __name__ == '__main__': unittest.main()
