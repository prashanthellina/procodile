'''
Represents a city.

G{importgraph}
'''

from procodile.procedural import ProceduralException, make_seed
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer, Range, Random
import procodile.geometry as geometry

from road import Model as RoadModel
from sector import GeneratorConfig as SectorConfig
from sector import Generator as SectorGenerator

class Model(BaseModel, BaseRenderer):
    '''
    City model.
    '''

    def __init__(self, length, height, roads, sectors):
        self.length = length
        self.height = height

        #: the main roads in a city
        self.roads = roads

        #: the sectors (or divisions) of the city
        # as formed by the main roads.
        self.sectors = sectors

    def _render_svg(self, origin):
        renderables = []

        x, y = origin
        point = (x + self.length, y + self.height)
        rect = geometry.AxisAligned2DRectangle(origin, point)
        svg.store_attributes(rect, fill='#eeeeee')

        renderables.append(rect)

        for (rx, ry), r in self.roads:
            rorigin = (rx + x, ry + y)
            renderables.extend(r.render('svg', rorigin))

        for (sx, sy), sector in self.sectors:
            sorigin = (sx + x, sy + y)
            renderables.extend(sector.render('svg', sorigin))

        return renderables

    def _render_x3d(self, xml_node):
       
        for origin, sector in self.sectors:
            transform = xml_node.Transform
            transform.translation = '%s %s %s' % origin
            
            sector.render('x3d', transform)

class GeneratorConfig(BaseGeneratorConfig):
    length = Range(1000, 5000)
    height = Range(1000, 5000)
    num_roads = Range(10, 20)

    road_width = 20
    min_gap_between_roads = 50

class Generator(BaseGenerator):

    def generate(self, seed, config, depth, region):
        pass
