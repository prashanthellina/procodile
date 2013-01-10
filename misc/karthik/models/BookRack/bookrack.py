#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 17, 2009 2:30:32 PM$"

from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw

class Rack(BaseGenerator):

    CONFIG = (
                'length', (1, 2),
                'width', (0.3, 0.5),
                'height', (1, 2),
             )

    SUB_GENERATORS = {
#                        'book':None,
                     }

    def generate(self, config):
        C = config

        rack = draw.makeBox(C.length, C.width, C.height)
        rack.visible = False
        self.add_geom(rack)

        ps = self.get_enclosing()
        geoms = ps.get_geoms(tag='shelf')

        for geom in geoms:
            new_geom = geom.cut(rack)
            self.replace_geom(geom,new_geom)

class BookRack(BaseGenerator):

    CONFIG = (
                'length', (1, 2),
                'width', (0.3, 0.5),
                'height', (1, 2),
             )

    SUB_GENERATORS = {
                        'rack':Rack,
                     }
   
    def generate(self, config):
        C = config
        
        shelf = draw.makeBox(C.length, C.width, C.height)
        shelf.tags.append('shelf')
        
#        wood_id = self.get_material('wood', M(texture='BookRack/vikraman.jpg'))
#        shelf.set_material(wood_id, texture_coords=[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])

        self.add_geom(shelf)
        
        self.subgen('rack', (C.length/2, 0, C.height/2), C.length/4., C.width/2, C.height/2.)
