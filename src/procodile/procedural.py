'''
Procedural generation abstractions and tools.

G{importgraph}
'''

import os
import logging

from procodile.utils import ProcodileException, DotAccessDict, Matrix
from procodile.draw import SurfaceGroup
import procodile.buildspace as bs
import procodile.pick as pick

log = logging.getLogger()

class ProceduralException(ProcodileException):
    '''
    Generic Procedural Exception.
    '''
    def __init__(self, message):
        self._message = message

    def __repr__(self):
        return self._message

    def __str__(self):
        return repr(self)

class GeneratorInfo:
    def __init__(self):
        self.id = None
        self.name = None

        # Generator class
        self.generator = None

        # parent generator
        self.parent = None

        self.config = None
        self.seed = None
        self.s_seed = None
        self.index = None
        self.depth = None
        self.location = None # local location
        self.glocation  = None # global location

class Generator:
    '''
    Abstract class representation
    a "procedure" which can generate
    "items" procedurally.
    '''

    TITLE = ''
    DESCRIPTION = ''

    #: configuration for this generator
    CONFIG = (
                # Config parameters come here
                # some examples:

                # ('length', Range(10, 20)),
                # ('breadth', 50)
             )

    #: generator classes used by this generator
    #  to produce finer levels of complexity/detail.
    #  This is a mapping of :
    #  sub-generator-name (str) -> sub-generator class object
    #  eg: {
    #        'river': River
    #      }
    SUB_GENERATORS = {}

    #: Materials that can be applied to geoms produced by this
    #   generator.
    #  This is a mapping of :
    #  material-name (str) -> material class/object
    #  eg: {
    #        'bark': Bark
    #      }
    MATERIALS = {}

    RECIPE_CONFIG = None

    #: Will be assigned value of type GeneratorIdentification by Loader.
    #   This is for internal use only.
    IDENT = None

    def __init__(self, info, recipes, bspace, picker, log=None):

        self.id = info.id
        self.seed = info.seed
        self.s_seed = info.s_seed
        self.location = info.glocation
        self.name = info.name
        self.depth = info.depth
        self.config = info.config
        self.parent = info.parent
        self.info = info
        self.log = log or globals()['log']
        self.config.materials = info.materials

        self.recipes = recipes
        self.picker = picker
        self.bspace = bspace

        self.geoms = {}
        self.matrix = None

        x, y, z = self.location.get_translation()
        self.bbox = bs.BoundBox(x, y, z, x, y, z)

        self.ancestors = []
        self._compute_ancestors()
        self.children = []
        self._num_subgens = 0

        self.gen_trans = {}
        self.geom_trans = {}
        self.inv_location = self.location.inverse()

        parent = info.parent
        if parent:
            parent.children.append(self)

        if not parent:
            self.bspace.root_gen = self

        bspace.notify_event('add_gen', self, self.parent)

        self.generate(self.config)

        bspace.index.update(self)
        self.reset_trans()

    @classmethod
    def get_recipe_config(self):
        r = self.RECIPE_CONFIG

        if not r:
            return None

        return r[0] if isinstance(r, list) else r

    @classmethod
    def add_recipe_config(self, rc):
        _rc = self.RECIPE_CONFIG

        if not _rc:
            self.RECIPE_CONFIG = [rc]
        
        else:
            if isinstance(_rc, list):
                _rc.insert(0, rc)
            else:
                self.RECIPE_CONFIG = [rc, _rc]

    def _serialize_mesh(self, geom, **options):
        vertices, indices, normals, tcoords = geom.mesh

        mesh = '%s;\n%s;\n%s;' % (repr(vertices),
                              repr(normals),
                              repr(indices))
        return mesh

    def _serialize_geoms(self, gen, **options):
        gen_geoms = gen.geoms
        for g in self.geoms.itervalues():

            gbbox, gnode = self.bspace.index.node_map[id(g)]
            gbbox = ', '.join('%.2f' % i for i in gbbox.as_tuple())
            loc = g.matrix.get_formatted()
            geom = gen_geoms.geom

            geom.attrs = (('bbox', gbbox),
                          ('location', loc),
                          ('visible', 1 if g.visible else 0))

            if options.get('mesh', True):
                geom.mesh = self._serialize_mesh(g, **options)

    def serialize(self, doc, **options):
        gen = doc.generator

        bbox, node = self.bspace.index.node_map[id(self)]
        bbox = ', '.join('%.2f' % i for i in bbox.as_tuple())

        gen.attrs = (('id', self.id),
                     ('seed', self.seed),
                     ('s_seed', self.s_seed),
                     ('name', self.name),
                     ('location', self.location.get_formatted_location()),
                     ('bbox', bbox))

        gen.config.attrs = self.config

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
        self.ancestors = ancestors

    def add_geom(self, geom, _global=False):

        bspace = self.bspace

        # compute global position of geom
        if not _global:
            # TODO: delete line: geom.matrix = self.location.multiply(geom.matrix)
            geom.transform(self.location)

        geom.generator = self

        # remember geom
        _id = id(geom)
        self.geoms[_id] = geom

        index = bspace.index

        # (re)add generator into spatial index
        # grow the bound box of generator if required
        # as per the geom being added
        bbox = geom.get_bound_box()
        bbox = bs.BoundBox(*bbox)
        self.bbox.merge(bbox)
        index.update(self)

        # (re)add geom into spatial index
        index.update(self, geom)
     
        self._register_material(geom)
           
        bspace.notify_event('add_geom', self, geom)

    def _register_material(self, geom):
        bspace = self.bspace
        pdir = self.IDENT.package_dir

        if isinstance(geom, SurfaceGroup):
            geoms = geom.surfaces.values()
        else:
            geoms = [geom]
        
        for geom in geoms:
           
            if geom.material:
                t = geom.material.texture
                t.fpath = os.path.join(pdir, t.fpath)
                if bspace.register_texture(t):
                    bspace.notify_event('add_texture', t)

            if bspace.register_material(geom.material):
                bspace.notify_event('add_material', geom.material)
            else:
                geom.material = bspace.get_registered_material(geom.material)

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

            self.bspace.notify_event('del_geom', self, geom)

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
            #  TODO: delete lines
            # old_geom, gmatrix = self.geom_trans.pop(_id)
            # old_geom.matrix = gmatrix
            # new_geom.matrix = self.location.multiply(new_geom.matrix)
            
            old_geom = self.geom_trans.pop(_id)
            old_geom.transform(self.location)
            new_geom.transform(self.location)

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
            geom.transform(self.location)

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

        # TODO: delete lines: gmatrix = geom.matrix
        # lmatrix = self.inv_location.multiply(gmatrix)

        # self.geom_trans[_id] = geom, gmatrix
        # geom.matrix = lmatrix
        
        self.geom_trans[_id] = geom
        geom.transform(self.inv_location)

    def transform_results(self, results):

        for generator in results.get_generators():
            self.transform_generator(generator)

        for geom in results.get_geoms():
            self.transform_geom(geom)

    def _subgen(self, generator, config, seed, name,
                location, index):
        gen_obj = rungen(generator, config,
                         seed=seed,
                         name=name,
                         location=location,
                         bspace=self.bspace,
                         parent=self,
                         index=index,
                         log=self.log)
        return gen_obj

    def subgen(self, sub_gen_name, location, *config_args,
                    **config_kwargs):

        generator = self.get_sub_generator(sub_gen_name)
        index = self._num_subgens

        seed = pick.make_seed(self.seed, index)

        config = generator.make_config(*config_args,
                                       **config_kwargs)

        location = Matrix(location)

        gen_obj = self._subgen(generator, config, seed,
                        sub_gen_name, location, index)

        self._num_subgens += 1

    @staticmethod
    def _parse_data(data):

        # when key-value pairs are not enclosed in a tuple but laid out
        # directly using only whitespace for separation, then it is a linear
        # type data. This format of data is supported to allow
        # for more readability.
        seq = (tuple, list)
        is_linear = [1 for i in data if not isinstance(i, seq)]

        # convert linear type data into standard form
        if is_linear:
            _data = []
            for index in xrange(0, len(data), 2):
                _data.append(data[index:index+2])
            data = _data

        data = [list(p) for p in data]

        return data

    @classmethod
    def get_config(self):
        return self._parse_data(self.CONFIG)

    @classmethod
    def make_config(self, *args, **kwargs):
        
        config = self.get_config()

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

        return DotAccessDict(config)

    @classmethod
    def get_subgens(self):
        subgens = self.SUB_GENERATORS
        if isinstance(subgens, dict):
            return subgens

        self.SUB_GENERATORS = dict(self._parse_data(subgens))
        return self.SUB_GENERATORS

    def generate(self, config):
        pass

    @classmethod
    def get_sub_generator(self, name):
        '''
        @type name: str
        @param name: name of the sub generator
            defined as a key in SUB_GENERATORS

        @rtype: classobj
        @return: generator class (child of Generator)
        '''
        return self.get_subgens()[name]

    def cleanup(self, deep=False):

        if deep:
            for c in self.children[:]:
                c.cleanup(deep)

        if self.parent:
            self.parent.children.remove(self)
        else:
            self.bspace.root_gen = None

        geoms = self.geoms.values()
        self.del_geoms(*geoms)
        self.bspace.index.remove(self)
        
        self.bspace.notify_event('del_gen', self, self.parent)

