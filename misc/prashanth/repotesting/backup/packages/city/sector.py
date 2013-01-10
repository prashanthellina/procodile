'''
Represents a city sector.
A sector in a city is formed as an enclosure
formed by main roads.

G{importgraph}
'''

import procodile.geometry as geometry
from procodile.procedural import ProceduralException, make_seed
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer, Range
from procodile.procedural import Random

class Model(BaseModel, BaseRenderer):
    '''
    City Sector model.
    '''

    def __init__(self, length, height, roads, layouts):
        pass

class GeneratorConfig(BaseGeneratorConfig):
    length = Range(1000, 5000)
    height = Range(1000, 5000)

    num_roads = Range(10, 20)
    min_gap_between_roads = 10

    road_width = 10

class Generator(BaseGenerator):
    CONFIG = GeneratorConfig
    MODEL = Model

    def generate(self, seed, config, depth, region):
        pass
