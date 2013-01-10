#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 17, 2009 10:07:49 AM$"

from procodile.procedural import BaseGenerator
from procodile.buildspace import Location
import procodile.draw as draw
import math

class Tree(BaseGenerator):

    CONFIG = (
                 'height', (.1, 5),
                 'diameter', (0.05, 0.5),
                 'branches', (10, 20),
                 'depth', 4
             )

    SUB_GENERATORS = {
                        'tree':None
                     }

    def generate(self, config):

        C = config
        if C.depth <= 0:
            return

        trunk = draw.makeCylinder(C.diameter/2,C.height)
        self.add_geom(trunk)

        for i in xrange(C.branches):

            if i == 0:
                at_height = C.height
            else:
                at_height = C.height * self.picker.pick((0.5, 0.75))

            location = Location()

            y_rotation = self.picker.pick((-math.pi/2, math.pi/2))
            z_rotation = self.picker.pick((-math.pi/2, math.pi/2))

            location.translate((0, 0, at_height))
            location.rotate((z_rotation, (0, 0, 1)))
            location.rotate((y_rotation, (0, 1, 0)))

            height = C.height * self.picker.pick((0.25, 0.75))
            diameter = C.diameter * self.picker.pick((0.25, 0.75))

            self.subgen('tree', location, diameter = diameter,
                        depth = C.depth-1, height = height)

Tree.SUB_GENERATORS['tree'] = Tree
