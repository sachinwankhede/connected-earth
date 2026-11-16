#!/usr/bin/env python3
"""#977: lib/outline_check.py finds a place point more than N km outside its own outline, and only that."""
import json, os, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'lib'))
import outline_check as oc

square = [0, 0, 1, 0, 1, 1, 0, 1, 0, 0]   # a 1 x 1 degree square at the equator (about 111 km a side)
assert oc.inside(0.5, 0.5, [square]) and not oc.inside(2, 0.5, [square])
assert abs(oc.distance_km(2, 0.5, [square]) - 111.2) < 1, oc.distance_km(2, 0.5, [square])
with tempfile.TemporaryDirectory() as t:
    for d in ('outlines', 'places'): os.makedirs(os.path.join(t, 'data', d))
    for pid, lon, lat in (('in', 0.5, 0.5), ('near', 1.02, 0.5), ('far', 3, 0.5), ('nopoint', None, None)):
        json.dump({'n': pid, 'r': [square]}, open(os.path.join(t, 'data', 'outlines', pid + '.json'), 'w'))
        json.dump({'id': pid, 'lat': lat, 'lng': lon}, open(os.path.join(t, 'data', 'places', pid + '.json'), 'w'))
    got = oc.outside(t, 5.0)
    assert [p for _, p in got] == ['far'], got   # 'near' is 2 km out (under 5), 'in' is inside, 'nopoint' has no point
    assert [p for _, p in oc.outside(t, 1.0)] == ['far', 'near'], oc.outside(t, 1.0)
print('ok')
