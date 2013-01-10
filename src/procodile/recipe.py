'''
Recipe abstraction (configurability)
G{importgraph}
'''

import os
import new
import copy
from pprint import pformat

from pyparsing import OneOrMore, Literal, Regex, Optional

from procodile.loader import get_class

PREDICATE_VARS = ['seed', 's_seed', 'depth', 'name', 'config', 'id']
PREDICATE_ARGS = ', '.join(['%s=None' % k for k in PREDICATE_VARS])

class XNode:
    ABSOLUTE = 0
    RELATIVE = 1

    def __init__(self, name, predicate, separator):
        self.name = name
        self._predicate = predicate
        self._separator = separator
        self.separator = self.ABSOLUTE if separator == '/' else self.RELATIVE
        self.predicate = None
        self.generator = None

        self._make_predicate_fn()

    def _make_predicate_fn(self):
        if self._predicate:
            fn = eval('lambda %s: %s' % (PREDICATE_ARGS,
                                        self._predicate))
        else:
            fn = lambda **kwargs: True

        self.predicate = fn

    def matches(self, gen_info, compare_with_parent=False):

        if self.name != '*':
            if compare_with_parent:
                if not issubclass(gen_info.generator, self.generator):
                    return False
            else:
                if self.generator != gen_info.generator:
                    return False

        kwargs = {}
        for attr in PREDICATE_VARS:
            kwargs[attr] = getattr(gen_info, attr)

        return self.predicate(**kwargs)

    def __str__(self):
        return "<XNode: %s, %s>" % (self.name, self._predicate)

    def __repr__(self):
        return str(self)

def make_xnode(s, loc, tokens):
    
    if len(tokens) == 3:
        sep, name, predicate = tokens
        predicate = predicate[1:-1]

    elif len(tokens) == 2:
        sep, name = tokens
        predicate = None

    xnode = XNode(name, predicate, sep)
    return xnode

def make_xnode_nosep(tokens):
    tokens.insert(0, '//')
    return make_xnode(None, None, tokens)

def make_xpath_parser():
    identifier = Regex('[A-Za-z_\.][A-Za-z_\.0-9]*')
    predicate = Regex('\[[^\]]*\]')
    node = (identifier | Literal('*')) + Optional(predicate)
    separator = Literal('//') | Literal('/')
    xpath_part = separator + node
    xpath_part.setParseAction(make_xnode)
    xpath = OneOrMore(xpath_part)
    xpath = node | xpath
    return xpath

XPATH_PARSER = make_xpath_parser()

def parse_xpath(xpath):
    '''
    >>> print parse_xpath('//bingo[hello/min//goblah]//moon/tingo[hmm]')
    [<XNode: bingo, hello/min//goblah>, <XNode: moon, None>, <XNode: tingo, hmm>]

    >>> print parse_xpath('//bingo/blah')
    [<XNode: bingo, None>, <XNode: blah, None>]

    >>> print parse_xpath('bingo["dingo == 10"]')
    [<XNode: bingo, "dingo == 10">]

    >>> print parse_xpath('bingo')
    [<XNode: bingo, None>]

    >>> print parse_xpath('*["dingo == 10"]')
    [<XNode: *, "dingo == 10">]
    '''
    result = XPATH_PARSER.parseString(xpath)
    if isinstance(result[0], (unicode, str)):
        result = [make_xnode_nosep(result)]
    return result

def match_xpath(xnodes, gen_info, root_info):

    xnode = xnodes[-1]
    xnodes = xnodes[:-1]

    # When a recipe is created by applying recipe config to a
    # generator, a sub-class of generator is created to represent
    # the recipe. However, the matches in the recipe trying to 
    # match the generator at root level will not work because of
    # this. The following is a special case handling to remedy that.
    compare_with_parent = (gen_info == root_info and \
                          issubclass(gen_info.generator,
                                     RecipeBasedGenerator))

    if not xnode.matches(gen_info, compare_with_parent):
        return False

    if xnode.separator == XNode.ABSOLUTE:

        parent = None if gen_info == root_info else gen_info.parent

        if parent and xnodes:
            return match_xpath(xnodes, parent.info, root_info)

        elif not parent and not xnodes:
            return True

        else:
            return False

    else:
        
        if not xnodes:
            return True

        ancestors = gen_info.parent.ancestors[:]
        ancestors = [g.info for g in ancestors]
        ancestors.insert(0, gen_info.parent.info)

        ancestors = [] if gen_info == root_info else ancestors

        for ancestor in ancestors:
            if match_xpath(xnodes, ancestor, root_info):
                return True

        return False

