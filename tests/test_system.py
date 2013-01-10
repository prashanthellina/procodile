#!/usr/bin/env python

from nose import with_setup

import procodile.system as system
from procodile.utils import fequals

def test_system_obj_exists():
    assert(system.SYSTEM)

def test_color():

    # Check if color construction works
    c = system.Color((0.5, 0.6, 0.7))
    assert(fequals(c.red, 0.5))
    assert(fequals(c.green, 0.6))
    assert(fequals(c.blue, 0.7))

    # Check if RGB to HSV conversion works
    h,s,v = c.get_hsv()
    assert(fequals(h, 0.583333333333))
    assert(fequals(s, 0.285714285714))
    assert(fequals(v, 0.7))

    # Check if HSV to RGB conversion works
    c = system.Color(hsv=(0.583333333333, 0.285714285714, 0.7))
    r, g, b = c.get_rgb()
    assert(fequals(r, 0.5))
    assert(fequals(g, 0.6))
    assert(fequals(b, 0.7))

    # Check if invalid inputs are handled sanely
    c = system.Color((2, -1, 20.5))
    assert(fequals(c.red, 1))
    assert(fequals(c.green, 0))
    assert(fequals(c.blue, 1))

def test_material_color():
    
    # Check if color construction works
    m = system.MaterialColor((0.5, 0.6, 0.7))
    assert(fequals(m.red, 0.5))
    assert(fequals(m.green, 0.6))
    assert(fequals(m.blue, 0.7))

    # Check if HSV conversion works
    h, s, v = m.get_hsv()
    assert(fequals(h, 0.58333333333333337))
    assert(fequals(s, 0.28571428571428564))
    assert(fequals(v, 0.69999999999999996))

    # Check that diffuse is same as MaterialColor
    dh, ds, dv = m.diffuse.get_hsv()
    assert(fequals(h, dh))
    assert(fequals(s, ds))
    assert(fequals(v, dv))

    # Check if value of ambient color is lesser
    h, s, v = m.ambient.get_hsv()
    assert(fequals(h, 0.58333333333333337))
    assert(fequals(s, 0.28571428571428559))
    assert(fequals(v, 0.55999999999999994)) # <--

    # Check if value of specular color is greater
    h, s, v = m.specular.get_hsv()
    assert(fequals(h, 0.58333333333333337))
    assert(fequals(s, 0.28571428571428559))
    assert(fequals(v, 0.84)) # <--

    # Check if default emissive color is black
    h, s, v = m.emissive.get_hsv()
    assert(h == s == v)
    assert(fequals(h, 0))

    # Set value for emissive and check that
    # only 'value' component is modified
    m.set_emissive_value(0.5)
    h, s, v = m.emissive.get_hsv()
    assert(fequals(h, 0.58333333333333337))
    assert(fequals(s, 0.28571428571428564))
    assert(fequals(v, 0.5))

    # Check update() method
    m.ambient_change = -.4

    #  Check that nothing changed
    h, s, v = m.ambient.get_hsv()
    assert(fequals(h, 0.58333333333333337))
    assert(fequals(s, 0.28571428571428559))
    assert(fequals(v, 0.55999999999999994))

    # do update()
    m.update()
   
    # Check that update of ambient has worked 
    h, s, v = m.ambient.get_hsv()
    assert(fequals(h, 0.583333333333))
    assert(fequals(s, 0.285714285714))
    assert(fequals(v, 0.42))
