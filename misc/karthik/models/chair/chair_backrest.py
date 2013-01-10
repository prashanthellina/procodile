#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 3, 2009 1:58:49 PM$"

from procodile.procedural import BaseGenerator
import procodile.draw as draw

class ChairBackRest(BaseGenerator):
    CONFIG = (
                 'width', (0.3, 1.0),
                 'back_rest_thickness', (0.02, 0.1),
                 'back_rest_height', (0.0, 1.0)
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):

        back_rest = draw.makeBox(config.width,
                                 config.back_rest_thickness,
                                 config.back_rest_height)

        self.add_geoms(back_rest)

class BarBackRest(ChairBackRest):

    CONFIG = (
                 'width', (0.3, 1.0),
                 'back_rest_thickness', (0.02, 0.1),
                 'back_rest_height', (0.0, 1.0),
                 'no_of_holes', (5,20)
             )

    def generate(self, config):

        back_rest = draw.makeBox(config.width,
                                 config.back_rest_thickness,
                                 config.back_rest_height)

        no_of_portions = 2. * config.no_of_holes + 1
        bar_width = config.width/no_of_portions
        bar_height = config.back_rest_height - (config.back_rest_height/10) * 2

        x = 0

        for i in range(no_of_portions):
            if i%2 != 0:
                bar_origin = (x,0,config.back_rest_height/10)
                bar = draw.makeBox(bar_width,
                               config.back_rest_thickness,
                               bar_height,bar_origin)
                back_rest = back_rest.cut(bar)
            x = x+bar_width
        self.add_geoms(back_rest)
