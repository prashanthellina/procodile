#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 14, 2009 3:25:24 PM$"

from procodile.procedural import BaseGenerator
import procodile.draw as draw
from plot import Plot, RuralPlot
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
                        'plot': Plot,
                        'rural_plot': RuralPlot,
                        'layout':None,
                        'road': road
                     }

    def generate(self, config):
        C = config

        if C.length < 1 or C.width < 1:
            print 'returning empty layout'
            return

#        layouts = self.make_layouts(C.length, C.width, C.plot_width, C.road_width)
        print 'len n wid are ',C.level, C.length, C.width, C.road_width, self.picker.pick((3,5)), 20, self.picker
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

#            else:
#                self.subgen('plot', origin, slength,swidth, [C.plot_length],
#                                [C.height_range], C.plot_gap)
        for road in roads:
            origin, (road_length, road_width), rotation = road
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))
            self.subgen('road', origin,
                    road_length, road_width)
                    
#        for (origin, (llength, lwidth)) in layouts:
#            self.subgen('layout', origin, C.level, llength, lwidth, C.plot_width,
#                        [C.plot_length],  C.road_width, [C.height_range], C.plot_gap)
#
#        if not layouts:
#            location = ((C.length,0,0), (math.pi / 2, (0, 0, 1))) if C.length < C.width else (0,0,0)
#            l,w = (C.width, C.length) if C.length < C.width else (C.length, C.width)
##            print '$' * 10, C.plot_length
#
#            if C.level in [3, 4]:
#                self.subgen('rural_plot', location, l,w,
#                            [C.height_range])
#
#            else:
#                self.subgen('plot', location, l,w, [C.plot_length],
#                                [C.height_range], C.plot_gap)

#            loc, dir = location if len(location)==2 else (location, None)
#            x, y, z = loc
#            left_road = (x - C.road_width, y, z)
#            right_road = (x + l, y, z)
#            v_road_origins = [left_road, right_road]
#            bottom_road = ((x, y, z), (-math.pi / 2, (0, 0, 1)))
#            up_road = ((x, y + w + C.road_width, z), (-math.pi / 2, (0, 0, 1)))
#            h_road_origins = [bottom_road, up_road]
#            for ro in h_road_origins:
#                self.subgen('road', ro,
#                        l, C.road_width)
#            for ro in v_road_origins:
#                self.subgen('road', ro,
#                        w, C.road_width)


    def make_layouts(self, length, width, plot_width, road_width):
        if length < width:
            if length > plot_width  and length/2 > plot_width+road_width:
                l,w = [length/2-road_width/2,width]
                space1 = ((0,0,0), (l,w))
                space2 = ((l+road_width, 0,0), (l,w))
                return [space1, space2]
        else:
            if width > plot_width and width/2 > plot_width+road_width:
                l,w = [length, width/2-road_width/2]
                space1 = ((0,0,0), (l,w))
                space2 = ((0,w+road_width, 0), (l,w))
                return [space1, space2]
        return []

Layout.SUB_GENERATORS['layout']=Layout