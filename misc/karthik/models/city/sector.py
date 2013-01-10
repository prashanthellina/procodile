##! /usr/bin/python
#
#__author__="karthik"
#__date__ ="$Sep 10, 2009 9:51:15 AM$"
#
#from procodile.procedural import BaseGenerator
#import procodile.draw as draw
#from layout import Layout
#from road import make_roads
#
#class Sector(BaseGenerator):
#
#    CONFIG = (
#                 'length', (1000, 5000),
#                 'width', (1000, 5000),
#                 'num_roads', (2, 4),
#                 'road_width', (10, 20),
#                 'min_gap_btw_roads', (100, 200)
#             )
#
#    SUB_GENERATORS = {
#                        'layout': Layout,
#                     }
#
#    def generate(self, config):
#
#        road_data, spaces = make_roads(config.length, config.width,
#                                        config.road_width, config.num_roads,
#                                        config.min_gap_btw_roads, self.seed)
#
#        for index, (origin, (slength, swidth)) in enumerate(spaces):
#            self.subgen('layout', origin, slength, swidth)
