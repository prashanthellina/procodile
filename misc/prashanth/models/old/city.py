'''
Represents a city.

G{importgraph}
'''

from procodile.procedural import ProceduralException, make_seed
from procodile.procedural import BaseGenerator, BaseGeneratorConfig
from procodile.procedural import BaseModel, BaseRenderer, Range, Random
import procodile.svg as svg
import procodile.geometry as geometry
from procodile.renderers import SVGRenderer

from procodile.models.road import Model as RoadModel, make_roads
from procodile.models.sector import GeneratorConfig as SectorConfig
from procodile.models.sector import Generator as SectorGenerator

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

class GeneratorConfig(BaseGeneratorConfig):
    length = Range(10000, 50000)
    height = Range(10000, 50000)
    num_roads = Range(10, 20)

    road_width = 20
    min_gap_between_roads = 250

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
        for origin, road_length, road_width, orientation in road_data:
            road = RoadModel(road_length, road_width, orientation)
            road_models.append((origin, road))

        sectors = []
        sgen = SectorGenerator()

        for index, (origin, (slength, sheight)) in enumerate(spaces):
            sseed = make_seed(seed, index)
            sconfig = SectorConfig()
            sconfig.length = slength
            sconfig.height = sheight
            sector = sgen.generate(sseed, sconfig, depth, region)
            sectors.append((origin, sector))

        city = Model(length, height, road_models, sectors)
        return city
