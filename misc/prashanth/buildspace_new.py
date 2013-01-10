'''
Represents the build space where "drawing" happens.

G{importgraph}
'''

import cStringIO

import numpy
from rtree import index as rtree

import draw
from procodile.xmlwriter import XMLNode
import procodile.transformations as trans
from procodile.utils import fequals_sequence

class BoundBox:
    def __init__(self, xmin=0, ymin=0, zmin=0,
                       xmax=0, ymax=0, zmax=0):

        if isinstance(xmin, BoundBox):
            xmin, ymin, zmin,
            xmax, ymax, zmax = xmin.as_tuple()
        
        elif isinstance(xmin, tuple):
            xmin, ymin, zmin, \
            xmax, ymax, zmax = xmin

        self.xmin = xmin
        self.ymin = ymin
        self.zmin = zmin
        self.xmax = xmax
        self.ymax = ymax
        self.zmax = zmax

    def merge(self, bbox):
        self.xmin = min(self.xmin, bbox.xmin)
        self.ymin = min(self.ymin, bbox.ymin)
        self.zmin = min(self.zmin, bbox.zmin)
        self.xmax = max(self.xmax, bbox.xmax)
        self.ymax = max(self.ymax, bbox.ymax)
        self.zmax = max(self.zmax, bbox.zmax)

    def contains(self, bbox):
        if not self.xmin <= bbox.xmin <= self.xmax:
            return False

        if not self.xmin <= bbox.xmax <= self.xmax:
            return False

        if not self.ymin <= bbox.ymin <= self.ymax:
            return False

        if not self.ymin <= bbox.ymax <= self.ymax:
            return False

        if not self.zmin <= bbox.zmin <= self.zmax:
            return False

        if not self.zmin <= bbox.zmax <= self.zmax:
            return False

        return True

    def transform(self, location):
        x1, y1, z1, x2, y2, z2 = self.as_tuple()
        x1, y1, z1 = location.transform((x1, y1, z1))
        x2, y2, z2 = location.transform((x2, y2, z2))

        bbox = BoundBox()
        bbox.xmin = min(x1, x2)
        bbox.xmax = max(x1, x2)
        bbox.ymin = min(y1, y2)
        bbox.ymax = max(y1, y2)
        bbox.zmin = min(z1, z2)
        bbox.zmax = max(z1, z2)

        return bbox

    def __copy__(self):
        return self.copy()

    def __deepcopy__(self):
        return self.copy()

    def copy(self):
        return BoundBox(*self.as_tuple())

    def as_tuple(self):
        return (self.xmin, self.ymin, self.zmin,
                self.xmax, self.ymax, self.zmax)

    def __str__(self):
        return '<BoundBox%s>' % repr(self.as_tuple())

    def __repr__(self):
        return str(self)

class IndexNode:
    def __init__(self, _id, gen_obj, geom=None):
        self.id = _id
        self.gen_obj = gen_obj
        self.geom = geom

class SpatialIndex:
    def __init__(self):
        p = rtree.Property()
        p.dimension = 3
        index = rtree.Index(None, properties=p)
        self.index = index

        self.node_map = {}

    def add(self, gen_obj, geom=None):
        bbox = geom.get_bound_box() if geom else gen_obj.bbox.as_tuple()
        _id = id(geom) if geom else id(gen_obj)
        node = IndexNode(_id, gen_obj, geom)
        self.index.insert(_id, bbox)
        self.node_map[_id] = (BoundBox(*bbox), node)

    def remove(self, gen_obj, geom=None):
        obj = geom if geom else gen_obj
        _id = id(obj)

        try:
            bbox, node = self.node_map.pop(_id)
        except KeyError:
            return

        self.index.delete(_id, bbox.as_tuple())

    def update(self, gen_obj, geom=None):
        self.remove(gen_obj, geom)
        self.add(gen_obj, geom)

    def has(self, gen_obj, geom=None):
        obj = geom if geom else gen_obj
        _id = id(obj)
        data = self.node_map.get(_id, None)

        return bool(data is not None)

    def _intersection(self, bbox):
        if isinstance(bbox, BoundBox):
            bbox = bbox.as_tuple()

        results = self.index.intersection(bbox)
        for index, _id in enumerate(results):
            bbox, node = self.node_map[_id]
            results[index] = node.gen_obj, node.geom, bbox
        return results

    def intersection(self, bbox, filter_fn=None):
        geoms = []
        generators = []

        results = self._intersection(bbox)

        for gen_obj, geom, nbbox in results:

            if filter_fn and not filter_fn(bbox, gen_obj, geom, nbbox):
                continue
                
            if geom:
                geoms.append(geom)
            else:
                generators.append(gen_obj)

        return SpatialResults(generators, geoms)

    def within(self, bbox):
        filter_fn = lambda bbox, gen_obj, geom, nbbox: bbox.contains(nbbox)
        return self.intersection(bbox, filter_fn)

    def surrounding(self, bbox):
        filter_fn = lambda bbox, gen_obj, geom, nbbox: not bbox.contains(nbbox)
        return self.intersection(bbox, filter_fn)

    def enclosing(self, bbox):
        filter_fn = lambda bbox, gen_obj, geom, nbbox: nbbox.contains(bbox)
        return self.intersection(bbox, filter_fn)

