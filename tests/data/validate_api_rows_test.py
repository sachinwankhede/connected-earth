#!/usr/bin/env python3
"""build/validate_api.py fails a Species tab row without its id, a food row of the wrong shape, a journeys file that is not the shape the app reads, and a journey end whose node is not in that place (#1013)."""
import json, os, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run(files):
    with tempfile.TemporaryDirectory() as d:
        for name, data in files.items():
            p = os.path.join(d, name); os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(data, open(p, 'w'))
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'build', 'validate_api.py'), d], capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

good = [['White-tailed deer', 556, 'b01b8c4b64b1.webp', 'odocoileus-virginianus'], ['Nameless', 3, 0, 'x-y']]
assert run({'species-tab/top.json': good})[0] == 0
assert run({'species-tab-pilot/g-birds-0.json': good})[0] == 0
for bad in ([['Deer', 5, 0]], [['Deer', 5, 0, 'Odocoileus Virginianus']], [['Latin name', 'Deer', 5, 0, 'odocoileus-virginianus']], [['Deer', '5', 0, 'x']]):
    code, out = run({'species-tab/top.json': bad}); assert code == 1 and 'top.json' in out, (bad, out)
sp = {'l': 'A b', 'n': 'N', 'tl': 2, 'ic': 'hopper'}
assert run({'species/a-b.json': dict(sp, ea=good, eb=[], rl=good)})[0] == 0
code, out = run({'species/a-b.json': dict(sp, ea=[['Deer', 5, 0]])}); assert code == 1 and 'a-b.json' in out, out

J = {'couple': 0.5, 'src': {}, 'cross': [{'id': 'osprey', 'type': 'species', 'title': 'Osprey', 'text': 't', 'ends': [{'eco': 'yellowstone', 'node': 'osprey'}]}]}
place = {'nodes': [{'id': 'osprey', 'latin': 'Pandion haliaetus', 'sid': 'pandion-haliaetus'}]}
assert run({'journeys/main.json': J, 'yellowstone.json': place})[0] == 0
code, out = run({'journeys/main.json': J, 'yellowstone.json': {'nodes': [{'id': 'other'}]}}); assert code == 1 and 'osprey' in out and 'yellowstone/osprey' in out, out
code, out = run({'journeys/main.json': J}); assert code == 1 and 'yellowstone/osprey' in out, out   # the place has no file
code, out = run({'journeys/main.json': {'couple': 0.5, 'src': {}, 'cross': [{'id': 'x'}]}, 'yellowstone.json': place}); assert code == 1 and 'journeys/main.json' in out, out
print('ok')
