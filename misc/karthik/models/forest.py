#! /usr/bin/python

from procodile.procedural import BaseGenerator
import procodile.draw as draw

from tree.normal import Tree

class Forest(BaseGenerator):

    CONFIG = (
                'length', (10, 20),
                'width', (10, 20),
                'density', (.05, .01)
             )

    SUB_GENERATORS = {
                        'tree': Tree
                     }

    def generate(self, config):
        C = config

        area = C.length * C.width
        num = int(C.density * area)
        print area, num

        for i in xrange(num):
            x = self.picker.pick((0, C.length))
            y = self.picker.pick((0, C.width))
            self.subgen('tree', (x, y, 0))
