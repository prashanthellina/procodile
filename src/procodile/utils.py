'''
Misc utilities

G{importgraph}
'''

__version__ = "dev"

import os
import re
import sys
import copy
import inspect
import random
import string
import logging
import operator
import unicodedata
from math import fabs, sqrt, acos
import ctypes

import procodile.transformations as trans

ALPHANUM = string.letters + string.digits

log = logging.getLogger()

class ProcodileException(Exception):
    '''
    Generic Procodile Exception.
    '''
    pass

def create_logger(filename, log_level=logging.NOTSET, stderr=False):
    '''
    Make a logger that writes to I{filename}.

    @type filename: str
    @param filename: filename of file to which log has to be written

    @type log_level: logging.<log level>
    @param log_level: logging.[DEBUG, INFO, EXCEPTION, WARNING]

    @return: log object
    '''

    logger = logging.getLogger()
    handler = logging.FileHandler(filename)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if stderr:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(log_level)

    return logger

def restrict_value(value, min_value, max_value):
    '''
    Makes sure value is truncated to fit into
    allowed min-max range (inclusive).

    >>> restrict_value(10, 20, 30)
    20

    >>> restrict_value(40, 20, 30)
    30

    >>> restrict_value(25, 20, 30)
    25

    @type value: float/int/any object supporting comparison
    @param value:

    @type min_value: minimum value in the range
    @param min_value:

    @param max_value: maximum value in the range

    @return: truncated value
    '''
    if value < min_value:
        value = min_value
    elif value > max_value:
        value = max_value
    return value

def percent(value):
    '''
    Compute percentage of value.

    >>> fequals(percent(20), 0.20)
    True

    @type value: int
    @rtype: float
    '''
    return value/100.

def fequals(f1, f2, precision=1e-6):
    '''
    Checks for equality of floats with tolerance.

    >>> fequals(10.1, 10.100000000001)
    True

    >>> fequals(10.1, 10.11)
    False

    >>> fequals(0, 0)
    True

    @type f1: float
    @type f2: float
    @keyword precision: float
    '''
    _abs = fabs
    return _abs(f1-f2) <= _abs(f1) * precision

def fequals_sequence(t1, t2, precision=1e-6):
    '''
    Checks float equality for all floats in t1 and t2

    >>> fequals_sequence((1.0, 2.0), (1.0,))
    Traceback (most recent call last):
        assert(len(t1) == len(t2))
    AssertionError

    >>> fequals_sequence((1.0, 2.0), (1.0, 2.0))
    (True, True)

    >>> fequals_sequence((1.0, 2.0), (1.0, 2.1))
    (True, False)

    @type t1: sequence of float values
    @type t2: sequence of float values
    '''
    assert(len(t1) == len(t2))
    return tuple([fequals(t1[i], t2[i], precision) for i in range(len(t1))])

def true_fn(fn, *args):
    '''
    Call fn with args and returns True always.

    >>> true_fn(lambda x,y: False, 10, 20)
    True

    >>> true_fn(lambda x,y: 'A', 10, 20)
    True

    @type fn: callable
    @param fn:

    @param args: arguments to be passed to fn
    '''

    fn(*args)
    return True

def ignore(*args):
    '''
    Used for variables which are not used
    but must be present. This can help
    avoid pylint warnings.

    >>> ignore(10, 20)
    (10, 20)

    @type args: anything
    @param args:
    '''
    return args

def avg(items):
    '''
    Compute the average of the items.

    >>> avg([10, 20, 30, 50])
    27.5

    >>> fequals(avg([0.1, 0.2]), 0.15000000000000002)
    True

    @type items: sequence
    @param items:
    '''

    s = sum(items)
    l = len(items)

    return s / float(l)

def get_index(sequence, item):
    '''
    Gives the index of I{item} in I{sequence}.

    >>> get_index([1,2,3], 2)
    1

    >>> get_index([1,2,3], 4)

    @type sequence: sequence; list, tuple
    @param sequence: a sequence of items

    @type item: object
    @param item: a item to be searched for in sequence

    @rtype: item or None
    @return: int; If not present returns L{None}.
    '''
    try:
        return sequence.index(item)
    except ValueError:
        return None

def get_class_name(obj):
    '''
    Get the class name of an object.

    @type obj: python L{object}
    @param obj: object whose class name is required

    @rtype: str
    @return: name of the class
    '''
    return obj.__class__.__name__

