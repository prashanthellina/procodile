from geometry import *
from pprint import pprint

'''
rectangles = [AxisAligned2DRectangle((58, 91), (62, 92)), AxisAligned2DRectangle((37, 35), (41, 38)), AxisAligned2DRectangle((58, 49), (60, 51)), AxisAligned2DRectangle((79, 26), (81, 28)), AxisAligned2DRectangle((23, 91), (24, 94)), AxisAligned2DRectangle((4, 39), (5, 42)), AxisAligned2DRectangle((10, 96), (12, 98)), AxisAligned2DRectangle((1, 94), (5, 99)), AxisAligned2DRectangle((77, 6), (79, 7)), AxisAligned2DRectangle((71, 94), (75, 95)), AxisAligned2DRectangle((53, 11), (58, 14)), AxisAligned2DRectangle((45, 41), (50, 43)), AxisAligned2DRectangle((31, 75), (33, 77)), AxisAligned2DRectangle((89, 63), (93, 64)), AxisAligned2DRectangle((13, 39), (16, 43)), AxisAligned2DRectangle((52, 60), (57, 65)), AxisAligned2DRectangle((50, 64), (54, 68))]

m = RectangleMerger()
polygons = m.merge(rectangles)

pprint( polygons )
'''

m = RectangleMerger()

# big rectangle with two rectangular holes
polygons = [
            OrthogonalPolygon(((0, 0), (100, 0), (100, 100), (0, 100))),
            OrthogonalPolygon(((10, 10), (40, 10), (40, 90), (10, 90))),
            OrthogonalPolygon(((60, 10), (90, 10), (90, 90), (60, 90))),
           ]

polygons = [
            OrthogonalPolygon(points=[(10, 18), (11, 18), (11, 15), (14, 15), (14, 14), (16, 14), (16, 11), (21, 11), (21, 16), (20, 16), (20, 20), (21, 20), (21, 24), (20, 24), (20, 23), (19, 23), (19, 16), (16, 16), (16, 19), (11, 19), (11, 22), (10, 22)]),
            OrthogonalPolygon(points=[(15, 23), (18, 23), (18, 27), (15, 27)])
           ]
polygons = [
            OrthogonalPolygon(points=[(24, 11), (30, 11), (30, 7), (35, 7), (35, 8), (39, 8), (39, 13), (35, 13), (35, 11), (31, 11), (31, 15), (29, 15), (29, 20), (28, 20), (28, 17), (24, 17)]), OrthogonalPolygon(points=[(32, 12), (34, 12), (34, 14), (32, 14)])
           ]
polygons = [
    OrthogonalPolygon(points=[(14, 22), (19, 22), (19, 26), (23, 26), (23, 28), (24, 28), (24, 30), (22, 30), (22, 29), (19, 29), (19, 27), (14, 27)]), OrthogonalPolygon(points=[(15, 29), (17, 29), (17, 32), (15, 32)])
]

print polygons[0].is_point_inside((15, 29))
pprint (m._pair_polygons_and_holes(polygons))
