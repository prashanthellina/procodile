#! /usr/bin/python

import math
from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw
from procodile.loader import get_class

bus = get_class(r'c:\code\procodile\misc\vikraman', 'bus.Bus')

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

class Junction(BaseGenerator):

    CONFIG = (
                 'length', (50, 100),
                 'width', (2, 10),
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):
        C = config
        line = draw.Line((C.width, 0, 0), (0, 0, 0))
        line = draw.Shape([line.unwrap()])
        junction = line.extrude((0, C.length, 0))
        
        self.add_geom(junction)

class SimpleRoad(BaseGenerator):

    CONFIG = (
                 'length', (100, 500),
                 'width', (1, 4),
                 'lanes', (1, 6),
                 'divider_width', (0.1, 0.5)
             )

    SUB_GENERATORS = {
                        'divider': Divider,
                     }

    def generate(self, config):
        C = config

        road_id = self.get_material('road', M(texture='textures/road_0.jpg'))

        line = draw.Line((C.width, 0, 0), (0, 0, 0))
        line = draw.Shape([line.unwrap()])
        road = line.extrude((0, C.length, 0))

        texture_size = 3.
        tx = C.width / texture_size
        ty = C.length / texture_size

        tcoords = [(tx, 0.0), (tx, ty), (0.0, ty), (0.0, 0.0)]
        road.set_material(road_id, texture_coords=tcoords)
        self.add_geom(road)

#        if C.lanes > 1:
#            divider_origin = (C.width/2-C.divider_width/2, 0, C.height)
#            self.subgen('divider', divider_origin, C.length, C.divider_width)


class MainRoad(BaseGenerator):

    CONFIG = (
                 'length', (100, 500),
                 'width', (1, 4),
                 'lanes', (1, 6),
                 'divider_width', (0.1, 0.5)
             )

    SUB_GENERATORS = {
                        'divider': Divider,
                        'bus': bus,
                     }

    def generate(self, config):
        C = config
        road_id = self.get_material('road', M(texture='textures/road_0.jpg'))

        line = draw.Line((C.width, 0, 0), (0, 0, 0))
        line = draw.Shape([line.unwrap()])
        road = line.extrude((0, C.length, 0))

        texture_size = 3.
        tx = C.width / texture_size
        ty = C.length / texture_size

        tcoords = [(tx, 0.0), (tx, ty), (0.0, ty), (0.0, 0.0)]
        road.set_material(road_id, texture_coords=tcoords)
#            road.visible = False
        self.add_geom(road)
        self.subgen('bus', ((0, 0, 0), (math.pi/2, (0, 0, 1))))

#            print 'before'
#            s_roads = self.get_intersection()
#            print 'after ', s_roads
#            if not s_roads:
#                road.visible = True

#        if C.lanes > 1:
#            divider_origin = (C.width/2-C.divider_width/2, 0, C.height)
#            self.subgen('divider', divider_origin, C.length, C.divider_width)

        
