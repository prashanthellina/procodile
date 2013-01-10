'''
Manages packages and their classes (generators etc) through loading, \
unloading and reloading.

G{importgraph}
'''

import os
import sys
import imp
import inspect
import logging
import xml.etree.ElementTree as etree

from procodile.xmlwriter import XMLNode
from procodile.procedural import Generator, Category
from procodile.utils import get_ancestors, log_function_call as logfn
from procodile.utils import get_tmp_dir, url_to_filename, get_random_name
from procodile.repository.utils import get_repos_cache, set_repos_cache
from procodile.repository.utils import parse_version, unparse_version
from procodile.repository.utils import get_package_versions
from procodile.repository.utils import RepositoryException
from procodile.repository.add_package import add_package
from procodile.repository.client import CLIENT

log = logging.getLogger()

d = os.path.dirname
PYTHON_INSTALL_DIR = d(d(os.__file__))
PY_STD_PATHS = [p for p in sys.path if p.startswith(PYTHON_INSTALL_DIR)]
PROCODILE_DIR = d(imp.find_module('procodile')[1])
ALLOWED_PATHS = [PROCODILE_DIR] + PY_STD_PATHS

#: Package which is currently being loaded
CUR_PACKAGE = None

def _is_in_dir(path, _dir):
    '''
    Check if path points to an entity inside _dir.
    '''
    return path.startswith(_dir)

class GeneratorIdentification:
    '''
    Represents the identification of the generator
    with fields - location (repo_uri/package_path, id, version)
    '''
    def __init__(self):
        self.location = None
        self.id = None
        self.version = None
        self.is_remote = None
        
        self.package_dir = None

class Package:
    '''
    Represents a package that has been loaded.
    '''
    
    def __init__(self, path, loader,
                 uri=None, package_home=None, version=None):

        #: path on filesystem for this package
        self.path = path

        #: metadata about the package
        self.meta = None

        #: loader which loaded this package
        self.loader = loader

        #: classes of this package that have been
        # loaded (explicitly)
        self._classes = {}

        #: packages that this package depends on
        self._depends_on = set()

        #: packages that depend on this package
        self._depended_on = set()

        #: python modules loaded (from package dir)
        self._modules = {}

        #: has package been loaded
        self.is_loaded = False

        #: remote package (from repository) attributes

        #:   uri of repository
        self.uri = uri

        #:   package home id in repo
        self.package_home = package_home

        #:   version of package in repo
        self.version = version

    def __str__(self):
        return '<Package %s>' % self.path

    __repr__ = __str__

    def load(self):
        self.meta = get_package_metadata(self.path)
        for g in self.meta.generators:
            class_id = self.meta.id_map.get(g.class_id, g.class_id)
            _class = self.get_class(class_id)
            self._set_gen_ident(_class, class_id)

    def _set_gen_ident(self, _class, _id):
        ident = GeneratorIdentification()
        ident.location = self.uri if self.uri else self.path

        p = self.package_home
        ident.id = '.'.join([p, _id]) if p else _id

        ident.version = self.version
        ident.is_remote = self.is_remote_package()
        ident.package_dir = self.path

        _class.IDENT = ident

    def is_remote_package(self):
        return bool(self.uri)

    def get_class(self, _id):
        if _id in self._classes:
            return self._classes[_id]

        else:
            _class = self._load_class(_id)
            self._classes[_id] = _class
            return _class

    def get_module(self, _id):
        if _id in self._modules:
            return self._modules[_id]

        else:
            return self._load_module(_id)

    def _load_module(self, _id):
        global CUR_PACKAGE

        # restrict imports to allowed paths
        path = [self.path] + ALLOWED_PATHS
        orig_path = sys.path
        sys.path = path

        # track inter-package dependencies
        if CUR_PACKAGE:
            CUR_PACKAGE._depends_on.add(self.path)
            self._depended_on.add(CUR_PACKAGE.path)

        prev_package = CUR_PACKAGE
        CUR_PACKAGE = self

        sys_modules = sys.modules.copy()

        # add this package's modules to sys.modules
        sys.modules.update(self._modules)

        try:
            # start the import process
            _module = __import__(_id, fromlist=['*'])

        finally:
            sys.path = orig_path
            CUR_PACKAGE = prev_package

            # remove this package's modules from sys.modules
            for key in self._modules:
                if key in sys.modules:
                    del sys.modules[key]
       
        modules_before = set(sys_modules.keys())
        modules_after = set(sys.modules.keys())
        new_modules = modules_after - modules_before

        # move newly loaded package modules to _modules
        # from sys.modules
        for m in new_modules:
            module = sys.modules[m]

            if module is not None and hasattr(module, '__file__') and \
                not _is_in_dir(module.__file__, self.path):
                continue

            self._modules[m] = module
            del sys.modules[m]

        return _module

    def _load_class(self, _id):
        module_path, class_name = _id.rsplit('.', 1)
        module = self.get_module(module_path)
        _class = getattr(module, class_name)

        self._classes[_id] = _class
        return _class

    def reload(self):
        pass

    def unload(self):
        pass

