"""The first-view budget (#369) fails on the things it is meant to catch, and passes on today's page."""
import os, sys, tempfile, unittest, shutil
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'build'))
import firstview

PAGE = '<link rel="preconnect" href="https://server.arcgisonline.com"><script>var GLYPHS = "https://tiles.openfreemap.org/fonts/{f}/{r}.pbf"; var S = { a: { type: "vector", url: "https://tiles.openfreemap.org/planet" } };</script><a href="https://en.wikipedia.org/wiki/Osprey">x</a>'

class Hosts(unittest.TestCase):
    def test_links_are_not_loads(self):
        self.assertEqual(firstview.resource_hosts(PAGE), {'server.arcgisonline.com', 'tiles.openfreemap.org'})
    def test_new_script_host_is_found(self):
        self.assertIn('cdn.example.com', firstview.resource_hosts(PAGE + '<script src="https://cdn.example.com/x.js"></script>'))
    def test_new_map_source_host_is_found(self):
        self.assertIn('t.example.com', firstview.resource_hosts(PAGE + 'var T = { type: "raster", url: "https://t.example.com/{z}" };'))

class Weight(unittest.TestCase):
    def make(self, extra_host='', pad=0):
        d = tempfile.mkdtemp(); self.addCleanup(shutil.rmtree, d)
        os.makedirs(os.path.join(d, 'api/places/main'))
        open(os.path.join(d, 'index.html'), 'w').write(PAGE + extra_host)
        open(os.path.join(d, 'maplibre-gl-1.0.js'), 'wb').write(os.urandom(pad))
        for f in ('index-world', 'cards-world'): open(os.path.join(d, 'api/places/main/%s.json' % f), 'w').write('[]')
        os.makedirs(os.path.join(d, 'api/journeys')); open(os.path.join(d, 'api/journeys/main.json'), 'w').write('{}')
        return d
    def test_small_page_passes(self):
        self.assertEqual(firstview.check(self.make())[1], 0)
    def test_overweight_fails(self):
        out, bad = firstview.check(self.make(pad=firstview.FIRST_VIEW_GZIP_MAX + 10_000))
        self.assertEqual(bad, 1); self.assertTrue(any('OVER' in l for l in out))
    def test_new_host_fails(self):
        out, bad = firstview.check(self.make('<script src="https://cdn.example.com/x.js"></script>'))
        self.assertEqual(bad, 1); self.assertTrue(any('NEW HOST: cdn.example.com' in l for l in out))

@unittest.skipUnless(os.path.exists(os.path.join(firstview.ROOT, 'index.html')) and os.path.exists(os.path.join(firstview.ROOT, 'api/places/main/index-world.json')), 'build has not run')
class Today(unittest.TestCase):
    def test_built_page_is_inside_the_budget(self):
        out, bad = firstview.check()
        self.assertEqual(bad, 0, '\n'.join(out))

if __name__ == '__main__': unittest.main()
