'''
Represents a Tree.

G{importgraph}
'''

from procodile.procedural import ProceduralException, make_seed
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer, Range, Random
from procodile.repository.client.utils import Repository
import procodile.geometry as geometry

class Model(BaseModel, BaseRenderer):
    '''
    Tree model.
    '''

    def __init__(self):
        pass

class GeneratorConfig(BaseGeneratorConfig):
    length = Range(1000, 5000)
    height = Range(1000, 5000)

class Generator(BaseGenerator):
    
    CONFIG = GeneratorConfig
    MODEL = Model
    SUB_GENERATORS = {}

    def generate(self, seed, config, depth, region):
        pass
