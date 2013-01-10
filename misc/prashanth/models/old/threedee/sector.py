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

from procodile.models.threedee.road import Model as RoadModel, make_roads
from procodile.models.threedee.layout import GeneratorConfig as LayoutConfig
from procodile.models.threedee.layout import Generator as LayoutGenerator

class Model(BaseModel, BaseRenderer):
    '''
    City Sector model.
    '''

    def __init__(self, length, height, roads, layouts):
        self.length = length
        self.height = height

        #: the roads inside this sector
        self.roads = roads

        #: the layouts of a sector as formed
        # by the roads
        self.layouts = layouts

    def _render_svg(self, origin):
        renderables = []

        x, y = origin
        point = (x + self.length, y + self.height)
        rect = geometry.AxisAligned2DRectangle(origin, point)
        svg.store_attributes(rect, fill='#dddddd')

        renderables.append(rect)

        for (rx, ry), r in self.roads:
            rorigin = (rx + x, ry + y)
            renderables.extend(r.render('svg', rorigin))

        for (sx, sy), layout in self.layouts:
            sorigin = (sx + x, sy + y)
            renderables.extend(layout.render('svg', sorigin))

        return renderables

    def _render_x3d(self, xml_node):
       
        for origin, layout in self.layouts:
            transform = xml_node.Transform
            transform.translation = '%s %s %s' % origin
            
            layout.render('x3d', transform)

class GeneratorConfig(BaseGeneratorConfig):
    length = Range(1000, 5000)
    height = Range(1000, 5000)

    num_roads = Range(10, 20)
    min_gap_between_roads = 10

    road_width = 10

class Generator(BaseGenerator):

    def generate(self, seed, config, depth, region):
        R = Random(seed)

        length = R.generate(config.length)
        height = R.generate(config.height)
        num_roads = R.generate(config.num_roads)
        min_gap = config.min_gap_between_roads

        road_data, spaces = make_roads(length, height, config.road_width,
                                       num_roads, min_gap, R)

        road_models = []
        for origin, road_length, config.road_width, orientation in road_data:
            road = RoadModel(road_length, config.road_width, orientation)
            road_models.append((origin, road))
        #print 'sub-roads: ', len(road_models)

        layouts = []
        lgen = LayoutGenerator()

        for index, (origin, (llength, lheight)) in enumerate(spaces):
            lseed = make_seed(seed, index)
            lconfig = LayoutConfig()
            lconfig.length = llength
            lconfig.height = lheight
            layout = lgen.generate(lseed, lconfig, depth, region)
            x, y = origin
            origin = x, 0, -y
            layouts.append((origin, layout))

        sector = Model(length, height, road_models, layouts)
        return sector