class Category(Generator):
    '''
    Abstract class which serves to indicate that
    a given generator is a category type. The indication
    is acheived by subclassing from this class
    '''
    pass

def _pick_materials(picker, materials):
    _materials = DotAccessDict()

    for name, material in materials.iteritems():
        if isclass(material):
            material = material()

        material = picker.pick(material)
        material.name = name
        _materials[name] = material

    return _materials

def _rungen(generator, config, seed=0,
            name=None, location=None,
            bspace=None, picker=None,
            parent=None, index=0, log=None):

    if not picker:
        picker = pick.Picker(seed)
        _config = picker.pick(config)
        _materials = _pick_materials(picker, generator.MATERIALS)

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

    recipes = []
    _id = '%s' % index

    g = GeneratorInfo()

    g.id = _id
    g.generator = generator
    g.index = index
    g.seed = seed
    g.s_seed = seed
    g.config = _config
    g.materials = _materials
    g.location = location
    g.glocation = glocation
    g.parent = parent
    g.depth = depth
    g.name = name
    g.picker = picker

    # remembering original values
    # (cannot be modified by recipe)
    g._seed = seed
    g._config = config.copy()
    g._generator = generator

    # Recipe handling

    def on_seed_changed(key, value):
        if key != 's_seed':
            return
        # seed modified, so recompute picker and config
        g.picker = pick.Picker(g.s_seed)
        g.config = picker.pick(config)
        g.materials = _pick_materials(picker, generator.MATERIALS)

    rc = generator.RECIPE_CONFIG

    if rc:
        rc = rc if isinstance(rc, list) else [rc]
        rc = [(g, x) for x in rc]
        recipes.extend(rc)

    for root_info, recipe_config in reversed(recipes):
        recipe_config.apply(g, root_info, on_seed_changed)

        if not g.generator:
            # recipe wants to inhibit
            return

    # checking if g.generator has changed after applying recipe
    if g.generator != generator:
        new_config = dict(g.generator.get_config())
        new_config = g.picker.pick(new_config)

        for c in new_config:
            if c in g.config:
                new_config[c] = g.config[c]

        g.config = new_config

    gen_obj = g.generator(g, recipes, bspace, g.picker, log)

    return gen_obj

