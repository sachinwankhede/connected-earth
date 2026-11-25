"""jobs/identitycheck.py (#1142): a species row on a genus page and a genus row on a species page are listed; a synonym, a correct row and a row with no page are not."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'jobs'))
import identitycheck as IC
ident = {'ranks': {'G': 'genus', 'S': 'species', 'F': 'family'}, 'rows': {
    'a-b': ['Q1', 'G', 'A', 'taxon', ''], 'acer': ['Q2', 'S', 'Acer pictum', 'taxon', ''], 'c-d': ['Q3', 'S', 'Eurema d', 'taxon', ''],
    'e-f': ['Q4', 'S', 'E f', 'taxon', ''], 'g-h': ['', '', '', 'taxon', 'row has no page'], 'i-j': ['Q5', 'F', 'I', 'taxon', ''], 'res': ['Q6', 'G', 'X', 'resource', '']}}
rows = {'a-b': {'latin': 'A b'}, 'acer': {'latin': 'Acer'}, 'c-d': {'latin': 'C d'}, 'e-f': {'latin': 'E f'}, 'g-h': {'latin': 'G h'}, 'i-j': {'latin': 'I j'}, 'res': {'latin': 'X y'}}
m = IC.mismatches(rows, ident)
assert set(m) == {'a-b', 'acer', 'i-j'}, m
assert m['a-b'][0] == 'species row on a genus page' and m['acer'][0] == 'genus row on a species page' and m['i-j'][3] == 'family'
print('identitycheck ok')
