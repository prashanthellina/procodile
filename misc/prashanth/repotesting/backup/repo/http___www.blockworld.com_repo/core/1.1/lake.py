'''
Represents a lake.

G{importgraph}
'''

from procodile.procedural import ProceduralException
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer
from procodile.procedural import Random

import procodile.svg as svg
import procodile.geometry as geometry

class Model(BaseModel, BaseRenderer):
    '''
    Lake model.
    '''

    def __init__(self, length, height):
        self.length = length
        self.height = height

    def _render_svg(self):
        x1, y1 = 0, 0
        x2, y2 = x1 + self.length, y1 + self.height

        r = geometry.AxisAligned2DRectangle((x1, y1), (x2, y2))
        return [r]

class GeneratorConfig(BaseGeneratorConfig):
    min_radius = 10
    max_radius = 50

class Generator(BaseGenerator):

    def generate(self, seed, config, depth, region):
        R = Random(seed)
        radius = R.random(config.min_radius, config.max_radius)

        model = Model(radius)
        return model

        
