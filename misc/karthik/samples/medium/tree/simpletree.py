from procodile.procedural import BaseGenerator
import procodile.draw as draw

class CubeTreeTopGenerator(BaseGenerator):
    CONFIG = (
                'length', (0.5, 5),
             )

    def generate(self, config):

        length = config.length
        halflen = length / 2.
        top = draw.makeBox(length, length, length, (-halflen, -halflen, 0))
        self.add_geom(top)

class TorusTreeTopGenerator(BaseGenerator):
    CONFIG = (
                'length', (0.5, 5),
             )

    def generate(self, config):

        halflen = config.length / 2.
        top = draw.makeTorus(halflen, halflen - .05)
        self.add_geom(top)

class SimpleTree(BaseGenerator):
    CONFIG = (
                'trunk_width', (0.05, 0.5),
                'height', (0.5, 5),
                'top_size', (1, 5),
             )

    SUB_GENERATORS = ('cube_top', CubeTreeTopGenerator,
                      'torus_top', TorusTreeTopGenerator)

    def generate(self, config):

        C = config
        twidth = C.trunk_width
        halfwidth = twidth / 2.
        trunk = draw.makeBox(twidth, twidth, C.height, (-halfwidth, -halfwidth, 0))
        self.add_geom(trunk)

        self.subgen('cube_top', (0, 0, config.height), config.top_size)