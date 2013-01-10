'''
Drawing API

G{importgraph}
'''

import math
import operator

import gts

import procodile.transformations as trans
from procodile.utils import fequals_sequence

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
                #TODO list of 4 lists of 4 floats each (four rows)
                pass
            elif len(args[0]) == 3:
                translation = args[0]
            elif len(args[0]) == 2:
                translation, rotation = args[0]

        elif len(args) == 2:
            origin, orientation = args

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
        return math.sqrt(self.x ** 2 + \
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
        theta = math.acos(cos_theta)

        axis = a.cross(b)

        rotation_matrix = Matrix(rotation=(theta, axis))

        return rotation_matrix

def _get_bound_box(vertices):
    xvalues = (v.x for v in vertices)
    min_x = min(xvalues)
    max_x = max(xvalues)

    yvalues = (v.y for v in vertices)
    min_y = min(yvalues)
    max_y = max(yvalues)

    zvalues = (v.z for v in vertices)
    min_z = min(zvalues)
    max_z = max(zvalues)

    return (min_x, min_y, min_z,
            max_x, max_y, max_z)

class Geom:
    def __init__(self):
        #: geom belongs to which generator
        self.generator = None

        #: tags
        self.tags = []

        #: invisible geoms are not rendered
        self.visible = True

        #: underlying GTS object
        self._obj = None

        #: transformation matrix
        self.matrix = Matrix()

        #: operations matrix
        self.omatrix = Matrix()

    def get_position(self):
        return self.matrix.get_translation()

    def get_orientation(self):
        return self.matrix.get_rotation()

    def translate(self, translation):
        self.matrix.translate(translation)
        self.omatrix.translate(translation)
        return self

    def rotate(self, rotation):
        self.matrix.rotate(rotation)
        self.omatrix.rotate(rotation)
        return self

    def vertices(self):
        pass

    def get_bound_box(self):
        return _get_bound_box(self.vertices())

    def unwrap(self):
        return self._obj

    def set_obj(self, obj):
        self._obj = obj

    def get_obj(self):
        return self._obj

    def __repr__(self):
        return str(self)

class Vertex(Geom):
    def __init__(self, x=0, y=0, z=0):
        Geom.__init__(self)

        self.x = property(self._get_x. self_set_x)
        self.y = property(self._get_y. self_set_y)
        self.z = property(self._get_z. self_set_z)

        translation_matrix = Matrix(translation=(x, y, z))
        self.matrix.concatenate(translation_matrix)

    def _ensure_obj(self):
        if not self._obj:
            self._obj = gts.Vertex(0, 0, 0)

    def vertices(self):
        return (self,)

    def distance(self, vertex):
        x1, y1, z1 = self.get_translation()
        x2, y2, z2 = vertex.get_translation()

        d = (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2
        d = math.sqrt(d)

        return d

    def _get_x(self):
        return self.get_position()[0]

    def _set_x(self, value):
        self.translate((value, 0, 0))

    def _get_y(self):
        return self.get_position()[1]

    def _set_y(self, value):
        self.translate((0, value, 0))

    def _get_z(self):
        return self.get_position()[2]

    def _set_z(self, value):
        self.translate((0, 0, value))

    def __str__(self):
        x, y, z = self.get_position()
        return '<Vertex %s, %s, %s>' % (x, y, z)

class Edge(Geom):

    def __init__(self, *args):
        Geom.__init__(self)

        self.length = None
    
        if len(args) == 2:
            a1, a2 = args
            if isinstance(a1, Vertex):
                if isinstance(a2, Vertex):
                    self._init_from_vertices(a1, a2)
                elif isinstance(a2, (int, float)):
                    self._init_from_vertex_length(a1, a2)

        elif len(args) == 1:
            if isinstance(args[0], (int, float)):
                self._init_from_length(args[0])

        elif len(args) == 0:
            self.length = 0

        if self.length is None:
            raise Exception('unable to create edge: args = %s' % ((args,)))

        self.v1 = property(self._get_v1)
        self.v2 = property(self._get_v2)

    def _init_from_length(self, length):
        self.length = length

    def _init_from_vertex_length(self, v, length):
        self.length = length
        tx, ty, tz = v.x, v.y, v.z
        translation_matrix = Matrix(translation=(tx, ty, tz))
        self.matrix.concatenate(translation_matrix)
        
        if v._obj:
            v1, v2 = gts.Vertex(0, 0, 0), gts.Vertex(self.length, 0, 0)
            self._obj = gts.Edge(v1, v2)

    def _init_from_vertices(self, v1, v2):
        # http://stackoverflow.com/questions/286274/

        self.length = v1.distance(v2)

        a = Vector(self.length, 0, 0)
        tx, ty, tz = v1.x, v1.y, v1.z
        b = Vector(v2.x - tx, v2.y - ty, v2.z - tz)

        rot_matrix = a.rotation(b)
        self.matrix.concatenate(rot_matrix)
        translation_matrix = Matrix(translation=(tx, ty, tz))
        self.matrix.concatenate(translation_matrix)

    def _ensure_obj(self):
        if not self._obj:
            v1, v2 = gts.Vertex(0, 0, 0), gts.Vertex(self.length, 0, 0)
            self._obj = gts.Edge(v1, v2)

    def vertices(self):
        return (self.v1, self.v2)

    def _get_v1(self):
        v = Vertex()

        if self._obj:
            v.set_obj(self._obj.v1)

        v.matrix = self.matrix.multiply(v.matrix)
        return v
        
    def _get_v2(self):
        v = Vertex(self.length, 0, 0)

        if self._obj:
            v.set_obj(self._obj.v2)

        v.matrix = self.matrix.multiply(v.matrix)
        return v

    def __str__(self):
        return '<Edge %s %s>' % (self.v1, self.v2)

class Face(Geom):

    def __init__(self, e1, e2, e3):
        Geom.__init__(self)

        ue1, ue2, ue3 = e1.unwrap(), e2.unwrap(), e3.unwrap()
        self._obj = gts.Face(ue1, ue2, ue3)

        self.e1 = e1
        self.e2 = e2
        self.e3 = e3

    def __str__(self):
        return '<Face %s %s %s>' % (self.e1, self.e2, self.e3)

class Surface(Geom):

    def __init__(self, faces=[]):
        Geom.__init__(self)

        self._obj = gts.Surface()
        self.type = 'generic'

        if faces:
            for f in faces:
                f = f.unwrap()
                self._obj.add(f)

    def __str__(self):
        return '<Surface %s at %x>' % (self.type, id(self))

# Basic geometric primitives

class Sphere(Surface):
    
    def __init__(self, radius=1, lod=1):
        Surface.__init__(self)
        self.type = 'Sphere'

        self.radius = radius
        self.lod = lod

        s = gts.sphere(lod)
        s.scale(radius, radius, radius)
        self._obj = s

class Box(Surface):

     def __init__(self, lx, ly, lz):
        Surface.__init__(self)
        self.type = 'Box'

        self.lx = lx
        self.ly = ly
        self.lz = lz

        c = gts.cube()
        c.scale(lx, ly, lz)
        self._obj = c

class Circle(Surface):
    pass

class Ellipse(Surface):
    pass

class Cylinder(Surface):
    pass

class Cone(Surface):
    pass

class Tetrahedron(Surface):
    pass

class Pyramid(Surface):
    pass

class Torus(Surface):
    pass
