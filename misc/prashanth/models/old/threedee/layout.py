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

    def _render_svg(self):
        pass

    def _render_x3d(self, xml_node):
        import random
        r, g, b = random.random(), random.random(), random.random()

        length = self.length
        height = self.height
        count = 0

        factor = 50
        
        transform = xml_node.Transform
        tx, tz = length / 2., -height / 2.
        transform.attrs = {'translation': '%s %s %s' % (tx, 0, tz)}

        sub_transform = transform
        while length > factor and height > factor:
            shape = sub_transform.Shape
            shape.Box.size = '%s %s %s' % (length, factor, height)
            shape.Appearance.Material.attrs = {'diffuseColor': '%s %s %s' % (r, g, b),
                'transparency': '0.1'}

            length -= factor
            height -= factor
            count += 1
            
            sub_transform = sub_transform.Transform
            q_factor = factor / 4.
            sub_transform.attrs = {'translation': '%s %s %s' % (q_factor, factor, -q_factor)}

class GeneratorConfig(BaseGeneratorConfig):
    length = Range(20, 100)
    height = Range(20, 100)

class Generator(BaseGenerator):
    def generate(self, seed, config, depth, region):
        R = Random(seed)

        length = R.generate(config.length)
        height = R.generate(config.height)

        layout = Model(length, height)

        return layout
