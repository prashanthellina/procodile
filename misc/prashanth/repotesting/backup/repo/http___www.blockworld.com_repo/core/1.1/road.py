'''
Represents a road.

G{importgraph}
'''

from procodile.procedural import ProceduralException
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer, Range
import procodile.svg as svg
import procodile.geometry as geometry

class Model(BaseModel, BaseRenderer):
    '''
    Road model.
    '''

    def __init__(self, length, width, orientation):
        #: the road is a straight line
        self.length = length

        #: the wideness of the road
        self.width = width

        #: horizontal/vertical
        self.orientation = orientation

    def _render_svg(self, origin):

        x, y = origin
        if self.orientation == 'horizontal':
            p2 = (x + self.length, y + self.width)
        else:
            p2 = (x + self.width, y + self.length)

        rect = geometry.AxisAligned2DRectangle(origin, p2)
        svg.store_attributes(rect, stroke_width=0, fill="black")
        
        return [rect]

class GeneratorConfig(BaseGeneratorConfig):
    def __init__(self):
        pass

class Generator(BaseGenerator):
    def __init__(self):
        pass
        

