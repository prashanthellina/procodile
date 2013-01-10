'''
Represents a city.

G{importgraph}
'''

from procodile.procedural import ProceduralException, make_seed
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer, Range, Random
from procodile.repository.client.utils import get_class
import procodile.geometry as geometry

from sector import GeneratorConfig as SectorConfig
from sector import Generator as SectorGenerator, Model as SectorModel

repo = 'http://localhost:9000'
TreeGenerator = get_class(repo, 'karthik.nature.tree.Generator', '0.2')

class Model(BaseModel, BaseRenderer):
    '''
    City model.
    '''

    def __init__(self, length, height, roads, sectors):
        pass

class GeneratorConfig(BaseGeneratorConfig):
    length = Range(1000, 5000)
    height = Range(1000, 5000)
    num_roads = Range(10, 20)

    road_width = 20
    min_gap_between_roads = 50

class Generator(SectorGenerator):
    
    CONFIG = GeneratorConfig
    MODEL = Model
    SUB_GENERATORS = {'sector': SectorGenerator,
                      'tree': TreeGenerator}

    def generate(self, seed, config, depth, region):
        pass