class Loader:
    '''
    Manages loading, reloading and unloading of packages.
    '''

    def __init__(self):
        self.packages = {}

    def _clean_path(self, path):
        sep = os.path.sep
        return path if not path.endswith(sep) else path.rstrip(sep)

    def unload(self, package_path):
        p = self._clean_path(package_path)
        self.packages.pop(p).unload()

    def reload(self, package_path):
        p = self._clean_path(package_path)
        self.packages[p].reload()

    def get_package(self, package_path,
                    uri=None, package_home=None, version=None):
        p = self._clean_path(package_path)

        pkg = self.packages.get(p, None)
        if not pkg:
            pkg = Package(p, self,
                            uri=uri, package_home=package_home,
                            version=version)
            self.packages[p] = pkg
            pkg.load()

        return pkg

__loader__ = Loader()
LOADER = __loader__

def get_loader():
    return LOADER

def set_loader(new_loader):
    global LOADER
    old_loader = LOADER
    LOADER = new_loader
    return old_loader

def reset_to_default_loader():
    global LOADER
    LOADER = __loader__

# ---- Package Metadata ----

class RepositoryClass:
    def __init__(self):
        self._repo_class_info_ = {}

    @classmethod
    def set_repo_class_info(self, info):
        self._repo_class_info_ = info

    @classmethod
    def get_repo_class_info(self):
        return self._repo_class_info_

class _BaseInfo:
    def __init__(self):
        self.repository_uri = ''
        self.package_version = ''
        self.class_id = ''

    def get_xml_attrs(self, id_map={}):

        class_id = id_map.get(self.class_id, self.class_id)
        attrs = {'id': class_id}

        if self.repository_uri:
            attrs['repo'] = self.repository_uri

        if self.package_version:
            attrs['version'] = self.package_version

        return attrs

    def __repr__(self):
        if self.repository_uri:
            rep = ';'.join([self.class_id, self.repository_uri, self.version])
        else:
            rep = self.class_id

        cname = self.__class__.__name__
        return '<%s %s, parent=%s>' % (cname, rep, self.parents)

class _GeneratorInfo(_BaseInfo):
    '''
    Generator info gathered by
    introspecting a python code file.
    '''

    def __init__(self):
        self.title = ''
        self.description = ''
        self.module_id = ''
        self.gen_class = None

        self.config = []

        self.repository_uri = ''
        self.package_version = ''
        self.class_id = ''

        self.sub_generators = []
        self.parents = []
        self.categories = []

    def xmlize(self, node, id_map={}):
        # attrs
        gen = node.generator
        gen.attrs = self.get_xml_attrs(id_map)

        gen.title = self.title
        gen.description = self.description

        # categories
        for c in self.categories:
            gen.category.attrs = c.get_xml_attrs()

        # parents
        for p in self.parents:
            gen.parent.attrs = p.get_xml_attrs()

        # config
        config = gen.config
        for k, v in self.config:
            config.param.attrs = {'name': k, 'value': v}

        # sub generators
        for sgen in self.sub_generators:
            gen.sub_generator.attrs = sgen.get_xml_attrs()

def _is_child(_class, parent_class):
    return parent_class in _class.__bases__

def _get_relative_fpath(fpath, base):
    if not base:
        return fpath.lstrip(os.path.sep)

    return fpath.split(base, 1)[-1].lstrip(os.path.sep)

def _convert_fpath_to_import(fpath):
    _import = fpath.rsplit('.py', 1)[0]
    _import = _import.replace(os.path.sep, '.')
    return _import

def _get_class_id(_class):
    module_name = _class.__module__
    class_name = _class.__name__

    class_id = '%s.%s' % (module_name, class_name)
    return class_id

