'''
Represents a layout (a part of a city sector).
A layout in a city sector is formed as an enclosure
formed by roads.

G{importgraph}
'''

from procodile.procedural import ProceduralException
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer, Range
import procodile.svg as svg

class Model(BaseModel, BaseRenderer):
    '''
    City Sector Layout model.
    '''

    def __init__(self, plots):
        #: the area of the layout is divided
        # into rectangular regions called plots.
        # A plot can be a building/park/play area.
        self.plots = plots

    def _render_svg(self):
        pass

class GeneratorConfig(BaseGeneratorConfig):
    layout_width = Range(
    plot_width = 20
    plot_length = Range(20, 100)

class Generator(BaseGenerator):
    def generate(self, seed, config, depth, region):
        R = Random(seed)

        return sector
