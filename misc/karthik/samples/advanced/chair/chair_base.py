#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 3, 2009 12:51:08 PM$"

from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw
import math

class ChairBase(BaseGenerator):
    CONFIG = (
                 'width', (0.3, 1.0),
                 'base_length', (0.2, 4),
                 'base_thickness', (0.02, 0.1)
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):

        base = draw.makeBox(config.width, config.base_length, config.base_thickness)
        x = self.picker.pick((1.0))
        wood_id = self.get_material('grass', M(texture='bark.jpg'))
        base.set_material(wood_id, texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)])
        self.add_geoms(base)

class RoundBase(ChairBase):

    def generate(self, config):
        
        base = draw.makeCylinder(config.width/2,
                                 config.base_thickness,
                                 (config.width/2,config.width/2,0))
        x = self.picker.pick((1.0))
        wood_id = self.get_material('grass', M(texture='bark.jpg'))
        base.set_material(wood_id, texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)])
        self.add_geoms(base)

class FlowerBase(ChairBase):

    CONFIG = (
                 'width', (0.3, 1.0),
                 'base_length', (0.2, 4),
                 'base_thickness', (0.02, 0.1),
                 'cover_area', (0.02, 0.1)
             )

    def generate(self, config):
        
        base = draw.makeBox(config.width, config.base_length, config.base_thickness)
        smaller = config.width if config.width < config.base_length else config.base_length
        center_radius = smaller/10
        vertical_center = (config.base_length-config.cover_area)/2
        center = (config.width/2,vertical_center,0)
        cylinder = draw.makeCylinder(center_radius,
                                     config.base_thickness,
                                     center)
        base = base.cut(cylinder)

        ell_majorradius = smaller/10
        ell_minorradius = smaller/20
        e1 = (config.width/2+center_radius+ell_majorradius,vertical_center,0)
        eli = draw.Ellipse((0,0,0),ell_majorradius,ell_minorradius)
        ellipse = eli.toShape()
        ellipse_face = draw.Face(draw.Wire(ellipse.Edges))
        ellipse = ellipse_face.extrude((0,0,config.base_thickness))
        ellipse1 = ellipse.copy()

        ellipse1.translate(e1)
        base = base.cut(ellipse1)

        e2 = (config.width/2-center_radius-ell_majorradius,vertical_center,0)
        ellipse2 = ellipse.copy()        
        ellipse2.translate(e2)        
        base = base.cut(ellipse2)

        e3 = (config.width/2,vertical_center + center_radius + ell_majorradius, 0)
        ellipse3 = ellipse.copy()
        aTrsf=draw.Matrix()
        aTrsf.rotateZ(math.pi/2) # rotate around the z-axis
        ellipse3=ellipse3.transform(aTrsf)
        ellipse3.translate(e3)
        base = base.cut(ellipse3)

        e4 = (config.width/2,vertical_center - center_radius - ell_majorradius, 0)
        ellipse4 = ellipse.copy()
        ellipse4=ellipse4.transform(aTrsf)
        ellipse4.translate(e4)
        base = base.cut(ellipse4)

        x = self.picker.pick((1.0))
        wood_id = self.get_material('grass', M(texture='bark.jpg'))
        base.set_material(wood_id, texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)])
        self.add_geoms(base)
