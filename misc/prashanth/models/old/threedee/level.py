'''
Building Level model and generator.

G{importgraph}
'''

from procodile.procedural import BaseGenerator
import procodile.geometry as geometry
import procodile.draw as draw


class Generator(BaseGenerator):
    CONFIG = (
                'length', (10, 100),
                'width', (10, 100),
                'height', (3, 5),
                'inner_wall_thickness', (.1, .3),
                'outer_wall_thickness', (.2, .4),
                'corridor_length', (6, 8),
                'corridor_width', (6, 8),
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):
        
        C = config

        level_rect = ((0, 0), (C.length, C.width))
        level_rect = geometry.AxisAligned2DRectangle(*level_rect)

        cx = C.length / 2 - C.corridor_length / 2
        cy = C.width / 2 - C.corridor_width / 2
        corridor_rect = ((cx, cy), (cx + C.corridor_length,
                                    cy + C.corridor_width))
        corridor_rect = geometry.AxisAligned2DRectangle(*corridor_rect)

        apartments = divide_into_apartments(
                        self.picker, level_rect, corridor_rect)

        for apartment in apartments:
            (x1, y1), (x2, y2) = apartment

            length = abs(x2 - x1)
            width = abs(y2 - y1)

            if not length or not width:
                continue

            p = draw.makePlane(length, width)
            p = p.Wires[0]
            p = draw._wrap_value(p)
            p = p.extrude((0, 0, C.height))

            origin = (x1, y1, 0)
            self.add_geom(p)

def divide_into_apartments(P, level, corridor):
    coords = []

    xvalues = [level.min_x(), corridor.min_x(),
               corridor.max_x(), level.max_x()]
    yvalues = [level.max_y(), corridor.max_y(),
               corridor.min_y(), level.min_y()]

    for yindex, y in enumerate(yvalues[:-1]):
        cur_row = []

        for xindex, x in enumerate(xvalues[:-1]):
            x1 = x
            y1 = y
            x2 = xvalues[xindex + 1]
            y2 = yvalues[yindex + 1]
            cur_row.append(((x1, y1), (x2, y2)))

        coords.append(cur_row)

    get = lambda r,c: coords[r][c]

    corners = {
                (0, 0): [(0, 1), (1, 0)],
                (2, 0): [(1, 0), (2, 1)],
                (0, 2): [(0, 1), (1, 2)],
                (2, 2): [(2, 1), (1, 2)],
              }

    clumps = {
                (0, 1): [get(0,1)],
                (1, 0): [get(1, 0)],
                (1, 2): [get(1, 2)],
                (2, 1): [get(2, 1)],
             }

    for corner, centers in corners.iteritems():
        center = P.pick(centers)
        clumps[center].append(get(*corner))

    apartments = []
    clumps = clumps.values()
    for clump in clumps:
        clump.sort()
        (a1, a2), (b1, b2) = clump[0], clump[-1]
        apartment = (a1, b2)
        apartments.append(apartment)

    return apartments