def rungen(generator, config, seed=0,
           name=None, location=None,
           bspace=None, picker=None,
           parent=None, index=0, log=None):

    if not bspace:
        bspace = bs.BuildSpace()

    def run_fn():
        return _rungen(generator, config, seed, name, location,
                       bspace, picker, parent, index, log)

    bspace.queue_generator(run_fn)

    if not parent: # is root gen
        bspace.state = bspace.STATE_RUNNING

    try:
        return bspace.run()
    finally:
        if not parent:
            bspace.state = bspace.STATE_COMPLETED

def _ensure_rerun_state(bspace):
    if bspace.state != bspace.STATE_COMPLETED:
        raise Exception('cannot rerun in current state')

def _make_rerun_fn(generator):

    g = generator
    info = g.info
    gen_class = info._generator
    config = info._config
    seed = info._seed
    name = info.name
    location = info.location
    parent = g.parent
    index = info.index

    def run_fn():
        g.cleanup(deep=True)
        parent._subgen(gen_class, config, seed,
                       name, location, index)

    return run_fn

def re_rungen(generator):
    return re_rungens([generator])

def re_run_rootgen(generator):
    g = generator

    bspace = g.bspace
    bspace.state = bspace.STATE_RUNNING

    try: 
        g.cleanup(deep=True)
     
        info = g.info
        gen_class = info._generator
        config = info._config
        seed = info._seed
        name = info.name
        location = info.location
        log = g.log
       
        return rungen(gen_class, config, seed, name, location,
                        bspace=g.bspace, log=log)
    finally:
        bspace.state = bspace.STATE_COMPLETED

def _filter_redundant_generators(generators):
    gens = set(generators)
    o_gens = []

    for g in generators:
        redundant = False

        for a in g.ancestors:
            if a in gens:
                redundant = True
                break

        if not redundant:
            o_gens.append(g)

    return o_gens

def re_rungens(generators):
    bspace = generators[0].bspace
    _ensure_rerun_state(bspace)

    generators = _filter_redundant_generators(generators)

    if len(generators) == 1 and generators[0] == bspace.root_gen:
        return re_run_rootgen(generators[0])

    for g in generators:
        run_fn = _make_rerun_fn(g)
        bspace.queue_generator(run_fn)

    bspace.state = bspace.STATE_RUNNING

    try:
        return bspace.run(re_run=True)
    finally:
        bspace.state = bspace.STATE_COMPLETED
