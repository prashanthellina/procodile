##! /usr/bin/python
#
#__author__="karthik"
#__date__ ="$Sep 10, 2009 9:22:55 AM$"
#
#from procodile.procedural import BaseGenerator
#import procodile.draw as draw
#from sector import Sector
#from road import make_roads
#
#class City(BaseGenerator):
#
#    CONFIG = (
#                 'length', (100, 500),
#                 'width', (100, 500),
#                 'num_roads', (2, 4),
#                 'road_width', (30, 50),
#                 'min_gap_btw_roads', (100, 500)
#             )
#
#    SUB_GENERATORS = {
#                        'sector': Sector,
#                     }
#
#    def generate(self, config):
#
#        road_data, spaces = make_roads(config.length, config.width,
#                                        config.road_width, config.num_roads,
#                                        config.min_gap_btw_roads, self.seed)
#        plate = draw.makeBox(config.length, config.width, 1)
#        plate.translate((0,0,-1))
#        self.add_geom(plate)
#        for index, (origin, (slength, swidth)) in enumerate(spaces):
#            self.subgen('sector', origin, slength, swidth)
#
#
#
#
#
#
#
