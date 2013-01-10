#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 10, 2009 1:11:52 PM$"

from procodile.procedural import BaseGenerator
from building import LBuildings
from building import Base
from tree import Tree

class RuralPlot(BaseGenerator):

    CONFIG = (
                 'length', (1000, 5000),
                 'width', (1000, 5000),
                 'build_height_range', None,
             )

    SUB_GENERATORS = {
                        'building': LBuildings,
                        'base': Base,
                        'tree': Tree
                     }

    def pick_height(self, _range):
        _range = _range[:]

        total = 0.0
        for index, (probability, cur_range) in enumerate(_range):
            total = total + probability
            _range[index] = (total, cur_range)

        choice = self.picker.pick((0.0, 1.0))
        for index, (probability, cur_range) in enumerate(_range):
            if probability > choice:
                return self.picker.pick(cur_range)

        return self.picker.pick(_range[-1][-1])

    def generate(self, config):
        C = config

        self.subgen('base', (0, 0, 0), C.length, C.width)
        
        building_height = self.pick_height(C.build_height_range)

        self.subgen('base', (0, 0, 0), C.length, C.width)
        if building_height == 0:
            return

        self.subgen('building', (0+1, 0+1, 0.2), C.length-2, C.width-2,
                    height=building_height)
