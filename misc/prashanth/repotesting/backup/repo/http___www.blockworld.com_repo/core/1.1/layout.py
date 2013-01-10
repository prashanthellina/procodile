'''
Represents a layout (a part of a city sector).
A layout in a city sector is formed as an enclosure
formed by roads.

G{importgraph}
'''

from procodile.procedural import ProceduralException
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer, Range
from procodile.procedural import Random

class Model(BaseModel, BaseRenderer):
    '''
    City Sector Layout model.
    '''

    def __init__(self, length, height):
        self.length = length
        self.height = height    

class Generator(BaseGenerator):

    class CONFIG(BaseGeneratorConfig):
        length = Range(100, 500)
        width = Range(100, 500)

    def generate(self, seed, config, depth, region):
        R = Random(seed)

        length = R.generate(config.length)
        height = R.generate(config.height)

        layout = Model(length, height)

        return layout
