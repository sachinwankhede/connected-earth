import json, os, shutil, sys, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'jobs')); sys.path.insert(0, os.path.join(ROOT, 'build'))
import cleanwikis

def fake(answer):
    """A get() that answers like the Wikipedia API from {asked title: ('redirect', to[, fragment]) | 'missing' | 'disambig' | 'page'}."""
    def get(url):
        import urllib.parse
        titles = urllib.parse.unquote(url.split('titles=')[1]).split('|'); red = []; pages = {}
        for t in titles:
            a = answer.get(t, 'page')
            if isinstance(a, tuple):
                red.append({'from': t, 'to': a[1], **({'tofragment': a[2]} if len(a) > 2 else {})}); pages.setdefault(a[1], {'title': a[1]})
            elif a == 'missing': pages[t] = {'title': t, 'missing': ''}
            elif a == 'disambig': pages[t] = {'title': t, 'pageprops': {'disambiguation': ''}}
            else: pages[t] = {'title': t}
        return {'query': {'redirects': red, 'pages': {str(i): p for i, p in enumerate(pages.values())}}}
    return get

class Decide(unittest.TestCase):
    def test_redirect_to_the_rows_page_is_the_same(self):
        self.assertEqual(cleanwikis.decide([('Great egret', 'Ardea alba')], fake({'Ardea alba': ('redirect', 'Great egret')})), {('Great egret', 'Ardea alba'): True})
    def test_different_pages_are_kept(self):
        self.assertEqual(cleanwikis.decide([('Soil', 'Soil fertility')], fake({})), {('Soil', 'Soil fertility'): False})
    def test_missing_disambiguation_and_section_are_kept(self):
        ps = [('A', 'B'), ('C', 'D'), ('E', 'F')]
        r = cleanwikis.decide(ps, fake({'B': ('redirect', 'A', 'History'), 'C': 'disambig', 'D': ('redirect', 'C'), 'F': 'missing', 'E': 'missing'}))
        self.assertEqual(r, {p: False for p in ps})
    def test_more_than_fifty_titles_are_asked_in_chunks(self):
        asked = []
        def get(url): asked.append(url); return fake({})(url)
        cleanwikis.lookup(['T%d' % i for i in range(120)], get); self.assertEqual(len(asked), 3)

class Apply(unittest.TestCase):
    def test_only_the_nodes_wiki_changes(self):
        import species
        orig = species.table
        species.table = lambda root=None: {'x': {'sid': 'sp1', 'wiki': 'Great egret'}}
        d = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(d, 'data', 'places'))
            node = {'id': 'a', 'sp': 'sp1', 'wiki': 'Ardea alba', 'desc': 'd'}; other = {'id': 'b', 'sp': 'sp1', 'wiki': 'Egrets', 'desc': 'e'}
            json.dump({'nodes': [node, other], 'name': 'P'}, open(os.path.join(d, 'data', 'places', 'p.json'), 'w'))
            self.assertEqual(cleanwikis.apply(d, {('Great egret', 'Ardea alba'): True}), (1, 1))
            e = json.load(open(os.path.join(d, 'data', 'places', 'p.json')))
            self.assertEqual(e['nodes'][0], {'id': 'a', 'sp': 'sp1', 'desc': 'd'}); self.assertEqual(e['nodes'][1], other); self.assertEqual(e['name'], 'P')
            self.assertEqual(cleanwikis.apply(d, {('Great egret', 'Ardea alba'): True}, dry=True), (0, 0))
        finally: species.table = orig; shutil.rmtree(d)

if __name__ == '__main__': unittest.main()
