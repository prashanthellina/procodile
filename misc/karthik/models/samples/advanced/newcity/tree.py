#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 17, 2009 2:30:32 PM$"

from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw
import math

class Tree(BaseGenerator):

    CONFIG = (
                'diameter', (0.05, 0.5),
                'height', (0.5, 5),
                'trunk_diameter', (0.1, 0.5),
             )
   
    def generate(self, config):

        C = config
        grass_id = self.get_material('grass', M(texture='textures/grass.jpg'))
        bark_id = self.get_material('bark', M(texture='textures/bark.jpg'))

        trunk = draw.makeBox(C.diameter/4., C.diameter/4., C.height)
        trunk.set_material(bark_id)
        self.add_geom(trunk)

        length = C.diameter
        pnt = (-length/2., -length/2., C.height)
        top = draw.makeBox(length, length, length, pnt)
        x = self.picker.pick((1.0))
        top.set_material(grass_id, texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)])
        self.add_geom(top)


class PineTree(BaseGenerator):

    CONFIG = (
                 'height', (0.5, 5),
                 'width', (0.3, 2),
                 'top_ratio', (0.6, 0.9),
                 'trunk_ratio', (0.1, 0.4),
                 'trunk_diameter', (0.05, 0.5)
             )

    def make_plate(self, height, width, lift_height, rotation=0):
        line = draw.Line((0, 0, 0), (width, 0, 0))
        line = draw.Shape([line.unwrap()])
        face = line.extrude((0, 0, height))

        t = draw.Matrix()
        t.move((-width/2., 0, 0))
        t.move((0, 0, lift_height))
        face = face.transform(t)

        t = draw.Matrix()
        t.rotateZ(math.pi)
        other_face = face.transform(t)

        t = draw.Matrix()
        t.rotateZ(rotation)
        face = face.transform(t)
        other_face = other_face.transform(t)

        face.set_material(self.leaves_id)
        other_face.set_material(self.leaves_id)

        return face, other_face

    def generate(self, config):

        C = config
        self.leaves_id = self.get_material('leaves', M(texture='tree\\pine_tree.png'))
        bark_id = self.get_material('bark', M(texture='tree\\bark.jpg'))

        if C.top_ratio + C.trunk_ratio < 1.0:
            C.trunk_ratio = 1.0 - C.top_ratio

        trunk_height = C.height * C.trunk_ratio
        dia = C.trunk_diameter
        trunk = draw.makeBox(dia, dia, trunk_height)
        trunk.set_material(bark_id)
        trunk.translate((-dia/2., -dia/2., 0))
        self.add_geom(trunk)

        top_height = C.height * C.top_ratio
        lift_height = C.height - top_height
        for rotation in (0, math.pi/2, math.pi/4, -math.pi/4):
            rotation += .01
            plate = self.make_plate(top_height, C.width, lift_height, rotation)
            self.add_geoms(*plate)
