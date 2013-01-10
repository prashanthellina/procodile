# -*- coding: utf-8 -*-
'''
Building Window model and generator.

G{importgraph}
'''


from procodile.procedural import BaseGenerator
from procodile import draw



class Generator(BaseGenerator):

    CONFIG = (
              'width', (1, 3),
              'thickness', (.1, .3),
              'height', (2, 5),
              )

    SUB_GENERATORS = {
                     }

    def generate(self, config):        
        C = config

        door = draw.makeBox(C.width, C.thickness*2, C.height)
        door.visible = False
        door.tags.append('door')
        self.add_geom(door)
        ps = self.get_enclosing()
        geoms = ps.get_geoms(tag='wall')
        for geom in geoms:
            new_geom = geom.cut(door)
            self.replace_geom(geom,new_geom)

        