def rec_getattr(obj, attr):
    return reduce(getattr, attr.split('.'), obj)

def rec_setattr(obj, attr, value):
    # http://mousebender.wordpress.com/2006/11/10/recursive-getattrsetattr/
    attrs = attr.split('.')
    setattr(reduce(getattr, attrs[:-1], obj), attrs[-1], value)

class RecipeBasedGenerator:
    def _is_recipe_based_generator(self):
        pass

class RecipeConfig(object):

    RECIPE_TEMPLATE = '''\
# RECIPE 1.0
from procodile.recipe import RecipeConfig
import procodile.loader as loader

D = %(description)s

G = %(generators)s

M = %(matches)s

O = %(onmatches)s

data = {'description': D, 'generators': G, 'matches': M, 'onmatches': O}
recipe = RecipeConfig(__file__, loader.CUR_PACKAGE.path, data)
Generator = recipe.make_generator()
Generator.__module__ = __name__'''

    def __init__(self, *args):

        #: path of recipe on filesystem
        self.fpath = None

        #: absolute path for package dir
        self.package_dir = None

        # used fo generators introspection in configuration window
        self.version_dir = None

        parse_failed = False

        if len(args) == 0:
            self.data = {'description': '',
                         'generators': [],
                         'matches': [],
                         'onmatches': []}

        elif len(args) == 1:
            arg = args[0]

            if isinstance(arg, dict):
                self.data = arg

            else:
                parse_failed = True

        elif len(args) == 3:
            fpath, package_dir, self.data = args
            self.package_dir = self._clean_path(package_dir)
            self.fpath = self._compute_relative_fpath(fpath)
            self._make_paths_absolute()

        else:
            parse_failed = True

        if parse_failed:
            raise Exception('invalid arg')

        self._root_generator = None
        self._generators = {}
        self._matches = []
        self._onmatches = []

        self._match_actions = []

        self.parse_data()

    def _clean_path(self, path):
        sep = os.path.sep
        return path if not path.endswith(sep) else path.rstrip(sep)

    def _compute_relative_fpath(self, fpath):
        if not os.path.isabs(fpath):
            return fpath

        pdir = self.package_dir
        if not fpath.startswith(pdir):
            raise Exception('bad fpath and package_dir')
        
        fpath = os.path.relpath(fpath, pdir)
        return fpath

    def _get_generator(self):

        if not self.data['generators']:
            return None

        else:
            return self.data['generators'][0]

    def _set_generator(self, value):
        '''
        @type value: list
        @param value: [name, location, id, version]
        '''
        value = list(value)
        
        if len(value) == 3:
            value.append(None) # version

        generators = self.data['generators']

        if not generators:
            generators.append(value)

        else:
            generators[0] = value

    def _get_description(self):
        return self.data['description']

    def _set_description(self, desc):
        self.data['description'] = desc

    def _get_generators(self):
        return self.data['generators']

    def _get_matches(self):
        return self.data['matches']

    def _get_onmatches(self):
        return self.data['onmatches']

    generators = property(_get_generators)
    matches = property(_get_matches)
    onmatches = property(_get_onmatches)
    description = property(_get_description, _set_description)
    generator = property(_get_generator, _set_generator)

    def _get_item(self, space, name, skip_first=False):
        loc = -1
        items = self.data[space]

        for index, item in enumerate(items):
            if index == 0 and skip_first:
                continue

            if item[0] == name:
                loc = index
                break

        return loc

    def add_generator(self, name, location, _id, version=None):
        if self._get_item('generators', name) != -1:
            raise Exception('generator "%s" exists!' % name)

        self.generators.append([name, location, _id, version])
        return len(self.generators) - 1

    def del_generator(self, name):
        index = self._get_item('generators', name)

        if index == -1:
            raise Exception('generator "%s" not known' % name)

        else:
            self.generators.pop(index)

        return index

    def rename_generator(self, old_name, name):
        if self._get_item('generators', name) != -1:
            raise Exception('generator "%s" exists!' % name)

        index = self._get_item('generators', old_name)
        
        if index == -1:
            raise Exception('generator "%s" not known' % old_name)

        self.generators[index][0] = name
        return index

    def change_generator(self, name, location, _id, version=None):
        index = self._get_item('generators', name)
        
        if index == -1:
            raise Exception('generator "%s" not known' % name)

        self.generators[index] = [name, location, _id, version]
        return index

    def get_generator(self, name):
        index = self._get_item('generators', name)
        if index != -1:
            return self.generators[index]

    def add_match(self, name, conditions=None):
        if self._get_item('matches', name) != -1:
            raise Exception('match "%s" exists!' % name)

        if not conditions:
            conditions = []

        data = [name]
        data.extend(conditions)

        self.matches.append(data)
        return len(self.matches) - 1

    def del_match(self, name):
        index = self._get_item('matches', name)
        if index == -1:
            raise Exception('match "%s" not known' % name)

        self.matches.pop(index)
        return index

    def rename_match(self, old_name, name):
        if self._get_item('matches', name) != -1:
            raise Exception('match "%s" exists!' % name)

        index = self._get_item('matches', old_name)
        if index == -1:
            raise Exception('match "%s" unknown' % old_name)

        self.matches[index][0] = name
        return index

    def get_match(self, name):
        index = self._get_item('matches', name)
        if index != -1:
            return self.matches[index]

    def add_condition(self, match_name, condition):
        match = self.get_match(match_name)
        if not match:
            raise Exception('match "%s" not known' % match_name)

        if condition not in match[1:]:
            match.append(condition)

    def del_condition(self, match_name, condition):
        match = self.get_match(match_name)
        if not match:
            raise Exception('match "%s" not known' % match_name)

        if condition in match[1:]:
            match.remove(condition)

    def change_condition(self, match_name, old_condition, condition):
        match = self.get_match(match_name)
        if not match:
            raise Exception('match "%s" not known' % match_name)

        if old_condition in match[1:]:
            index = match.index(old_condition)

            if condition not in match[1:]:
                match[index] = condition
            else:
                raise Exception('match "%s" already has condition "%s"' % \
                            (match_name, condition))

        else:
            raise Exception('match "%s" does not have condition "%s"' % \
                        (match_name, old_condition))

    def add_onmatch(self, name, kv_pairs=None):
        if self._get_item('onmatches', name) != -1:
            raise Exception('onmatch "%s" exists!' % name)

        if not kv_pairs:
            kv_pairs = []

        data = [name]
        data.extend(kv_pairs)

        self.onmatches.append(data)
        return len(self.onmatches) - 1

    def del_onmatch(self, name):
        index = self._get_item('onmatches', name)
        if index == -1:
            raise Exception('onmatch "%s" not known' % name)

        self.onmatches.pop(index)
        return index

    def rename_onmatch(self, old_name, name):
        if self._get_item('onmatches', name) != -1:
            raise Exception('onmatch "%s" exists!' % name)

        index = self._get_item('onmatches', old_name)
        if index == -1:
            raise Exception('onmatch "%s" unknown' % old_name)

        self.onmatches[index][0] = name
        return index

    def get_onmatch(self, name):
        index = self._get_item('onmatches', name)
        if index != -1:
            return self.onmatches[index]

    def add_kv_pair(self, onmatch_name, key, value):
        onmatch = self.get_onmatch(onmatch_name)
        if not onmatch:
            raise Exception('onmatch "%s" not known' % onmatch_name)

        if [key, value] not in onmatch[1:]:
            onmatch.append([key, value])

    def del_kv_pair(self, onmatch_name, key, value):
        onmatch = self.get_onmatch(onmatch_name)
        if not onmatch:
            raise Exception('onmatch "%s" not known' % onmatch_name)

        if [key, value] in onmatch[1:]:
            onmatch.remove([key, value])

    def change_kv_pair(self, onmatch_name, old_kv, kv):
        onmatch = self.get_onmatch(onmatch_name)
        if not onmatch:
            raise Exception('onmatch "%s" not known' % onmatch_name)

        old_kv = list(old_kv)
        kv = list(kv)

        if old_kv in onmatch[1:]:
            index = onmatch.index(old_kv)

            if kv not in onmatch[1:]:
                onmatch[index] = kv
            else:
                raise Exception('onmatch "%s" already has kv "%s"' % \
                            (onmatch_name, kv))

        else:
            raise Exception('onmatch "%s" does not have kv "%s"' % \
                        (onmatch_name, old_kv))

    def _ensure_dirs(self, pdir, rdir):
        rdir_parts = rdir.split(os.path.sep)

        part_path = pdir
        for part in rdir_parts:
            part_path = os.path.join(part_path, part)
            if not os.path.exists(part_path):
                os.makedirs(part_path)
            init_fname = os.path.join(part_path, '__init__.py')
            if not os.path.exists(init_fname):
                open(init_fname, 'wb').write('')

    def _make_paths_absolute(self, generators=None):
        generators = generators or self.data['generators']
        for index, (name, location, _id, version) in enumerate(generators):
            if not location:
                generators[index] = [name, self.package_dir, _id, version]

    def _make_paths_relative(self, generators=None):
        generators = generators or self.data['generators']
        pdir = self._clean_path(self.package_dir)
        
        for index, (name, location, _id, version) in enumerate(generators):
            location = self._clean_path(location)
            if location == pdir:
                generators[index] = [name, '', _id, version]

    def save(self, package_dir=None, fpath=None):
        '''
        Save this recipe to a file.

        @type package_dir: str
        @param package_dir: location of package to which recipe
            should be saved.

        @type fpath: str
        @param fpath: location within package where to save the
            recipe.
        '''
        fpath = fpath or self.fpath
        pdir = package_dir or self.package_dir

        if not os.path.exists(pdir):
            os.makedirs(pdir)

        rdir = os.path.dirname(fpath)
        self._ensure_dirs(pdir, rdir)

        data = copy.deepcopy(self.data)
        self._make_paths_relative(data['generators'])

        if fpath.split('.')[-1] in ('.pyc', '.pyo'):
            fpath = fpath[:-1]

        path = os.path.join(pdir, fpath)
        o = open(path, 'w')
        data = dict([(k, pformat(v)) for k, v in data.iteritems()])
        code = self.RECIPE_TEMPLATE % data
        o.write(code)
        o.close()

        if not self.package_dir:
            self.package_dir = self._clean_path(pdir)
            self.fpath = fpath

    def update(self):
        self.parse_data()

    def parse_data(self, data=None):
        '''
        parse data and initialize self
        '''
        data = data or self.data
        if not data:
            return

        generators = data['generators']
        matches = data['matches']
        onmatches = data['onmatches']
        
        self._parse_generators(generators)
        self._parse_matches(matches)
        self._parse_onmatches(onmatches)

        self._create_match_actions()

    def _parse_generators(self, generators):
        self._generators = {}

        gen_names = set()

        for index, (name, location, _id, version) in enumerate(generators):

            if name in gen_names:
                raise Exception('duplicate generator name - "%s"' % name)
            else:
                gen_names.add(name)

            if index == 0:
                self._root_generator = name

            self._generators[name] = {'id': _id, 'location': location,
                                     'version': version}

    def _parse_matches(self, matches):
        self._matches = []
        
        match_names = set()

        for match in matches:

            name = match[0]
            conditions = list(match[1:])

            if name in match_names:
                raise Exception('duplicate name for match - "%s"' % name)
            else:
                match_names.add(name)

            self._matches.append((name, conditions))

    def _organize_key_values(self, key_values):
        '''
        Ensure that seed = value kind of actions,
        are moved to the beginning. This is required
        because changing seed results in config being re-computed.

        On re-computation any config changes done by action_fn
        will be lost. This can be prevented if all seed actions
        are moved to the beginning.
        '''

        seed_key_values = []
        
        for index, (key, value) in enumerate(key_values):
            if key == 'seed':
                seed_key_values.append((key, value))
                key_values[index] = None

        while None in key_values:
            key_values.remove(None)

        for index, kv in enumerate(seed_key_values):
            key_values.insert(index, kv)

        return key_values

    def _parse_onmatches(self, onmatches):
        self._onmatches = []

        onmatch_names = set()

        for onmatch in onmatches:
            
            match = onmatch[0]

            if match in onmatch_names:
                raise Exception('duplicate name for onmatch - "%s"' % match)
            else:
                onmatch_names.add(match)
        
            key_values = list(onmatch[1:])
            self._organize_key_values(key_values)
            self._onmatches.append((match, key_values))

    def _parse_action_value(self, key, value):
        try:
            if value:
                value = eval(value)
        except NameError:
            pass

        if key == 'generator':
            if not value:
                value = None
            else:
                value = self._generators[value]['generator']

        return value

    def _make_action_fn(self, actions):
        f = self._parse_action_value
        actions = [(k, f(k, v)) for k, v in actions]

        def action_fn(generator_info, action_cb):
            g = generator_info
            for k, v in actions:
                v = g.picker.pick(v)
                rec_setattr(g, k, v)
                action_cb(k, v)

        return action_fn

    def _parse_condition(self, condition):
        condition = parse_xpath(condition)

        for xnode in condition:
            gen_name = xnode.name
            generator = self._generators[gen_name]['generator']
            xnode.generator = generator

        return condition

    def _make_match_fn(self, conditions):

        def match_fn(generator_info, root_info):
            g = generator_info
            r = root_info

            for c in conditions:
                if match_xpath(c, g, r):
                    return True

            return False

        return match_fn

    def _load_generator(self, location, _id, version):
        location = location or self.package_dir
        generator = get_class(location, _id, version)
        return generator

    def make_matcher(self, conditions):

        if not isinstance(conditions, (list, tuple)):
            conditions = [conditions]

        parsed_conditions = []

        for c in conditions:
            c = self._parse_condition(c)
            parsed_conditions.append(c)

        match_fn = self._make_match_fn(parsed_conditions)

        return match_fn

    def _create_match_actions(self):

        self._match_actions = []

        for gen_name, g in self._generators.iteritems():
            _id, location, version = g['id'], g['location'], g['version']

            generator = self._load_generator(location, _id, version)
            g['generator'] = generator

        null_action = lambda g: None
        _match_actions = {}

        for match, conditions in self._matches:

            _match_actions[match] = {'match_fn': self.make_matcher(conditions),
                                     'action_fn': null_action}

        for onmatch, actions in self._onmatches:
            action_fn = self._make_action_fn(actions)
            _match_actions[onmatch]['action_fn'] = action_fn

        for match, conditions in self._matches:
            data = _match_actions[match]
            match_fn = data['match_fn']
            action_fn = data['action_fn']
            self._match_actions.append((match_fn, action_fn))

    def apply(self, gen_info, root_info, action_cb):
        '''
        Apply recipe config to gen_info.
        '''

        for match, action in self._match_actions:
            if match(gen_info, root_info):
                terminate = action(gen_info, action_cb)
                if terminate:
                    break

    def make_generator(self, name='Generator'):
        root_gen = self._generators[self._root_generator]['generator']
        _class = new.classobj(str(name), (root_gen, RecipeBasedGenerator), {})
        _class.add_recipe_config(self)
        return _class
