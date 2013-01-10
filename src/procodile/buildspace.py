'''
Represents the build space where "drawing" happens.

G{importgraph}
'''

import cStringIO
import time

from rtree import index as rtree

from procodile.xmlwriter import XMLNode

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
    _types = geom.tags if geom.tags else [geom.generator]
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
            'generator': lambda geom, generator: geom.generator in generator,
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
                        generator=None,
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

        if generator:
            checks.append((m(generator), f['generator']))

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

class StopBuildException:
    '''
    Indicates that build process must be stopped.
    This exception must never be caught by "user" code
    in generators.
    '''
    pass

class BuildSpace:
    '''
    Represents the space in which generator
    activity occurs. All generators in a single
    run operate in this space. This is synonymous
    with document in a 3d editor.
    '''

    BFS = 0
    DFS = 1

    STATE_READY = 0
    STATE_RUNNING = 1
    STATE_PAUSED = 2
    STATE_COMPLETED = 3

    WAIT_INTERVAL = .1 # seconds

    def __init__(self, strategy=BFS):

        self.state = self.STATE_READY
        self.root_gen = None
        self.materials = {}
        self.textures = {}
        self.strategy = strategy
        self.queue = []

        self.index = SpatialIndex()

        self.event_handlers = []

    def register_material(self, material):
        if material and material not in self.materials:
            self.materials[material] = material
            return True
       
    def register_texture(self, texture):
        if texture and texture.fpath and texture not in self.textures:
            self.textures[texture] = texture
            return True

    def get_registered_material(self, material):
        return self.materials.get(material)
        
    def _wait(self):
        while self.state == self.STATE_PAUSED:
            time.sleep(self.WAIT_INTERVAL)

    def notify_event(self, event, *args):
        if self.state == self.STATE_PAUSED:
            self._wait()

        elif self.state == self.STATE_COMPLETED:
            raise StopBuildException

        for handler in self.event_handlers:
            handler(event, args)

    def queue_generator(self, run_fn):
        self.queue.append(run_fn)

    def process_queue(self):

        s = self.strategy
        q = self.queue

        if not q:
            return False

        run = q.pop(0) if s == self.BFS else q.pop(len(q) - 1)

        gen_obj = run()

        return None if s == self.BFS else gen_obj

    def run(self, re_run=False):
        try:

            if self.strategy == self.BFS:
                if self.root_gen is None or re_run:
                    while self.queue:
                        self.process_queue()
                    self.on_build_done()

            elif self.strategy == self.DFS:
                ret = self.process_queue()
                self.on_build_done()
                return ret

        except StopBuildException:
            pass

    def on_build_done(self):
        self.state = self.STATE_COMPLETED

    def pause(self):
        self.state = self.STATE_PAUSED

    def resume(self):
        self.state = self.STATE_RUNNING

    def stop(self):
        self.queue[:] = [] # clear queue
        self.state = self.STATE_COMPLETED

    def serialize(self, **options):
        doc = XMLNode('buildspace')
        self.root_gen.serialize(doc, **options)

        stream = cStringIO.StringIO()
        doc.serialize(stream)
        return stream.getvalue()

    def query(self, match_fn):
        matches = []
        r = self.root_gen

        if not r:
            return matches

        if match_fn(r.info, r.info):
            matches.append(r)

        matches.extend(self._query(r.info, r, match_fn))
        return matches

    def _query(self, rinfo, gen, match_fn):
        matches = []
        
        for sgen in gen.children:
            if match_fn(sgen.info, rinfo):
                matches.append(sgen)

            matches.extend(self._query(rinfo, sgen, match_fn))

        return matches

    def _get_class(self, gen):

        # When a recipe is created by applying recipe config to a
        # generator, a sub-class of generator is created to represent
        # the recipe. However, the following will not work because of
        # this. The following is a special case handling to remedy that.
        if hasattr(gen, '_is_recipe_based_generator') and \
            not gen.parent:
            _class = gen.__class__.__bases__[0]
        else:
            _class = gen.__class__

        return _class

    def _single_gen_xpaths(self, generator, names):
        parent_gen = generator.parent

        g_class = self._get_class(generator)
        g = names[g_class]
        g_id = generator.id

        if parent_gen:
            p_class = self._get_class(parent_gen)
            p = names[p_class]
            p_id = parent_gen.id
        else:
            p_class = p = p_id = None

        xpaths = []

        x = '//%s[id == "%s"]' % (g, g_id)
        d = 'Selected "%s"' % g
        xpaths.append((x, d, g_class))

        x = '//%s' % (g)
        d = 'All "%s"s' % g
        xpaths.append((x, d, g_class))
       
        if parent_gen:
            x = '//%s[id == "%s"]/%s' % (p, p_id, g)
            d = '"%s"s directly inside "%s"' % (g, p)
            xpaths.append((x, d, g_class))
        
            x = '//%s[id == "%s"]//%s' % (p, p_id, g)
            d = '"%s"s inside "%s"' % (g, p)
            xpaths.append((x, d, g_class))
        
            x = '//%s[id == "%s"]' % (p, p_id)
            d = '"%s" containing "%s"' % (p, g)
            xpaths.append((x, d, p_class))
            
            x = '//%s/%s' % (p, g)
            d = '"%s"s directly inside any "%s"' % (g, p)
            xpaths.append((x, d, g_class))
            
            x = '//%s//%s' % (p, g)
            d = '"%s"s inside any "%s"' % (g, p)
            xpaths.append((x, d, g_class))
            
            x = '//%s' % (p)
            d = '"%s"s' % (p)
            xpaths.append((x, d, p_class))

        return xpaths

    def _multi_gen_xpaths(self, generators, names):
        pass

    def suggest_xpaths(self, generators, names):
        if not isinstance(generators, (list, tuple, set)):
            generators = [generators]

        if len(generators) == 1:
            return self._single_gen_xpaths(generators[0], names)

        else:
            return self._multi_gen_xpaths(generators, names)