def get_function_call_info():
    '''
    Get the function call information

    >>> def add(a, b):
    ...     print get_function_call_info()
    ...
    >>> add(10, 20)
    add: a=10, b=20
    '''

    stack = inspect.stack()
    callers_stack_frame_info = stack[1]
    frame = callers_stack_frame_info[0]

    fname = frame.f_code.co_name
    l = frame.f_locals
    l = ', '.join(['%s=%s' % (k, repr(v)) for k, v in l.iteritems()])
    return '%s: %s' % (fname, l)

def get_function_locals(*args):
    '''
    Get the callers locals.

    >>> def add(a, b):
    ...     print get_function_locals()
    ...     c = 10
    ...     print get_function_locals('a', 'c')
    ...
    >>> add(10, 20)
    {'a': 10, 'b': 20}
    {'a': 10, 'c': 10}

    @type args: list
    @param args: list of locals to return

    @rtype: dict
    @return: locals (after filtering if filter specified)
    '''

    stack = inspect.stack()
    callers_stack_frame_info = stack[1]
    frame = callers_stack_frame_info[0]

    l = frame.f_locals
    if args:
        l = dict([(k, v) for k, v in l.iteritems() if k in args])

    return l

def log_function_call(func, is_method=False):
    '''
    A decorator to help log function calls
    along with the arguments.
    '''

    def wfunc(*args, **kwargs):

        l_args = args

        s_kwargs = ''
        if kwargs:
            s_kwargs = ', ' + ', '.join(['%s=%s' % (k, repr(v)) \
                                for k, v in kwargs.iteritems()])

        self = ''
        if is_method:
            self = args[0]
            self = '(%x) %s.' % (id(self), self.__class__.__name__)
            l_args = args[1:]

        log.debug('%s%s: %s%s' % (self, func.func_name,
                                    repr(l_args), s_kwargs))
        return func(*args, **kwargs)

    return wfunc

def log_method_call(func):
    '''
    Decorator to help log method calls
    along with the arguments.
    '''
    return log_function_call(func, True)

def url_to_filename(url):
    '''
    Converts a url to a valid filename by
    replacing special characters with '_'.

    >>> url_to_filename("http://blog.prashanthellina.com/tag/wiki")
    'http___blog.prashanthellina.com_tag_wiki'

    >>> url_to_filename("http://www.example.com/cgi-bin/x?abc=10&t=p")
    'http___www.example.com_cgi-bin_x_abc_10_t_p'

    @type url: str/unicode
    @param url: url to be converted

    @rtype: str
    @return: filename
    '''

    if isinstance(url, str):
        url = url.decode('utf8', 'ignore')

    fname = unicodedata.normalize('NFKD', url).encode('ascii', 'ignore')
    fname = re.sub('[^A-Za-z0-9\-_\.]', '_', fname)

    return str(fname)

def _parse_options(*args, **kwargs):
    return args, kwargs

def parse_options(options, _globals=None):
    '''
    Parses options of the type,
        arg0, arg1, kwarg0=val0

    >>> parse_options('x=10, y=20')
    ((), {'y': 20, 'x': 10})
    >>> parse_options('40, x=10, y=20')
    ((40,), {'y': 20, 'x': 10})

    @type options: str
    @param options: options to be parsed

    @type _globals: dict
    @param _globals: namespace in which
        options are to be parsed

    @rtype: tuple
    @return: args(list), kwargs(dict)
    '''

    _globals = copy.copy(_globals) or {}
    _globals['_parse_options'] = _parse_options

    exec 'data = _parse_options(%s)' % options in _globals

    args, kwargs = _globals['data']
    return args, kwargs

class DotAccessDict(dict):
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

def get_ancestors(_class):
    '''
    Get all the ancestors of given class.
    '''

    ancestors = set()

    parents = _class.__bases__
    ancestors.update(parents)

    for p in parents:
        ancestors.update(get_ancestors(p))

    return ancestors

def get_tmp_dir():
    return 'C:\\' if sys.platform == 'win32' else '/tmp/'

def get_random_name(length=8):
    return ''.join([random.choice(ALPHANUM) for x in xrange(length)])

def get_win32_home():
    '''
    Get the path of user home directory in win32 platform.

    @rtype: unicode
    @return: path of home dir
    '''
    from ctypes import wintypes, windll

    CSIDL_APPDATA = 26

    _SHGetFolderPath = windll.shell32.SHGetFolderPathW
    _SHGetFolderPath.argtypes = [wintypes.HWND,
                                ctypes.c_int,
                                wintypes.HANDLE,
                                wintypes.DWORD, wintypes.LPCWSTR]

    path_buf = wintypes.create_unicode_buffer(wintypes.MAX_PATH)
    result = _SHGetFolderPath(0, CSIDL_APPDATA, 0, 0, path_buf)
    return path_buf.value

