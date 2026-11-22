"""jobs/about.py clean(): a place summary cut mid-sentence (the Wikipedia extract stops at "(est.") is dropped, a whole sentence is kept."""
import ast, os, re, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import species

def load_clean():
    src = open(os.path.join(ROOT, 'jobs', 'about.py')).read()
    tree = ast.parse(src)
    keep = [n for n in tree.body if (isinstance(n, ast.FunctionDef) and n.name == 'clean') or (isinstance(n, ast.Assign) and getattr(n.targets[0], 'id', '') == 'MAXW')]
    ns = {'re': re, 'species': species}
    exec(compile(ast.Module(keep, []), 'about', 'exec'), ns)
    return ns['clean']

class T(unittest.TestCase):
    def test_cut_extract_dropped(self):
        c = load_clean()
        self.assertEqual(c('Unicoi State Park & Lodge is a 1,050-acre state park (est.'), '')

    def test_whole_sentence_kept_and_brackets_removed(self):
        c = load_clean()
        self.assertEqual(c('Mount Rainier National Park (pronounced x) is a large park in Washington state, United States.'), 'Mount Rainier National Park is a large park in Washington state, United States.')

    def test_no_final_stop_dropped(self):
        self.assertEqual(load_clean()('A long enough text that stops without any final stop'), '')

if __name__ == '__main__': unittest.main()
