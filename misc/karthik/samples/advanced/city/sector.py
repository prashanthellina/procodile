#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 14, 2009 1:14:01 PM$"

from procodile.procedural import BaseGenerator
from road_layout import make_roads
from plot import RuralPlot
from road import SimpleRoad
from road import Junction

class Sector(BaseGenerator):

    CONFIG = (
                 'length', (25, 50),
                 'width', (25, 50),
                 'num_roads', (2, 2),
                 'road_width', (5, 15),
                 'min_gap_btw_roads', (8, 10),
                 'height_range', [(.1, 0), (.6, (3,15)), (.25, (15, 50)),
                                (.05, (50, 100)), (.0, (100,200))]
             )

    SUB_GENERATORS = {
                        'sector': None,
                        'rural_plot': RuralPlot,
                        'road': SimpleRoad,
                        'junction': Junction
                     }

    def generate(self, config):
        C = config

        roads, junctions, spaces = make_roads(C.length, C.width,
                                        C.road_width, C.num_roads,
                                        C.min_gap_btw_roads, self.picker)

        road_width = C.road_width * 0.8 if C.road_width > 2 else C.road_width
        
        for origin, (slength, swidth), rotation in spaces:
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))

            self.subgen('sector', origin, slength, swidth, C.num_roads,
                        road_width, C.min_gap_btw_roads, [C.height_range])


        for road in roads:
            origin, (road_length, road_width), rotation = road
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))

            self.subgen('road', origin, road_length, road_width)

        for jn in junctions:
            origin, (jn_length, jn_width), rotation = jn
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))

            self.subgen('junction', origin, jn_length, jn_width)

        if not spaces:
            self.subgen('rural_plot', (0, 0, 0), C.length, C.width,
                        [C.height_range])

Sector.SUB_GENERATORS['sector'] = Sector

class SimpleCity(BaseGenerator):

    CONFIG = (
                 'length', (500, 500),
                 'width', (500, 500),
              )
    SUB_GENERATORS = {
                        'sector': Sector,
                        'road': SimpleRoad,
                        'junction': Junction
                     }
    def generate(self, config):
        C = config

        levels = [1, 2, 3, 4]
        
        level = self.picker.pick(levels)

        if level == 1:
            plot_gap = 4
            height_width_ratio = 8.
            road_width = 5
            min_gap_btw_roads = 8
            build_height = self.picker.pick((100,300))
            plot_width = build_height/height_width_ratio
            if plot_width < 10:
                plot_width = 10
            plot_length = (plot_width,plot_width*3)
            height_range = [(.1, 0), (.3, (3,15)), (.2, (15, 50)),
                            (.2, (50, 100)), (.2, (100,200))]

        elif level == 2:
            plot_gap = 10
            height_width_ratio = 8.
            road_width = 8
            min_gap_btw_roads = 10
            build_height = self.picker.pick((50,70))
            plot_width = build_height/height_width_ratio
            if plot_width < 10:
                plot_width = 10
            plot_length = (plot_width,plot_width*3)
            height_range = [(.1, 0), (.3, (3,15)), (.4, (15, 50)),
                            (.2, (50, 100)), (0.0, (100,200))]

        elif level == 3:
            plot_gap = 10
            height_width_ratio = 4.
            road_width = 8
            min_gap_btw_roads = 10
            build_height = self.picker.pick((3,15))
            plot_width = build_height/height_width_ratio
            if plot_width < 10:
                plot_width = 10
            plot_length = (plot_width,plot_width*3)
            height_range = [(.1, 0), (.3, (3,15)), (.5, (15, 50)),
                            (.1, (50, 100)), (0.0, (100,200))]

        else:
            plot_gap = 12
            height_width_ratio = 2.
            road_width = 8
            min_gap_btw_roads = 20
            build_height = self.picker.pick((3,15))
            plot_width = build_height/height_width_ratio
            if plot_width < 15:
                plot_width = 15
            plot_length = (plot_width,plot_width*4)
            height_range = [(.1, 0), (.6, (3,15)), (.25, (15, 50)),
                            (.05, (50, 100)), (.0, (100,200))]

        roads, junctions, spaces = make_roads(C.length, C.width,
                                        road_width, 2,
                                        min_gap_btw_roads, self.picker)

        for origin, (slength, swidth), rotation in spaces:
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))
            
            self.subgen('sector', origin,
                        slength, swidth, 2, road_width, min_gap_btw_roads,
                        [height_range])

        for road in roads:
            origin, (road_length, road_width), rotation = road
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))

            self.subgen('road', origin, road_length, road_width)

        for jn in junctions:
            origin, (jn_length, jn_width), rotation = jn
            x,y = origin
            origin = ((x, y, 0), (rotation, (0, 0, 1)))

            self.subgen('junction', origin, jn_length, jn_width)