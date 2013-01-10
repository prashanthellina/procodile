#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 14, 2009 3:25:24 PM$"

from procodile.procedural import BaseGenerator
import procodile.draw as draw
from plot import RuralPlot
from road_layout import make_roads
from procodile.procedural import BaseGenerator, Material as M
from road import SimpleRoad as road
import math

class Layout(BaseGenerator):

    CONFIG = (
                'level', [1,2,3,4],
                'length', (1000, 5000),
                'width', (1000, 5000),
                'plot_length',None,
                'plot_width', (20, 40),
                'road_width', (5, 10),
                'height_range', None,
                'plot_gap', (5, 12)
             )

    SUB_GENERATORS = {
                        'rural_plot': RuralPlot,
                        'road': road
                     }

    def generate(self, config):
        C = config

        if C.length < 1 or C.width < 1:
            print 'returning empty layout'
            return

        roads, junctions, spaces = make_roads(C.length, C.width,
                                            C.road_width, self.picker.pick((3,5)),
                                            20, self.picker)

        if not spaces:
            print 'no spaces'
            return
        for origin, (slength, swidth), rotation in spaces:
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))
            
            self.subgen('rural_plot', origin, slength,swidth,
                        [C.height_range])

        for road in roads:
            origin, (road_length, road_width), rotation = road
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))
            self.subgen('road', origin,
                    road_length, road_width)
