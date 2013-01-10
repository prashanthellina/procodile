# -*- coding: utf-8 -*-
'''
Building Level model and generator.

G{importgraph}
'''

import procodile.draw as draw
import procodile.geometry as geometry
from procodile.procedural import BaseGenerator
from flat import Generator as FlatGenerator
from door import Generator as DoorGenerator
import math


class Generator(BaseGenerator):

    CONFIG = (
              'length', (10, 100),
              'width', (10, 100),
              'height', (3, 5),
              'inner_wall_thickness', (.1, .3),
              'outer_wall_thickness', (.2, .4),
              'corridor_length', (2, 3),
              'corridor_width', (2, 3),
              'door_width', 1,
              'door_height', 2
              )

    SUB_GENERATORS = {
                        'flat': FlatGenerator,
                        'door': DoorGenerator
                     }

    def generate(self, config):
        
        C = config
        level_rect = ((0, 0), (int(C.length), int(C.width)))
        level_rect = geometry.AxisAligned2DRectangle(*level_rect)
        if C.length < 1 or C.width < 1:
            return
        corridor_length = int(C.length / 5)
        corridor_width = int(C.width / 5)
        corridor_length = 1 if corridor_length == 0 else corridor_length
        corridor_width = 1 if corridor_width == 0 else corridor_width
        
        if C.length < corridor_length or C.width < corridor_width:
            raise Exception, "corridor length, width should be less than that of level"

        cx = int(C.length / 2 - corridor_length / 2)
        cy = int(C.width / 2 - corridor_width / 2)
        corridor_rect = ((cx, cy), (cx + corridor_length,
                         cy + corridor_width))

        corridor_rect = geometry.AxisAligned2DRectangle(*corridor_rect)     
       
        apartments = divide_into_apartments(self.picker, level_rect, corridor_rect)

        for flat in apartments:
            (x1, y1), (x2, y2) = flat
            flat_length = abs(x2 - x1)
            flat_width = abs(y2 - y1)
            thickness = C.inner_wall_thickness
            p = draw.makePlane(flat_length, flat_width)
            p1 = draw.makePlane(flat_length-thickness * 2,
                                flat_width-thickness * 2,
                                (thickness, thickness, 0))

            p = p.cut(p1)
            p = p.Faces[0]

            p = draw._wrap_value(p)
            p = p.extrude((0, 0, C.height))

            origin = (x1, y1, 0)

            p.translate(origin)
            p.tags.append('wall')
            self.add_geom(p)

        self.make_doors(corridor_rect, C)

        for flat in apartments:
            self.make_flats(flat, C)


    def make_doors(self, corridor_rect, C):
        corridor_walls = corridor_rect.get_lines()
        corridor_points = [corridor_rect.point1, corridor_rect.point2]
        corridor_points.sort()
        (x1, y1), (x2, y2) = corridor_points
        for wall in corridor_walls:
            wall_points = [wall.point1, wall.point2]
            wall_points.sort()
            p1, p2 = wall_points
            if wall.is_horizontal():
                c = (p2[0]-p1[0]) / 2
                center = (p1[0] + c, p1[1])
                if p1[1]==y1:
                    xdoor_origin = (center[0]-C.door_width/2, center[1]-C.inner_wall_thickness, 0)
                else:
                    xdoor_origin = (center[0]-C.door_width/2, center[1], 0)
                

                self.subgen('door', xdoor_origin,
                            width=C.door_width,
                            height=C.door_height)
            else:
                c = (p2[1]-p1[1]) / 2
                center = (p1[0], p1[1] + c)
                ydoor_origin = (center[0], center[1]-C.door_width/2, 0)
                if p1[0]==x1:
                    location = (ydoor_origin, (math.pi / 2, (0, 0, 1)))
                else:
                    location = (ydoor_origin, (-math.pi / 2, (0, 0, 1)))

                self.subgen('door', location,
                            width=C.door_width,
                            height=C.door_height)

    def make_flats(self, flat, C):

        (x1, y1), (x2, y2) = flat
        origin = (x1, y1, 0)
        flat_length = abs(x2 - x1)
        flat_width = abs(y2 - y1)
        thickness = C.inner_wall_thickness
        flat_rect = ((round(x1-thickness), round(y1-thickness)), (round(x2-thickness), round(y2-thickness)))

        flat_rect = geometry.AxisAligned2DRectangle(*flat_rect)

        self.subgen('flat', origin,
                    length=flat_length,
                    width=flat_width,
                    height=C.height,
                    inner_wall_thickness=thickness,
                    outer_wall_thickness=C.outer_wall_thickness)

def divide_into_apartments(P, level, corridor):
    common, splits = geometry.split_overlapping_rectangles(level, corridor)
    center_rects = [split for split in splits if common.is_touching(split)]

    corner_rects = list(set(splits).difference(set(center_rects)))

    corner_center_map = {}

    for corner in corner_rects:
        for center in center_rects:
            if corner.is_touching(center):
                corner_center_map.setdefault(corner,[]).append(center)

    lumps ={}
    for center in center_rects:
        lumps.setdefault(center,[])

    for corner, centers in corner_center_map.iteritems():
        center = P.pick(centers)
        lumps[center].append(corner)


    rm = geometry.RectangleMerger()
    apartments = []
    for center, lump in lumps.iteritems():
        lump.append(center)
        polys = rm.merge(lump)
        ortho_poly = polys[0]
        data = ortho_poly.SplitData(ortho_poly)
        apartment = ortho_poly._get_rectangles(data).pop()
        apartments.append(((apartment.min_x(),apartment.min_y()),(apartment.max_x(),apartment.max_y())))

    return apartments