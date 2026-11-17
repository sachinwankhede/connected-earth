#!/usr/bin/env python3
"""#1038: build/override_report.py sorts name overrides into spelling, form, group and other."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'build'))
import override_report as o

def test_classes():
    assert o.classify('Cattails', 'Cattail') == 'spelling' and o.classify('Beavertail cactus', 'Beaver-tail cactus') == 'spelling'
    assert o.classify('Leopard', 'Javan leopard') == 'form' and o.classify('Brittlebush', 'White brittlebush') == 'form'
    assert o.classify('Fungi and bacteria', 'Fungi and soil microbes') == 'group' and o.classify('Peat', 'Peat & bog') == 'group'
    assert o.classify('Argali', 'Marco Polo sheep') == 'other' and o.classify('Cardinal catchfly', 'Indian-pink') == 'other'