def _update_class_info(info, _class):
    if _is_child(_class, RepositoryClass):
        repo_info = _class.get_repo_class_info()
        info.repository_uri = repo_info['repository_uri']
        info.package_version = repo_info['package_version']
        info.class_id = repo_info['class_id']
    else:
        info.class_id = _get_class_id(_class)

def _get_generator_info(gen_class, module_id):
    gen_info = _GeneratorInfo()
    gen_info.class_id = _get_class_id(gen_class)
    gen_info.title = gen_class.TITLE
    gen_info.description = gen_class.DESCRIPTION
    gen_info.module_id = module_id
    gen_info.gen_class = gen_class

    # parents of generator
    parents = _get_parents(gen_class, Generator, _GeneratorInfo)
    gen_info.parents.extend(parents)

    # categories of generator
    categories = _get_categories(gen_class, _GeneratorInfo)
    gen_info.categories.extend(categories)

    # sub generators
    for sgen_name in gen_class.get_subgens():
        sgen = gen_class.get_sub_generator(sgen_name)
        sgen_info = _GeneratorInfo()
        _update_class_info(sgen_info, sgen)
        gen_info.sub_generators.append(sgen_info)

    # config
    gen_info.config = conf_info = gen_class.get_config()

    return gen_info

def _get_parents(_class, root_class, info_class):

    parents = []

    for base in _class.__bases__:
        if not issubclass(base, root_class):
            continue

        if base == root_class:
            continue

        if base == Category:
            continue

        if issubclass(base, Category):
            continue

        info = info_class()
        _update_class_info(info, base)
        parents.append(info)

    return parents

def _get_categories(_class, info_class):

    categories = []

    for ancestor in get_ancestors(_class):
        if not issubclass(ancestor, Category):
            continue

        if ancestor == Category:
            continue

        info = info_class()
        _update_class_info(info, ancestor)
        categories.append(info)

    return categories

@logfn
def get_file_info(fpath, package_dir, ignore_external=True):

    generators = []

    fpath = _get_relative_fpath(fpath, package_dir)
    _import = _convert_fpath_to_import(fpath)

    package = get_loader().get_package(package_dir)
    module = package.get_module(_import)

    module_name = module.__name__

    for name, obj in module.__dict__.iteritems():

        if not inspect.isclass(obj):
            continue

        # ignore classes from other repositories
        # they will be picked up as dependencies
        # only if used in a generator or sub-classed
        # by generator.
        if _is_child(obj, RepositoryClass):
            continue
        
        # ignore classes which have been imported
        # from other modules
        if ignore_external and obj.__module__ != module_name:
            continue
        
        if issubclass(obj, Generator):
            info = _get_generator_info(obj, _import)
            generators.append(info)
        
    return generators

def _collect_files(data, dirname, files):
    files = [os.path.join(dirname, f) for f in files if f.endswith('.py')]
    data.extend(files)

def _is_init_file(fpath):
    fname = os.path.basename(fpath)
    fname = fname.rsplit('.', 1)[0]
    return fname == '__init__'

def _make_id_map(generators):
    id_map = {}

    for g in generators:
        class_id = g.gen_class.__name__

        if '.' in g.module_id:
            to_class_id = g.module_id.rsplit('.')[0] + '.' + class_id
        else:
            to_class_id = class_id

        id_map[g.class_id] = to_class_id

    return id_map

class PackageMeta:
    '''
    Meta data extracted by introspecting a package.
    '''

    def __init__(self, from_cache=True):

        self.from_cache = from_cache

        self.title = None
        self.description = None
        self.version = None

        self.files = []
        self.generators = []

        self.id_map = {}

    def xmlize(self):
        '''
        @rtype: XMLNode
        @return: xml document
        '''
        package = XMLNode('package')
        package.attrs = {'title': self.title,
                         'version': self.version}
        package.description = self.description

        gens = package.generators
        for generator in self.generators:
            generator.xmlize(gens, self.id_map)

        return package

def _get_python_files(dirpath):
    files = []
    package_dir = os.path.abspath(dirpath)
    os.path.walk(dirpath, _collect_files, files)
    return files

