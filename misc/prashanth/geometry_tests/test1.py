from geometry import *

g = PolygonGenerator()
m = RectangleMerger()
d = DiagramGenerator()

for p in g:
    print 'GENPOLY: ', p
    d.generate([p])
    rectangles = p.split()
    #print 'SPLITRECTS: ', rectangles
    polygons = m.merge(rectangles)
    poly = polygons[0]

    if poly != p:
        print poly
        import pdb; pdb.set_trace()
        break
    print '-' * 50
