#!/usr/bin/env python3
import hashlib, io, os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "jobs"))
import largeplacephotos as l

PAGE = 'https://commons.wikimedia.org/wiki/File:Amazon17_%285641020319%29.jpg'

class T(unittest.TestCase):
    def test_file_name_comes_from_the_commons_page_only(self):
        self.assertEqual(l.commons_name(PAGE), 'Amazon17_(5641020319).jpg')
        self.assertEqual(l.commons_name('https://commons.wikimedia.org/wiki/File:A b.jpg#x'), 'A_b.jpg')
        for bad in (None, '', 'https://example.org/wiki/File:A.jpg', 'https://commons.wikimedia.org/wiki/Category:A'): self.assertIsNone(l.commons_name(bad))

    def test_thumbnail_address_uses_the_md5_folder_and_stays_on_the_commons_host(self):
        n = 'Amazon17_(5641020319).jpg'; h = hashlib.md5(n.encode()).hexdigest()
        u = l.thumb_url(n, 500)
        self.assertTrue(u.startswith('https://upload.wikimedia.org/wikipedia/commons/thumb/%s/%s/' % (h[0], h[:2])))
        self.assertTrue(u.endswith('/500px-Amazon17_%285641020319%29.jpg'))
        self.assertEqual(l.source_urls(PAGE), [l.thumb_url(n, 500), l.thumb_url(n, 330)]); self.assertEqual(l.source_urls('x'), [])

    def test_todo_skips_done_and_unusable_and_respects_the_limit(self):
        P = {k: {'f': k + '.jpg', 'p': PAGE} for k in 'cba'}; P['nofile'] = {'p': PAGE}; P['other'] = {'f': 'o.jpg', 'p': 'https://x.org/'}
        self.assertEqual(l.todo(P, {'a': 'a.webp'}, 0), ['b', 'c']); self.assertEqual(l.todo(P, {}, 2), ['a', 'b'])

    def test_copy_is_a_webp_of_at_most_400_px(self):
        from PIL import Image
        im = Image.new('RGB', (1000, 500), (10, 120, 60)); data, size = l.shrink(im)
        self.assertEqual(size, (400, 200)); out = Image.open(io.BytesIO(data)); self.assertEqual(out.format, 'WEBP'); self.assertEqual(l.out_name('x/y.jpg'), 'x/y.webp')

    def test_a_failing_address_is_skipped_and_the_next_one_tried(self):
        def get(u, raw=False):
            if u == 'bad': raise RuntimeError('too many errors (HTTP 400) for x')
            return {'a': None, 'b': b'data'}[u]
        self.assertEqual(l.download(['bad', 'a', 'b'], get), b'data'); self.assertIsNone(l.download(['bad', 'a'], get)); self.assertIsNone(l.download([], get))

    def test_the_list_is_written_whole_with_every_call(self):
        import json, tempfile
        d = tempfile.mkdtemp(); old = l.LARGE; l.LARGE = os.path.join(d, 'large.json')
        try:
            l.save({'a': 'a.webp'}); l.save({'a': 'a.webp', 'b': 'b.webp'})
            self.assertEqual(json.load(open(l.LARGE)), {'a': 'a.webp', 'b': 'b.webp'}); self.assertEqual(os.listdir(d), ['large.json'])
        finally: l.LARGE = old

if __name__ == '__main__': unittest.main()
