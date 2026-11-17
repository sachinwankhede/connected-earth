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


def test_review_lists_outlines_whose_name_does_not_fit_and_drops_nothing():
    """#977: review() lists outlines whose name does not fit the place; it changes nothing."""
    root = tempfile.mkdtemp()
    for d in ('places', 'outlines'): os.makedirs(os.path.join(root, 'data', d))
    def put(pid, name, oname, size=0.1):
        json.dump({'id': pid, 'name': name, 'lat': 40.0, 'lon': -100.0}, open(os.path.join(root, 'data', 'places', pid + '.json'), 'w'))
        ring = [-100.0, 40.0, -100.0 + size, 40.0, -100.0 + size, 40.0 + size, -100.0, 40.0]
        json.dump({'n': oname, 'r': [ring]}, open(os.path.join(root, 'data', 'outlines', pid + '.json'), 'w'))
    put('ok', 'Loess Hills State Forest', 'Loess Hills State Forest')
    put('trail', 'Cape Cod National Seashore', 'Cape Cod Rail Trail')
    put('kind', 'Elk State Park', 'Elk State Forest', size=1.0)
    put('part', 'Delaware Bay and Bombay Hook', 'Bombay Hook National Wildlife Refuge')
    rows = {r[0]: r for r in oc.review(root)}
    assert 'ok' not in rows
    assert rows['trail'][4] == ['extra words', 'small'] and rows['kind'][4] == ['kind'] and 'missing words' in rows['part'][4]
    assert os.path.exists(os.path.join(root, 'data', 'outlines', 'trail.json'))


def test_refuses_a_unit_that_is_not_the_place():
    assert oc.refuses('Elk State Park', 'Elk State Forest') and oc.refuses('Arapaho National Wildlife Refuge', 'Arapaho National Forest')
    assert oc.refuses('Cape Cod National Seashore', 'Cape Cod Rail Trail') and oc.refuses('Dale Hollow Lake State Park', 'Dale Hollow Lake Wildlife Management Area')
    assert oc.refuses('San Bernardino National Forest', 'San Bernardino Other')
    assert not oc.refuses('Loess Hills State Forest', 'Loess Hills State Forest') and not oc.refuses('Mill Bluff State Park', 'Mill Bluff State Park-Iansr')
    assert not oc.refuses('Appalachian Trail Corridor', 'Appalachian National Scenic Trail Corridor')   # the place's own name says trail and corridor
    assert not oc.refuses('Loess Hills', 'Loess Hills State Forest')   # no kind on the place: the name decides
