#! /usr/bin/python

from procodile.procedural import BaseGenerator
import procodile.draw as draw

class Divider(BaseGenerator):

    CONFIG = (
                 'length', (100, 500),
                 'width', (1, 4),
                 'height', (0.4, 1.5)
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):
        C = config
        divider = draw.makeBox(C.width, C.length, C.height)
        self.add_geom(divider)

class SimpleRoad(BaseGenerator):

    CONFIG = (
                 'length', (100, 500),
                 'width', (1, 4),
                 'height', (0.1, 0.1),
                 'lanes', (1, 6),
                 'divider_width', (0.1, 0.5)
             )

    SUB_GENERATORS = {
                        'divider': Divider,
                     }

    def generate(self, config):
        C = config

        road = draw.makeBox(C.width, C.length, 78)
        road.visible = False
        self.add_geom(road)

        s_roads = self.get_intersection()
#        print 'got intersections', s_roads
        if not s_roads:
            road.visible = True

#        if C.lanes > 1:
#            divider_origin = (C.width/2-C.divider_width/2, 0, C.height)
#            self.subgen('divider', divider_origin, C.length, C.divider_width)