def get_user_app_dir(create=True):
    if sys.platform == 'win32':
        dirpath = os.path.join(get_win32_home(), 'procodile')
    else:
        dirpath = os.path.join(os.environ['HOME'], '.procodile')

    if not os.path.exists(dirpath) and create:
        os.makedirs(dirpath)

    return dirpath

html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    ">": "&gt;",
    "<": "&lt;",
    }

def escape_html(text):
    '''
    Produce entities within text.
    '''
    return ''.join(html_escape_table.get(c,c) for c in text)
    
class Matrix:
    '''
    4x4 Matrix abstraction for 3D transformations.
    All operations on matrix where appropriate are
    in-place unless mentioned otherwise.
    '''

    # AXES
    X = (1, 0, 0)
    Y = (0, 1, 0)
    Z = (0, 0, 1)

    def __init__(self, *args, **kwargs):
        '''
        Signature:
        *) Matrix
        *) translation, [rotation]
        *) (translation, rotation)
        *) tuple of 16 floats (row-major)
        *) list of 4 lists of 4 floats each (four rows)
        *) <no arguments> (unity matrix)
        '''
        translation = (0, 0, 0)
        rotation = (0, 0, 0)

        if args and isinstance(args[0], Matrix):
            self.matrix = args[0].matrix
            return

        if len(args) == 1:
            if len(args[0]) == 16:
                #TODO tuple of 16 floats (row-major)
                pass
            elif len(args[0]) == 4:
                self.matrix = args[0]
                return
            elif len(args[0]) == 3:
                translation = args[0]
            elif len(args[0]) == 2:
                translation, rotation = args[0]

        elif len(args) == 2:
            translation, rotation = args

        elif len(args) == 0:
            # Unity matrix
            pass

        else:
            raise Exception('invalid args: *args=%s, **kwargs=%s' %
                                    (args, kwargs))

        translation = kwargs.get('translation', translation)
        translation = trans.translation_matrix(translation)
        rotation = kwargs.get('rotation', rotation)
        rotation = self.get_rotation_matrix(rotation)

        self.matrix = trans.concatenate_matrices(translation, rotation)

    def _ensure_matrix(self, matrix):
        return matrix if isinstance(matrix, Matrix) else Matrix(matrix)

    def determinant(self):
        pass

    def inverse(self):
        '''
        Return inverse of this matrix.
        Does not modify in-place.
        '''
        matrix = trans.inverse_matrix(self.matrix)
        return Matrix(matrix)

    def invert(self):
        '''
        Inverts this matrix (in-place).
        '''
        self.matrix = trans.inverse_matrix(self.matrix)
        return self

    def multiply(self, matrix, inplace=False):

        matrix = self._ensure_matrix(matrix)
        matrix = trans.concatenate_matrices(self.matrix, matrix.matrix)

        if inplace:
            self.matrix = matrix
            return self

        else:
            matrix = Matrix(matrix)
            return matrix

    def concatenate(self, matrix):
        '''
        In-place.
        '''
        return self.multiply(matrix, True)

    def __mul__(self, matrix):
        return self.multiply(matrix)

    def __imul__(self, matrix):
        return self.concatenate(matrix)

    @classmethod
    def _get_type(self, value):
        if isinstance(value, (int, float)):
            return 'N'
        elif isinstance(value, (str, unicode)):
            return 'S'
        elif isinstance(value, (list, tuple)):
            return 'T'
        else:
            return 'O'

    @classmethod
    def get_rotation_matrix(self, rotation, wrap=False):
        rtype = [self._get_type(r) for r in rotation]

        if rtype == ['N', 'N', 'N', 'N']:
            matrix = trans.quaternion_matrix(rotation)

        elif rtype == ['N', 'N', 'N']:
            matrix = trans.euler_matrix(*rotation)

        elif rtype == ['N', 'N', 'N', 'S']:
            ai, aj, ak, axes = rotation
            matrix = trans.euler_matrix(ai, aj, ak, axes)

        elif rtype == ['N', 'T']:
            angle, direction = rotation
            matrix = trans.rotation_matrix(angle, direction)

        elif rtype == ['N', 'T', 'T']:
            angle, direction, point = rotation
            matrix = trans.rotation_matrix(angle, direction, point)

        else:
            raise Exception('invalid data for rotation: %s' % (rotation,))

        if wrap:
            return Matrix(matrix)
        else:
            return matrix

    def rotate(self, rotation, inplace=True):
        rmatrix = self.get_rotation_matrix(rotation, False)
        matrix = trans.concatenate_matrices(self.matrix, rmatrix)

        if inplace:
            self.matrix = matrix
            return self

        else:
            return Matrix(matrix)

    def rotate_x(self, angle, inplace=True):
        return self.rotate(angle, self.X, inplace)

    def rotate_y(self, angle, inplace=True):
        return self.rotate(angle, self.Y, inplace)

    def rotate_z(self, angle, inplace=True):
        return self.rotate(angle, self.Z, inplace)

    def scale(self, inplace=True):
        pass

    def transform(self):
        x, y, z = point
        point = (x, y, z, 1)

        point = numpy.dot(self.matrix, point)
        return tuple(point[:3])

    def equals(self, matrix):
        # TODO: check if this comparison works
        matrix = self._ensure_matrix(matrix)
        return self.matrix == matrix.matrix

    def __eq__(self, matrix):
        return self.equals(matrix)

    def __ne__(self, matrix):
        return not self.equals(matrix)

    def transpose(self, inplace=True):
        pass

    @classmethod
    def get_translation_matrix(self, translation, wrap=True):
        matrix = trans.translation_matrix(translation)

        if wrap:
            return Matrix(matrix)
        else:
            return matrix

    def translate(self, translation, inplace=True):
        tmatrix = self.get_translation_matrix(translation, False)
        matrix = trans.concatenate_matrices(self.matrix, tmatrix)

        if inplace:
            self.matrix = matrix
            return self

        else:
            return Matrix(matrix)

    def set_translation(self, inplace=True):
        pass

    def get_translation(self):
        return trans.translation_from_matrix(self.matrix)

    def set_scale(self, inplace=True):
        pass

    def get_scale(self):
        pass

    def set_rotation(self, inplace=True):
        pass

    def get_rotation(self):
        return trans.rotation_from_matrix(self.matrix)

    def get_formatted(self):
        tx, ty, tz = self.get_translation()

        angle, direction, point = self.get_orientation()
        point = tuple(point[:3])

        if angle == 0.0:
            o = 'None'

        else:
            all_true = lambda x, y: fequals_sequence(x, y) == (True, True, True)

            if all_true(direction, (1, 0, 0)):
                d = 'X'
            elif all_true(direction, (0, 1, 0)):
                d = 'Y'
            elif all_true(direction, (0, 0, 1)):
                d = 'Z'
            else:
                d = '%.3f, %.3f, %.3f' % direction

            if all_true(point, (0, 0, 0)):
                p = ''
            else:
                p = ' %.3f, %.3f, %.3f' % point

            o = '%.3f, %s' % (angle, d + p)
        
        return 'T=(%.3f, %.3f, %.3f), O=%s' % (tx, ty, tz, o)
        
