from geometry import *
from pprint import *
import svgfig
import random

#p = OrthogonalPolygon(((0, 0), (1, 0), (1, -1), (2, -1), (2, 0), (3, 0), (3, 1), (0, 1)))
#rectangles = p.split()
#pprint(rectangles)

#m = RectangleMerger()
#polygons = m.merge(rectangles)
#pprint(polygons)

#p = OrthogonalPolygon(((0, 0), (1, 0), (1, -1), (2, -1), (2, -2), (3, -2), (3, -3), (4, -3), (4, 3), (2, 3), (2, 2), (1,2), (1, 1), (0, 1)))
#p = OrthogonalPolygon(((0, 0), (3, 0), (3, 1), (2, 1), (2, 2), (1, 2), (1, 3), (0, 3)))
#p = OrthogonalPolygon(((0,0), (0,-2), (10, -2), (10, -1), (5, -1), (5, 0)))
#p = OrthogonalPolygon(points=[(15, 8), (18, 8), (18, 6), (17, 6), (17, 1), (18, 1), (18, 5), (19, 5), (19, 8), (20, 8), (20, 10), (15, 10)], holes=[])
#p = OrthogonalPolygon(points=[(3, 8), (12, 8), (12, 5), (14, 5), (14, 1), (11, 1), (11, 5), (7, 5), (7, 13), (3, 13)], holes=[])
#p = OrthogonalPolygon(points=[(27, 95), (29, 95), (29, 94), (32, 94), (32, 95), (34, 95), (34, 100), (30, 100), (30, 98), (27, 98)], holes=[])
#p = OrthogonalPolygon(points=[(37, 69), (42, 69), (42, 70), (41, 70), (41, 73), (38, 73), (38, 71), (37, 71)], holes=[])
#p = OrthogonalPolygon(points=[(95, 28), (97, 28), (97, 31), (99, 31), (99, 32), (100, 32), (100, 33), (95, 33)], holes=[])
#p = OrthogonalPolygon(points=[(19, 52), (21, 52), (21, 47), (24, 47), (24, 52), (22, 52), (22, 57), (21, 57), (21, 60), (20, 60), (20, 57), (19, 57)], holes=[])
#p = OrthogonalPolygon(points=[(19, 52), (21, 52), (21, 47), (24, 47), (24, 52), (22, 52), (22, 57), (21, 57), (21, 60), (20, 60), (20, 57), (19, 57)], holes=[])
#rectangles = p.split()
#pprint(rectangles)

#m = RectangleMerger()
#polygons = m.merge(rectangles)
#pprint(polygons)

#rectangles = [AxisAligned2DRectangle((21, 7), (26, 12)), AxisAligned2DRectangle((10, 18), (15, 22)), AxisAligned2DRectangle((15, 18), (17, 22))]
#print m.merge(rectangles)
#data = RectangleMerger.MergeData(rectangles)

#lines = [AxisAligned2DLine((1, 1), (1, -1)), AxisAligned2DLine((1, 0), (1, 1))]
#lines = [AxisAligned2DLine((3, 1), (2, 1)), AxisAligned2DLine((1, 1), (2, 1)), AxisAligned2DLine((0, 1), (1, 1))]
#lines = [AxisAligned2DLine((10, 10), (10, 5)), AxisAligned2DLine((10, 10), (10, 0)), AxisAligned2DLine((10, 10), (10, 15))]
#lines = m._simplify_colinear_lines(lines, data)
#print '-'*10, lines

p = OrthogonalPolygon([(0, 0), (10, 0), (10, 10), (0, 10)], holes=[OrthogonalPolygon([(4, 4), (6, 4), (6, 6), (4, 6)])])
rectangles = p.split()
print rectangles
