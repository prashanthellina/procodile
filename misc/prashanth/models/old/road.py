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
        
def make_roads(length, height, road_width, num_roads, min_gap, rnd_gen):

    R = rnd_gen
    half_width = road_width / 2.

    road_data = []
    hroads = [0, height]
    vroads = [0, length]

    for i in xrange(num_roads):
        if R.decision():
            road_length, roads, orientation = length, hroads, 'horizontal'

        else:
            road_length, roads, orientation = height, vroads, 'vertical'

        insert_at = R.generate(Range(0, len(roads) - 2))
        min_offset = roads[insert_at]
        max_offset = roads[insert_at + 1]

        min_offset = min_offset + min_gap
        max_offset = max_offset - min_gap

        if max_offset < min_offset:
            continue

        road_offset = R.generate(Range(min_offset, max_offset))
        roads.append(road_offset)
    
        if orientation == 'horizontal':
            origin = (0, road_offset - half_width)

        else:
            origin = (road_offset - half_width, 0)

        road_data.append((origin, road_length, road_width, orientation))

        roads.sort()
   
    spaces = []
    hroads.reverse()

    for x in range(len(vroads) - 1):
        for y in range(len(hroads) - 1):
            x1, y1 = vroads[x], hroads[y]
            x2, y2 = vroads[x + 1], hroads[y + 1]

            x1, y1 = x1 + half_width, y1 - half_width
            x2, y2 = x2 - half_width, y2 + half_width

            slength = abs(x2 - x1)
            sheight = abs(y1 - y2)

            spaces.append(((x1, y2), (slength, sheight)))

    return road_data, spaces
