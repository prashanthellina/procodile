'''
Procedural generation abstractions and tools.

G{importgraph}
'''

import sys
import os
import random
import inspect
import copy

from procodile.utils import BlockWorldException
from procodile.repository.core.client.utils import Repository
import procodile.buildspace as bs
import procodile.transformations as trans
from procodile.draw import Matrix

class ProceduralException(BlockWorldException):
    '''
    Generic Procedural Exception.
    '''
    def __init__(self, message):
        self._message = message

    def __repr__(self):
        return self._message

    def __str__(self):
        return repr(self)

class Config(dict):
    #http://code.activestate.com/recipes/361668/
    """A dict whose items can also be accessed as member variables.

    >>> d = attrdict(a=1, b=2)
    >>> d['c'] = 3
    >>> print d.a, d.b, d.c
    1 2 3
    >>> d.b = 10
    >>> print d['b']
    10

    # but be careful, it's easy to hide methods
    >>> print d.get('c')
    3
    >>> d['get'] = 4
    >>> print d.get('a')
    Traceback (most recent call last):
    TypeError: 'int' object is not callable
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self

    def serialize(self, doc):
        config = doc.config
        config.attrs = self

class GeneratorContext:
    def __init__(self):
        self.generator = None
        self.parent = None
        self.config = None
        self.seed = None
        self.index = None
        self.depth = None
        self.location = None # local location
        self.glocation  = None # global location

class BaseGenerator:
    '''
    Abstract class representation
    a "procedure" which can generate
    "items" procedurally.
    '''

    #: configuration for this generator
    CONFIG = (
                # Config parameters come here
                # some examples:

                # ('length', Range(10, 20)),
                # ('breadth', 50)
             )

    #: generator classes used by this generator
    #  to produce finer levels of complexity/detail.
    #  This is a mapping of sub-generator-name (str) ->
    #    sub-generator (tuple) where sub-generator
    #    is defined as (repo-uri, class-id, module-version)
    #  eg: {'road': ('http://example.com/repo', 
    #                'core.generators.RoadGenerator',
    #                '1.3'),
    #       'city': ('http://repos.com/repo',
    #                'somebody.project1.CityGenerator',
    #                ''),
    #       'river': River
    #      }
    SUB_GENERATORS = {}

    def __init__(self, name, seed, config, recipe,
                       location, bspace, parent_gen,
                       picker, depth):
        '''
        @type seed: int
        @param seed: identifies one unique "incarnation"
            or "build" of the generator.
        '''

        self.id = bspace.get_gen_id()
        self.seed = seed
        self.bspace = bspace
        self.location = location
        self.name = name
        self.depth = depth
        self.config = config
        self.recipe = recipe
        self.picker = picker

        self.geoms = {}
        self.matrix = None

        x, y, z = self.location.get_translation()
        self.bbox = bs.BoundBox(x, y, z, x, y, z)
        
        self.parent = parent_gen
        self.ancestors = []
        self._compute_ancestors()
        self.children = []

        self.gen_trans = {}
        self.geom_trans = {}
        self.inv_location = location.inverse()

        if parent_gen:
            parent_gen.children.append(self)

        self.generate(self.config)

        bspace.index.update(self)
        self.reset_trans()

        if not parent_gen:
            self.bspace.root_gen = self

    def _serialize_mesh(self, geom, **options):
        vertices, indices = geom.tessellate(1)
        face_normals = []
        vertex_normals = [[] for i in xrange(len(vertices))]

        for a, b, c in indices:
            pa = vertices[a]
            pb = vertices[b]
            pc = vertices[c]

            v1 = pb - pa
            v2 = pc - pa

            fn = v1.cross(v2)

            vertex_normals[a].append(fn)
            vertex_normals[b].append(fn)
            vertex_normals[c].append(fn)
            
        for index, fns in enumerate(vertex_normals):
            if not fns:
                vn = None

            elif len(fns) == 1:
                vn = fns[0]

            else:
                vn = sum(fns[1:], fns[0])

            if vn:
                if 0 not in (vn.x, vn.y, vn.z):
                    vn.normalize()
                vertex_normals[index] = (vn.x, vn.y, vn.z)

            else:
                vertex_normals[index] = (0, 0, 0)
        
        vertices = [(v.x, v.y, v.z) for v in vertices]
        mesh = '%s;\n%s;\n%s;' % (repr(vertices),
                              repr(vertex_normals),
                              repr(indices))
        return mesh

    def _serialize_geoms(self, gen, **options):
        gen_geoms = gen.geoms
        for g in self.geoms.itervalues():
            
            gbbox, gnode = self.bspace.index.node_map[id(g)]
            gbbox = ', '.join('%.2f' % i for i in gbbox.as_tuple())
            loc = g.matrix.get_formatted()
            geom = gen_geoms.geom

            geom.attrs = (('shape', g.ShapeType),
                          ('bbox', gbbox),
                          ('area', g.Area),
                          ('volume', '%.2f' % g.Volume),
                          ('location', loc))

            if options.get('mesh', True):
                geom.mesh = self._serialize_mesh(g, **options)

    def serialize(self, doc, **options):
        gen = doc.generator
                             
        bbox, node = self.bspace.index.node_map[id(self)]
        bbox = ', '.join('%.2f' % i for i in bbox.as_tuple())
        
        gen.attrs = (('id', self.id),
                     ('seed', self.seed),
                     ('name', self.name),
                     ('location', self.location.get_formatted()),
                     ('bbox', bbox))

        self.config.serialize(gen)

        if options.get('geoms', True):
            self._serialize_geoms(gen, **options)

        sgen = gen.sub_generators
        for child in self.children:
            child.serialize(sgen, **options)

    def _compute_ancestors(self):
        ancestors = []
        cur_node = self.parent
        while cur_node:
            ancestors.append(cur_node)
            cur_node = cur_node.parent
        self._ancestors = ancestors

    def add_geom(self, geom, _global=False): 

        # compute global position of geom
        if not _global:
            geom.matrix = self.location.multiply(geom.matrix)

        geom.generator = self

        # remember geom
        _id = id(geom)
        self.geoms[_id] = geom

        index = self.bspace.index

        # (re)add generator into spatial index
        # grow the bound box of generator if required
        # as per the geom being added
        bbox = geom.get_bound_box()
        bbox = bs.BoundBox(*bbox)
        self.bbox.merge(bbox)
        index.update(self)
        
        # (re)add geom into spatial index
        index.update(self, geom)
    
    def add_geoms(self, *geoms):
        if len(geoms) == 1 and isinstance(geoms[0], (list, tuple)):
            geoms = geoms[0]

        for geom in geoms:
            self.add_geom(geom)
 
    def del_geoms(self, *geoms):

        index = self.bspace.index

        for geom in geoms:
            _id = id(geom)

            if _id in self.geoms:
                del self.geoms[_id]

            index.remove(self, geom)

            geom.generator = None

        # recompute bbox
        self.bbox = bs.BoundBox()
        for geom in self.geoms.itervalues():
            bbox = geom.get_bound_box()
            bbox = bs.BoundBox(*bbox)
            self.bbox.merge(bbox)

        index.update(self)

    def replace_geom(self, old_geom, new_geom):
        _id = id(old_geom)

        if _id in self.geom_trans:
            old_geom, gmatrix = self.geom_trans.pop(_id)
            old_geom.matrix = gmatrix
            new_geom.matrix = self.location.multiply(new_geom.matrix)

        else:
            raise ProceduralException('unknown geom: %s' % old_geom)

        gen_obj = old_geom.generator
        _gid = id(gen_obj)

        if _gid in self.gen_trans:
            gen_obj, glocation, gbbox = self.gen_trans.pop(_gid)
            gen_obj.location = glocation
            gen_obj.bbox = gbbox

        gen_obj.del_geoms(old_geom)
        gen_obj.add_geom(new_geom, _global=True)
       
        self.transform_generator(gen_obj)
        self.transform_geom(new_geom)

    def _get_global_bbox(self, bbox):
        return bs.BoundBox(bbox).transform(self.location)

    def _do_spatial_query(self, bbox, query):
        bbox = self._get_global_bbox(bbox) if bbox else self.bbox
        query_fn = getattr(self.bspace.index, query)
        sr = query_fn(bbox)
        self.transform_results(sr)
        return sr

    def get_intersection(self, bbox=None):
        return self._do_spatial_query(bbox, 'intersection')
    
    def get_within(self, bbox=None):
        return self._do_spatial_query(bbox, 'within')

    def get_surrounding(self, bbox=None):
        return self._do_spatial_query(bbox, 'surrounding')

    def get_enclosing(self, bbox=None):
        return self._do_spatial_query(bbox, 'enclosing')

    def reset_trans(self):
        for generator, glocation , gbbox in self.gen_trans.itervalues():
            generator.location = glocation
            generator.bbox = gbbox

        self.gen_trans = {}

        for geom, gmatrix in self.geom_trans.itervalues():
            geom.matrix = gmatrix

        self.geom_trans = {}

    def transform_generator(self, generator):
        _id = id(generator)

        if _id in self.gen_trans or generator == self:
            return

        glocation = generator.location
        gbbox = generator.bbox

        lbbox = gbbox.transform(self.inv_location)
        llocation = self.inv_location.multiply(generator.location)

        self.gen_trans[_id] = generator, glocation, gbbox
        generator.location = llocation
        generator.bbox = lbbox

    def transform_geom(self, geom):
        
        _id = id(geom)
        
        if _id in self.geom_trans:
            return

        gmatrix = geom.matrix
        lmatrix = self.inv_location.multiply(gmatrix)

        self.geom_trans[_id] = geom, gmatrix
        geom.matrix = lmatrix

    def transform_results(self, results):
        
        for generator in results.get_generators():
            self.transform_generator(generator)

        for geom in results.get_geoms():
            self.transform_geom(geom)

    def subgen(self, sub_gen_name, location, *config_args,
                    **config_kwargs):

        generator = self.get_sub_generator(sub_gen_name)
        index = len(self.children)
        seed = make_seed(self.seed, index)

        config = generator.make_config(*config_args,
                                       **config_kwargs)

        location = Matrix(location)

        gen_obj = rungen(generator, config,
                         seed=seed,
                         name=sub_gen_name,
                         location=location,
                         bspace=self.bspace,
                         recipe=self.recipe,
                         parent=self,
                         index=index)

    @classmethod
    def make_config(self, *args, **kwargs):

        config = self.CONFIG

        # when key-value pairs are not enclosed in a tuple but laid out
        # directly using only whitespace for separation, then it is a linear
        # type config. This format of config is supported to allow
        # for more readability.
        is_linear_config = [1 for i in config if not isinstance(i, (tuple, list))]

        # convert linear type config into standard form
        if is_linear_config:
            _config = []
            for index in xrange(0, len(config), 2):
                _config.append(config[index:index+2])
            config = _config

        config = [list(p) for p in config]

        assert(len(args) <= len(config))

        # apply positional arguments
        for index, arg in enumerate(args):
            if arg == None:
                continue

            key, value = config[index]
            config[index] = key, arg

        # apply keyword arguments
        config = dict(config)
        for key, value in kwargs.iteritems():
            assert(key in config)
            config[key] = value

        return Config(config)

    def generate(self, config):
        pass

    @classmethod
    def get_sub_generator(self, name):
        '''
        @type name: str
        @param name: name of the sub generator
            defined as a key in SUB_GENERATORS

        @rtype: classobj
        @return: generator class (child of BaseGenerator)
        '''
        data = self.SUB_GENERATORS[name]

        if inspect.isclass(data):
            return data

        repo_uri, class_id, package_version = data
        repo = Repository(repo_uri)
        sub_generator = repo.get(class_id, package_version)
        return sub_generator

def rungen(generator, config, seed=0,
           name=None, location=None,
           bspace=None, picker=None,
           recipe=None, parent=None,
           index=0):

    if not picker:
        picker = Picker(seed)
        _config = picker.pick(config)

    if not location:
        location = Matrix()

    if not bspace:
        bspace = bs.BuildSpace()

    if parent:
        depth = parent.depth + 1
        glocation = parent.location.multiply(location)
    else:
        depth = 0
        glocation = location

    g = GeneratorContext()

    g.generator = generator
    g.index = index
    g.seed = seed
    g.config = _config
    g.location = location
    g.glocation = glocation
    g.parent = parent
    g.depth = depth
    g.name = name

    # Recipe handling

    if recipe:
        recipe.apply(g)

        # recipe has modified seed
        if g.seed != seed:
            picker = Picker(g.seed)
            g.config = picker.pick(config)

    if not g.generator:
        # recipe wants to inhibit
        return

    gen_obj = g.generator(name, g.seed, g.config, recipe,
                          g.glocation, bspace, parent,
                          picker, depth)

    return gen_obj

class Random:
    '''
    Generates pseudo random numbers
    given a seed value.
    '''

    def __init__(self, seed=None):
        self._seed = None

        self.seed(seed)

    def seed(self, seed):
        self.seed = seed
        if seed is not None:
            self._random = random.Random(seed)
        else:
            self._random = random.Random()

    def generate(self, _range):

        if not _range:
            return _range

        elif isinstance(_range, tuple):
            _range = Range(*_range)
            return self.generate(_range)

        elif isinstance(_range, Range):
            if isinstance(_range.min, int) and isinstance(_range.max, int):
                return self._random.randint(_range.min, _range.max)
            else:
                return self._random.uniform(_range.min, _range.max)

        elif isinstance(_range, (list, xrange)):
            return self._random.choice(_range)

        elif isinstance(_range, (dict, Config)):
            return self.configure(_range)

        else:
            return _range

    def decision(self):
        return bool(self._random.randint(0, 1))

    def configure(self, config):
        _config = {}

        for key, value in config.iteritems():
            value = self.generate(value)
            _config[key] = value

        config = Config(_config)
        return config

class Picker(Random):
    '''
    Simple wrapper around L{Random} to make
    a user friendly API.
    '''
    
    def pick(self, data=(True, False)):
        return Random.generate(self, data)
    
class Range:
    def __init__(self, _min, _max):
        self.min = _min
        self.max = _max

    def __repr__(self):
        return 'Range(%s, %s)' % (self.min, self.max)

def make_seed(*seeds):
    return abs(hash(seeds))

def load_generator(path):
    mpath, gclass_name = path.rsplit('.', 1)
    module = __import__(mpath, fromlist=[gclass_name])
    generator = getattr(module, gclass_name)
    return generator
