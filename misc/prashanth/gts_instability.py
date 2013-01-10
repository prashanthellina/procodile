'''
Test code for debugging the stability issues with boolean operations in GTS
'''

import gts
from pprint import pprint

show_vertex = lambda v: '%.2f, %.2f, %.2f' % (v.x, v.y, v.z)
show_face = lambda f: ('face', tuple(show_vertex(v) for v in f.vertices()))
show_surface = lambda s: ('surface', tuple(show_face(f) for f in s.faces()))

av1 = gts.Vertex(0, 0, 0)
av2 = gts.Vertex(1, 0, 0)
av3 = gts.Vertex(1, 1, 0)
av4 = gts.Vertex(0, 1, 0)

af1 = gts.Face(av1, av2, av3)
af2 = gts.Face(av3, av4, av1)

s1 = gts.Surface()
s1.add(af1)
s1.add(af2)

bv1 = gts.Vertex(0.5, 0, 0)
bv2 = gts.Vertex(1.5, 0, 0)
bv3 = gts.Vertex(1.5, 1, 0)
bv4 = gts.Vertex(0.5, 1, 0)

bf1 = gts.Face(bv1, bv2, bv3)
bf2 = gts.Face(bv3, bv4, bv1)

s2 = gts.Surface()
s2.add(bf1)
s2.add(bf2)

s3 = s1.union(s2)
pprint (show_surface(s3))

print s1.Nedges, s2.Nedges
num_edges = (s1.Nedges + s2.Nedges) / 2
print num_edges
print s3.coarsen(num_edges)
pprint (show_surface(s3))
print s3.area()
