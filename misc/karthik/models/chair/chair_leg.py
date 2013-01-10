#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 1, 2009 3:52:52 PM$"

from procodile.procedural import BaseGenerator
import procodile.draw as draw

class ChairLeg(BaseGenerator):
    CONFIG = (
                 'leg_height', (0.1, 1),
                 'leg_thickness', (0.01, 0.1),
                 'type',['square', 'cylinder', 'triangular']
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):
        if config.type == 'square':
            leg = draw.makeBox(config.leg_thickness,
                               config.leg_thickness,
                               config.leg_height)

        elif config.type == 'cylinder':
            origin = (config.leg_thickness/2,config.leg_thickness/2,0)
            leg = draw.makeCylinder(config.leg_thickness/2,
                                    config.leg_height, origin)

        elif config.type == 'triangular':
            leg = draw.makePolygon([(config.leg_thickness,0,0),(0,config.leg_thickness,0),(0,0,0)])
            leg = leg.extrude((0,0,config.leg_height))

        self.add_geoms(leg)

class CylispheLeg(ChairLeg):
    CONFIG = (
                 'leg_height', (0.1, 1),
                 'leg_thickness', (0.01, 0.1)
             )

    SUB_GENERATORS = {
                        'leg': ChairLeg
                     }

    def generate(self, config):

        cylinder_height = (config.leg_height-config.leg_thickness*2)/2
        base_cylinder = draw.makeCylinder(config.leg_thickness/2,
                                    cylinder_height)

        current_height = cylinder_height + config.leg_thickness/2
        base_sphere = draw.makeSphere(config.leg_thickness/2,
                                      (0,0,current_height))

        current_height = current_height + config.leg_thickness/2
        top_cylinder = draw.makeCylinder(config.leg_thickness/2,
                                         cylinder_height,(0,0,current_height))

        current_height = current_height + cylinder_height \
                                        + config.leg_thickness/2
        top_sphere = draw.makeSphere(config.leg_thickness/2,
                                      (0,0,current_height))

#        leg = draw.makeCompound([base_cylinder, base_sphere, top_cylinder, top_sphere])
#        leg.translate((config.leg_thickness/2,config.leg_thickness/2,0))

        base_cylinder.translate((config.leg_thickness/2,config.leg_thickness/2,0))
        base_sphere.translate((config.leg_thickness/2,config.leg_thickness/2,0))
        top_cylinder.translate((config.leg_thickness/2,config.leg_thickness/2,0))
        top_sphere.translate((config.leg_thickness/2,config.leg_thickness/2,0))

        self.add_geoms([base_cylinder, base_sphere, top_cylinder, top_sphere])