TRUE_FN = lambda a, b: True

def _sr_geom_type_filter(geom, _type):
    _types = geom.tags if geom.tags else [geom.parent]
    return set(_type).intersection(set(_types))

def _make_tuple(value):
    if isinstance(value, (list, tuple)):
        return value
    else:
        return (value,)

class SpatialResults:
    
    GENERATOR_FILTERS = {
            '_type': lambda gen, _type: isinstance(gen, _type),
            'parent': lambda gen, parent: gen.parent in parent,
            'ancestor': lambda gen, anc: set(anc).intersection(gen.ancestors),
        }

    GEOM_FILTERS = {
            '_type': _sr_geom_type_filter,
            'tag': lambda geom, tag: set(tag).intersection(set(geom.tags)),
            'parent': lambda geom, parent: geom.parent in parent,
            'visible': lambda geom, visible: geom.visible==visible,
        }

    def __init__(self, generators, geoms):

        self.generators = dict([(id(g), g) for g in generators])
        self.geoms = dict([(id(g), g) for g in geoms])

    def get_generators(self, _type=None,
                             parent=None,
                             ancestor=None,
                             filter_fn=TRUE_FN):
        generators = []

        checks = []
        f = self.GENERATOR_FILTERS
        m = _make_tuple

        if _type:
            checks.append((m(_type), f['_type']))

        if parent:
            checks.append((m(parent), f['parent']))

        if ancestor:
            checks.append((m(ancestor), f['ancestor']))

        for generator in self.generators.itervalues():

            skip_gen = False

            for value, check_fn in checks:
                if not check_fn(generator, value):
                    skip_gen = True
                    break

            if not skip_gen and filter_fn(self, generator):
                generators.append(generator)

        return generators

    def get_geoms(self, _type=None,
                        tag=None,
                        parent=None,
                        visible=None,
                        filter_fn=TRUE_FN):
        geoms = []

        checks = []
        f = self.GEOM_FILTERS
        m = _make_tuple

        if _type:
            checks.append((m(_type), f['_type']))
        
        if tag:
            checks.append((m(tag), f['tag']))

        if parent:
            checks.append((m(parent), f['parent']))

        if visible:
            checks.append((visible, f['visible']))

        for geom in self.geoms.itervalues():

            skip_geom = False

            for value, check_fn in checks:
                if not check_fn(geom, value):
                    skip_geom = True
                    break

            if not skip_geom and filter_fn(self, geom):
                geoms.append(geom)

        return geoms

class BuildSpace:
    def __init__(self):
        self.gen_id = 0
        self.root_gen = None

        self.index = SpatialIndex()

    def get_gen_id(self):
        gen_id = self.gen_id
        self.gen_id += 1
        return gen_id

    def serialize(self, **options):
        doc = XMLNode('buildspace')
        self.root_gen.serialize(doc, **options)

        stream = cStringIO.StringIO()
        doc.serialize(stream)
        return stream.getvalue()

    def get_all_geoms(self, node=None):
        if node == None:
            node = self.root_gen

        if not node:
            return []

        geoms = node.geoms.values()

        for cnode in node.children:
            geoms.extend(self.get_all_geoms(cnode))

        return geoms