@logfn
def get_package_metadata(package_dir, ignore_cache=False):
    '''
    Perform introspection on a package dir
    and return meta data. Also caches meta data so that
    future calls will be faster.

    @type package_dir: str
    @param package_dir: path to the directory which is the
        package_dir.

    @type ignore_cache: bool
    @param ignore_cache: If True, will ignore any package.xml
        found in package dir, even if it is up-to-date

    @rtype: PackageMeta
    @return: package meta data object
    '''

    if ignore_cache:
        files = _get_python_files(package_dir)
    else:
        files = []
        if is_package_meta_outdated(package_dir, files):
            # need to introspect; python files discovered in
            # above line will be used later below
            pass
        else:
            return parse_package_metadata(package_dir)
    
    title = os.path.split(package_dir.rstrip(os.path.sep))[-1]

    generators = []
    init_generators = []

    # process files and collect
    # information
    for fpath in files:
        is_init = _is_init_file(fpath)
        ignore_external = not is_init
        cur_generators = get_file_info(fpath, package_dir, ignore_external)

        gens = init_generators if is_init else generators
        gens.extend(cur_generators)

    id_map = _make_id_map(init_generators)

    meta = PackageMeta(from_cache=False)
    meta.title = title
    meta.files = files
    meta.generators = generators
    meta.id_map = id_map

    # preserve version and description from existing meta
    # if any
    old_meta = parse_package_metadata(package_dir)
    if old_meta:
        meta.version = old_meta.version
        meta.description = old_meta.description

    # cache new meta in package dir
    cache_package_metadata(meta, package_dir)

    return meta

@logfn
def cache_package_metadata(meta, package_dir, force=False):
    '''
    Serialize meta as xml and store in package.xml
    in package_dir.
    '''
    if meta.from_cache and not force:
        return

    fpath = os.path.join(package_dir, 'package.xml')
    f = open(fpath, 'w')
    
    xml_doc = meta.xmlize()
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    xml_doc.serialize(f)
    f.close()

@logfn
def parse_package_metadata(package_dir):
    '''
    Parse the metadata of a package captured
    in xml.
    '''

    fpath = os.path.join(package_dir, 'package.xml')
    if not os.path.exists(fpath):
        return None

    meta = PackageMeta()

    doc = etree.parse(fpath)
    package = doc.getroot()

    # FIXME: for now only some data is being parsed

    meta.version = package.get('version')
    meta.title = package.get('title')

    desc = package.find('description')
    meta.description = (desc.text or '').strip() if desc is not None else ''

    # parse generators
    gnodes = doc.findall('//generator')

    for g in gnodes:
        _id = g.get('id')
        g_info = _GeneratorInfo()
        g_info.class_id = _id

        # parse sub_generators
        sgnodes = g.findall('sub_generator')
        for sg in sgnodes:
            sg_info = _GeneratorInfo()
            _sgid = sg.get('id')
            sg_info.class_id = _sgid
            g_info.sub_generators.append(sg_info)
        
        meta.generators.append(g_info)

    return meta

def is_package_meta_outdated(package_dir, files=None):
    '''
    Checks if the package metadata stored
    in package.xml is outdated in comparison
    to the python files present.

    The comparison is done by modified time stamps
    of files found.
    '''
    
    _files = _get_python_files(package_dir)
    if isinstance(files, list):
        files.extend(_files)

    fpath = os.path.join(package_dir, 'package.xml')
    if not os.path.exists(fpath):
        # there is no package xml, so we can say
        # it amounts to metadata being "outdated"
        return True

    if not _files:
        # there are no files from which to extract
        # metadata, so it is as good as being up-to-date.
        return False

    pxml_mtime = os.path.getmtime(fpath)
    file_mtimes = [os.path.getmtime(f) for f in _files]

    return max(file_mtimes) > pxml_mtime


# ---- Repository Loader ----

class RepoImportError(Exception):
    pass