class Vector:
    # http://code.google.com/p/pyeuclid/
    # http://pyeuclid.googlecode.com/svn/trunk/euclid.py
    __slots__ = ['x', 'y', 'z']

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __copy__(self):
        return self.__class__(self.x, self.y, self.z)

    def copy(self):
        return self.__copy__(self)

    def __repr__(self):
        return 'Vector(%.2f, %.2f, %.2f)' % (self.x,
                                              self.y,
                                              self.z)

    def __eq__(self, other):
        if isinstance(other, Vector):
            return self.x == other.x and \
                   self.y == other.y and \
                   self.z == other.z
        else:
            assert hasattr(other, '__len__') and len(other) == 3
            return self.x == other[0] and \
                   self.y == other[1] and \
                   self.z == other[2]

    def __neq__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return self.x != 0 or self.y != 0 or self.z != 0

    def __len__(self):
        return 3

    def __getitem__(self, key):
        return (self.x, self.y, self.z)[key]

    def __setitem__(self, key, value):
        l = [self.x, self.y, self.z]
        l[key] = value
        self.x, self.y, self.z = l

    def __iter__(self):
        return iter((self.x, self.y, self.z))

    def __getattr__(self, name):
        try:
            return tuple([(self.x, self.y, self.z)['xyz'.index(c)] \
                          for c in name])
        except ValueError:
            raise AttributeError, name

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x,
                          self.y + other.y,
                          self.z + other.z)
        else:
            assert hasattr(other, '__len__') and len(other) == 3
            return Vector(self.x + other[0],
                           self.y + other[1],
                           self.z + other[2])
    __radd__ = __add__

    def __iadd__(self, other):
        if isinstance(other, Vector):
            self.x += other.x
            self.y += other.y
            self.z += other.z
        else:
            self.x += other[0]
            self.y += other[1]
            self.z += other[2]
        return self

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x,
                           self.y - other.y,
                           self.z - other.z)
        else:
            assert hasattr(other, '__len__') and len(other) == 3
            return Vector(self.x - other[0],
                           self.y - other[1],
                           self.z - other[2])


    def __rsub__(self, other):
        if isinstance(other, Vector):
            return Vector(other.x - self.x,
                           other.y - self.y,
                           other.z - self.z)
        else:
            assert hasattr(other, '__len__') and len(other) == 3
            return Vector(other.x - self[0],
                           other.y - self[1],
                           other.z - self[2])

    def __mul__(self, other):
        if isinstance(other, Vector):
            # TODO component-wise mul/div in-place and on Vector2; docs.
            return Vector(self.x * other.x,
                          self.y * other.y,
                          self.z * other.z)
        else:
            assert type(other) in (int, long, float)
            return Vector(self.x * other,
                           self.y * other,
                           self.z * other)

    __rmul__ = __mul__

    def __imul__(self, other):
        assert type(other) in (int, long, float)
        self.x *= other
        self.y *= other
        self.z *= other
        return self

    def __div__(self, other):
        assert type(other) in (int, long, float)
        return Vector(operator.div(self.x, other),
                       operator.div(self.y, other),
                       operator.div(self.z, other))


    def __rdiv__(self, other):
        assert type(other) in (int, long, float)
        return Vector(operator.div(other, self.x),
                       operator.div(other, self.y),
                       operator.div(other, self.z))

    def __floordiv__(self, other):
        assert type(other) in (int, long, float)
        return Vector(operator.floordiv(self.x, other),
                       operator.floordiv(self.y, other),
                       operator.floordiv(self.z, other))


    def __rfloordiv__(self, other):
        assert type(other) in (int, long, float)
        return Vector(operator.floordiv(other, self.x),
                       operator.floordiv(other, self.y),
                       operator.floordiv(other, self.z))

    def __truediv__(self, other):
        assert type(other) in (int, long, float)
        return Vector(operator.truediv(self.x, other),
                       operator.truediv(self.y, other),
                       operator.truediv(self.z, other))


    def __rtruediv__(self, other):
        assert type(other) in (int, long, float)
        return Vector(operator.truediv(other, self.x),
                       operator.truediv(other, self.y),
                       operator.truediv(other, self.z))

    def __neg__(self):
        return Vector(-self.x,
                        -self.y,
                        -self.z)

    __pos__ = __copy__

    def __abs__(self):
        return sqrt(self.x ** 2 + \
                    self.y ** 2 + \
                    self.z ** 2)

    magnitude = __abs__

    def magnitude_squared(self):
        return self.x ** 2 + \
               self.y ** 2 + \
               self.z ** 2

    def normalize(self):
        d = self.magnitude()
        if d:
            self.x /= d
            self.y /= d
            self.z /= d
        return self

    def normalized(self):
        d = self.magnitude()
        if d:
            return Vector(self.x / d,
                           self.y / d,
                           self.z / d)
        return self.copy()

    def dot(self, other):
        assert isinstance(other, Vector)
        return self.x * other.x + \
               self.y * other.y + \
               self.z * other.z

    def cross(self, other):
        assert isinstance(other, Vector)
        return Vector(self.y * other.z - self.z * other.y,
                       -self.x * other.z + self.z * other.x,
                       self.x * other.y - self.y * other.x)

    def reflect(self, normal):
        # assume normal is normalized
        assert isinstance(normal, Vector)
        d = 2 * (self.x * normal.x + self.y * normal.y + self.z * normal.z)
        return Vector(self.x - d * normal.x,
                       self.y - d * normal.y,
                       self.z - d * normal.z)

    def rotation(self, vector):
        '''
        Get rotation matrix to go from A to B.
        '''
        a = self
        b = vector

        cos_theta = a.dot(b) / (a.magnitude() * b.magnitude())
        theta = acos(cos_theta)

        axis = a.cross(b)

        rotation_matrix = Matrix(rotation=(theta, axis))

        return rotation_matrix

def drange(start, stop, step, precision=1e-6):
    '''
    Works like xrange builtin but can handle decimals.

    >>> fequals_sequence(list(drange(0.5, 1.0, .1)), [.5, .6, .7, .8, .9])
    (True, True, True, True, True)
    '''

    r = start
    while not fequals(r, stop):
        yield r
        r += step
