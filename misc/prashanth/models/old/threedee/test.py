from building import Generator as bgen
from pprint import pprint
import procodile.draw as draw

config = bgen.make_config()
config.num_levels = 1
config.height = None

seed = 0
o_bgen = bgen(seed, config)

# show geoms in freecad
#parts = o_bgen.bspace.get_all_geoms()
#for p in parts:
#    draw.show(p)

# serialize generator tree
print o_bgen.bspace.serialize()

# rtree test
# for _id, (bbox, node) in o_bgen.bspace.index.node_map.iteritems():
#     results = o_bgen.bspace.index.contained(bbox)
#     print _id, node.gen_obj, node.geom, bbox
#     results = [r[:2] for r in results]
#     pprint(results)
#     print

sr = o_bgen.get_surrounding((0, 0, 0, 10, 10, 0.15))
pprint (sr.generators)
print
print
pprint (sr.geoms)