class Repository:
    '''
    Represents a repository for
    procedural modules.
    '''

    def __init__(self, uri, repos_cache=None):
        '''
        @type uri: str
        @param uri: repository location
            eg: http://www.example.com/repo

        @type repos_cache: str/None
        @param repos_cache: directory to
            store the modules downloaded
            from the repository. If not specified
            uses the global repos location.
            (get_repos_cache())
        '''
        self.uri = uri

        if not get_repos_cache() and repos_cache:
            set_repos_cache(repos_cache)

        self.cache = repos_cache or get_repos_cache()
        if not self.cache:
            raise RepositoryException('Repos location not known')

    def _get_package_dir(self, repo_dir, class_id):
        parts = class_id.split('.')

        path = repo_dir

        for index, p in enumerate(parts):
            path = os.path.join(path, p)

            pindic_fname = os.path.join(path, '__package__')
            if os.path.exists(pindic_fname):
                class_id = '.'.join(parts[index + 1:])
                return path, class_id

    def _choose_version_dir(self, package_dir, version):

        # get versions on disk
        version_dirs = get_package_versions(package_dir, True)

        if not version_dirs:
            return None

        # return most recent version
        unparse = unparse_version
        if not version:
            return os.path.join(package_dir, unparse(version_dirs[-1]))

        version = parse_version(version)
        if version not in version_dirs:
            return None

        else:
            return os.path.join(package_dir, unparse(version))

    def _parse_class_id(self, class_id):
        parts = class_id.split('.')
        return '.'.join(parts[:-1]), parts[-1]

    def _raise_import_error(self, class_id, package_version=None):
        if package_version:
            msg = 'version=%s not found for repo=%s, class_id=%s' % \
                        (package_version, self.uri, class_id)
        else:
            msg = 'repo=%s, class_id=%s' % (self.uri, class_id)
        raise RepoImportError(msg)

    def _get_package_id(self, gen_id, version):
        CLIENT.repo_uri = self.uri
        gen_id = gen_id + '-' + version if version is not None else gen_id
        generator = CLIENT.generator(gen_id)
        package_id = generator['package_id']
        package_id = package_id.rsplit('-', 1)[0] # remove version part
        return package_id

    def _download_package(self, class_id, package_version):
        zip_fpath = os.path.join(get_tmp_dir(), get_random_name())

        try:
            CLIENT.repo_uri = self.uri
            CLIENT.download(zip_fpath, class_id, package_version)
            
            repo_dirpath = self._get_repo_dir()
            package_id = self._get_package_id(class_id, package_version)
            package_home = '.'.join(package_id.split('.')[:-1])

            add_package(zip_fpath, package_home, repo_dirpath)

        finally:
            if os.path.exists(zip_fpath):
                os.remove(zip_fpath)

    def _get_repo_dir(self):
        repo_dirname = url_to_filename(self.uri)
        repo_dirpath = os.path.join(self.cache, repo_dirname)
        return repo_dirpath

    def get_version_dir(self, class_id, package_version=None):
        repo_dirpath = self._get_repo_dir()

        # find package dir from class_id
        # and adjust class_id to make sense
        # within scope of package dir
        data = self._get_package_dir(repo_dirpath, class_id)
        if not data:
            self._download_package(class_id, package_version)

        data = self._get_package_dir(repo_dirpath, class_id)
        if not data:
            self._raise_import_error(class_id)

        package_dir, pclass_id = data

        # choose version
        fn = self._choose_version_dir
        version_dir = fn(package_dir, package_version)
        if not version_dir:
            self._download_package(class_id, package_version)

        version_dir = fn(package_dir, package_version)
        if not version_dir:
            self._raise_import_error(class_id, package_version)

        return version_dir, data

    def get(self, class_id, package_version=None):
        '''
        @type class_id: str
        @param class_id: identifier for the
            class from the repository.
            eg: core.models.CityModel

        @type package_version: str/None
        @param package_version: version of the package
            from which to get class
            eg: '1.3' (version of 'core' package, say)

        @rtype: classobj
        @return: class representing a generator or model.
        '''
        version_dir, data = self.get_version_dir(class_id, package_version)

        package_dir, pclass_id = data

        package_home = class_id.rsplit(pclass_id, 1)[0]
        package = get_loader().get_package(version_dir, uri=self.uri,
                        package_home=package_home, version=package_version)
        _class = package.get_class(pclass_id)

        _class.__bases__ += (RepositoryClass,)

        _repo_class_info = {'class_id': class_id,
                            'package_version': package_version,
                            'repository_uri': self.uri}
        _class.set_repo_class_info(_repo_class_info)

        return _class

def is_location_remote(location):
    return location.strip().startswith('http')

def get_class(location, class_id, package_version=None, repos_cache=None):
    '''
    Get a class from a location (either repository or local package).

    @type location: str
    @param location: url of the repository

    @type class_id: str
    @param class_id: class identifier
        eg: core.models.city.Model

    @type package_version: None/str
    @param package_version: version of package
        from which to get the desired class.

    @type repos_cache: str/None
    @param repos_cache: directory to
        store the modules downloaded
        from the repository. If not specified
        uses the global repos location.
        (get_repos_cache())
    '''
    if is_location_remote(location):
        repo = Repository(location, repos_cache)
        _class = repo.get(class_id, package_version)
    else:
        package = get_loader().get_package(location)
        _class = package.get_class(class_id)

    return _class
