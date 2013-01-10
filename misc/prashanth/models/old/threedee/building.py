'''
Building model and generator.

G{importgraph}
'''

from procodile.procedural import BaseGenerator
import procodile.draw as draw

from level import Generator as LevelGenerator

class Generator(BaseGenerator):
        
    CONFIG = (
                'length', (10, 100),
                'width', (10, 100),
                'num_levels', (1, 100),
                'height', (10, 500),
                'slab_height', (0.1, 0.3),
                'level_height', (3, 5),
                'corridor_length', (6, 8),
                'corridor_width', (6, 8),
                'wall_thickness', (.1, .3),
             )

    SUB_GENERATORS = {
                        'level': LevelGenerator
                     }

    def generate(self, config):
       
        C = config

        num_levels, slab_height, level_height = \
            self.compute_height_params(self.picker,
                                       C.height,
                                       C.slab_height,
                                       C.level_height,
                                       C.num_levels)

        for i in xrange(num_levels + 1):
            zoffset = (slab_height + level_height) * i
            slab = draw.makeBox(C.length, C.width, slab_height)
            origin = (0, 0, zoffset)
            slab.translate(origin)
            self.add_geom(slab)

        for i in xrange(num_levels):
            zoffset = slab_height + \
                        (slab_height + level_height) * i
            origin = (0, 0, zoffset)

            self.subgen('level', origin,
                        C.length, C.width, level_height, None,
                        C.wall_thickness, C.corridor_length,
                        C.corridor_width)

    def compute_height_params(self, P, height, slab_height,
                                level_height, num_levels):
        if height and num_levels:
            raise Exception('please specify height or num_levels')

        if height:
            num_levels = height / (slab_height + level_height)
         
        return num_levels, slab_height, level_height
