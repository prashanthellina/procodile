'''
Various geometry utilities.

G{importgraph}

NOTE: Please maintain this module in isolation from the
rest of the codebase as the intention is to spin this
off as a seperate project that can be open sourced.
'''

import operator
import random
from itertools import izip

DIR_UP = 'up'
DIR_DOWN = 'down'
DIR_LEFT = 'left'
DIR_RIGHT = 'right'

DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]

X_DIRECTIONS = [DIR_LEFT, DIR_RIGHT]
Y_DIRECTIONS = [DIR_DOWN, DIR_UP]

class GeometryException(Exception):
    '''Generic Geometry Exception'''

class InvalidData(GeometryException):
    '''Invalid/Bad data given'''

def is_odd(value):
    return value % 2 != 0

def is_even(value):
    return value % 2 == 0

class AxisAligned3DBox:
    '''
    Cuboid which is aligned to the axes.
    '''

    def __init__(self, point1, point2):
        '''
        @type point1: tuple of 3 float/ints.
        @type point2: tuple of 3 float/ints.
        '''
        self.point1 = point1
        self.point2 = point2

    def min_x(self):
        return min(self.point1[0], self.point2[0])

    def min_y(self):
        return min(self.point1[1], self.point2[1])

    def min_z(self):
        return min(self.point1[2], self.point2[2])

    def max_x(self):
        return max(self.point1[0], self.point2[0])

    def max_y(self):
        return max(self.point1[1], self.point2[1])

    def max_z(self):
        return max(self.point1[2], self.point2[2])

    def __str__(self):
        return 'AxisAligned3DBox(%s, %s)' % (self.point1, self.point2)

    def __repr__(self):
        return str(self)

class AxisAligned3DRectangle(AxisAligned3DBox):
    '''
    Rectangle in 3D space aligned to the axes.
    '''

    def __init__(self, point1, point2):
        '''
        @type point1: tuple of 3 float/ints.
        @type point2: tuple of 3 float/ints.
        '''
        AxisAligned3DBox.__init__(self, point1, point2)

        x1, y1, z1 = self.point1
        x2, y2, z2 = self.point2

        # Atleast the bounds one coordinate should be
        # same to make this a 3D rectangle.
        assert(x1 == x2 or y1 == y2 or z1 == z2)

    def __str__(self):
        return 'AxisAligned3DRectangle(%s, %s)' % (self.point1, self.point2)

    def __repr__(self):
        return str(self)

class AxisAligned2DRectangle:
    '''
    Rectangle in 2D space aligned to the axes.
    '''

    def __init__(self, point1, point2):
        '''
        @type point1: tuple of 2 float/ints.
        @type point2: tuple of 2 float/ints.
        '''

        self.point1 = point1
        self.point2 = point2

    def get_lines(self):
        '''
        Get the lines representing the sides.

        @rtype: list
        @return: list of L{AxisAligned2DLine}s
        '''

        x1, y1 = min(self.point1, self.point2)
        x2, y2 = max(self.point1, self.point2)

        lines = []
        lines.append(AxisAligned2DLine((x1, y1), (x1, y2)))
        lines.append(AxisAligned2DLine((x1, y1), (x2, y1)))
        lines.append(AxisAligned2DLine((x2, y2), (x1, y2)))
        lines.append(AxisAligned2DLine((x2, y2), (x2, y1)))

        return lines

    def is_touching(self, other):
        '''
        Check if rectangles are touching each other edge-wise.
        '''
        self_lines = set(self.get_lines())
        other_lines = set(other.get_lines())
        return bool(self_lines.intersection(other_lines))

    def max_x(self):
        return max(self.point1[0], self.point2[0])

    def max_y(self):
        return max(self.point1[1], self.point2[1])

    def min_x(self):
        return min(self.point1[0], self.point2[0])

    def min_y(self):
        return min(self.point1[1], self.point2[1])

    def has_point(self, point):
        x, y = point
        
        x1, x2 = self.min_x(), self.max_x()
        y1, y2 = self.min_y(), self.max_y()

        return x1 < x < x2 and y1 < y < y2

    def has_overlap(self, other):
        '''
        Check if this rectangle has overlap with I{other}
        rectangle.

        @type other: L{AxisAligned2DRectangle}
        @rtype: bool
        '''

        a = self
        b = other
    
        if (a.max_x() <= b.min_x()) or (a.min_x() >= b.max_x()):
            return False

        if (a.max_y() <= b.min_y()) or (a.min_y() >= b.max_y()):
            return False

        return True

    def _get_canonical_form(self):
        '''
        Computes standard representation for this rectangle.

        @rtype: tuple of tuple of 2 int/floats
        @return: (left-top point, right-bottom point)
        '''
        min_point = (self.min_x(), self.max_y())
        max_point = (self.max_x(), self.min_y())
        return (min_point, max_point)

    def __eq__(self, other):
        if other is None:
            return False

        fn1 = self._get_canonical_form
        fn2 = other._get_canonical_form

        eq = fn1() == fn2()
        return eq

    def get_bounding_box(self):
        '''
        Get axis aligned bounding box for this
        rectangle.

        @rtype: L{AxisAligned2DRectangle}
        '''
        return self

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        return cmp(self._get_canonical_form(),
                    other._get_canonical_form())

    def __hash__(self):
        return hash(self._get_canonical_form())

    def __str__(self):
        return 'AxisAligned2DRectangle(%s, %s)' % (self.point1, self.point2)

    def __repr__(self):
        return str(self)

class AxisAligned2DLine:
    '''
    Line in 2D space aligned to axes.
    '''

    def __init__(self, point1, point2):
        (x1, y1), (x2, y2) = point1, point2

        # ensure that line is axis aligned.
        assert((x1 == x2) or (y1 == y2))

        self.point1 = point1
        self.point2 = point2

    def is_horizontal(self):
        '''
        Is line aligned to X-axis?
        '''
        (x1, y1), (x2, y2) = self.point1, self.point2
        return y1 == y2

    def is_vertical(self):
        '''
        Is line aligned to Y-axis?
        '''
        (x1, y1), (x2, y2) = self.point1, self.point2
        return x1 == x2

    def get_offset(self):
        '''
        Get the offset from the axis to which
        this line is aligned. The offset will be
        distance from origin along X axis for
        vertical lines and distance along Y axis for
        horizontal lines.

        @rtype: int/float
        @return: distance from origin along aligned axis.
        '''
        if self.is_horizontal():
            return self.point1[1] # Y-value

        else:
            return self.point1[0] # X-value

    def get_bounds(self):
        '''
        Get the "range" of this line along the axis
        it is aligned to. For horizontal lines, the
        range will have two X values. For vertical
        lines, the range will have two Y values.

        @rtype: tuple of two int/floats
        @return: range of the line along its axis
        '''
        if self.is_horizontal():
            bounds = [self.point1[0], self.point2[0]]

        else:
            bounds = [self.point1[1], self.point2[1]]

        bounds.sort()
        return tuple(bounds)

    def get_other_endpoint(self, endpoint):
        '''
        Given an end point - I{point}, get the other
        end point of the line.

        @type endpoint: tuple of 2 int/floats
        @param endpoint: one endpoint of line
        '''

        if endpoint == self.point1:
            return self.point2

        elif endpoint == self.point2:
            return self.point1

        else:
            raise GeometryException('invalid endpoint %s for line %s' % \
                (endpoint, self))

    def split(self, offset):
        '''
        Split the line into two lines at I{offset}.

        @type offset: int/float
        @param offset: where to split the line
        '''
        
        (x1, y1), (x2, y2) = self.point1, self.point2

        if self.is_horizontal():
            if not in_range(offset, x1, x2, inclusive=False):
                return []

            line1 = AxisAligned2DLine((x1, y1), (offset, y1))
            line2 = AxisAligned2DLine((offset, y1), (x2, y1))

        else:

            if not in_range(offset, y1, y2, inclusive=False):
                return []

            line1 = AxisAligned2DLine((x1, y1), (x1, offset))
            line2 = AxisAligned2DLine((x1, offset), (x1, y2))

        return [line1, line2]

    def merge(self, line):
        '''
        Compute the merger of I{line} and this line.
        note: I{line} should be aligned with this line.
            Also this line is not modified as a result
            of this operation. A new merged line is 
            computed and returned.

        @type line: L{AxisAligned2DLine}
        @param line: line to be merged with this line

        @rtype: L{AxisAligned2DLine}
        @return: new merged line
        '''
        assert(self.is_horizontal() == line.is_horizontal())
        assert(self.get_offset() == line.get_offset())

        points = [line.point1, line.point2, self.point1, self.point2]

        merged_line = AxisAligned2DLine(min(points), max(points))

        return merged_line

    def get_intersection_point(self, line):
        '''
        Get the point where this line and I{line} intersect.
        For this test to make sense, the lines should
        have different alignment.
        
        @type line: L{AxisAligned2DLine}

        @rtype: tuple of 2 int/floats or None
        @return: point where the lines intersect or
            None when there is no intersection
        '''
        if line.is_horizontal() == self.is_horizontal():
            return None

        sb1, sb2 = self.get_bounds()
        lb1, lb2 = line.get_bounds()
        line_offset = line.get_offset()
        self_offset = self.get_offset()

        intersects = sb1 <= line_offset <= sb2 and lb1 <= self_offset <= lb2

        if intersects:
            if self.is_horizontal():
                return line_offset, self_offset
            else:
                return self_offset, line_offset

        return None

    def does_intersect(self, line):
        '''
        Does this line intersect I{line}?
        For this test to make sense, the lines should
        have different alignment.
        
        @type line: L{AxisAligned2DLine}

        @rtype: bool
        '''
        return bool(self.get_intersection_point(line))

    def has_overlap(self, line):
        '''
        Check if this line has overlap with I{line}.

        @type line: L{AxisAligned2DLine}

        @rtype: bool
        '''
        # For this test to make sense, the lines should
        # have the same alignment and offset.
        if not self.is_horizontal() == line.is_horizontal() or \
           not self.get_offset() == line.get_offset():
            return False

        start1, end1 = self.get_bounds()
        start2, end2 = line.get_bounds()

        if start1 < start2 and end1 <= start2:
            return False

        if start1 >= end2 and end1 > end2:
            return False
        
        return True

    def is_adjacent(self, line):
        '''
        Check if this line is adjacent to I{line}.
        
        @type line: L{AxisAligned2DLine}
        @rtype: bool
        '''
        points = set([self.point1, self.point2, line.point1, line.point2])

        has_overlap = False
        if line.is_horizontal() == self.is_horizontal():
            if self.has_overlap(line):
                has_overlap = True

        return len(points) == 3 and not has_overlap

    def symmetric_difference(self, line):
        '''
        Compute the symmetric difference between I{line}
        and this line.

        Symmetric Difference:
            Symmetric difference of sets A and B is the set
            whose members are members of exactly one of A and B.
            For instance, for the sets {1,2,3} and {2,3,4}, the
            symmetric difference set is {1,4}.
            (source: http://en.wikipedia.org/wiki/Set_theory)

        @type line: L{AxisAligned2DLine}

        @rtype: list
        @return: list of L{AxisAligned2DLine)s
        '''

        assert(self.is_horizontal() == line.is_horizontal())
        assert(self.get_offset() == line.get_offset())

        if not self.has_overlap(line):
            return [self, line]

        splits = []
        lines = [self.get_bounds(), line.get_bounds()]

        (start1, end1), (start2, end2) = lines

        if start2 < end1:
            if start1 != start2:
                splits.append((start1, start2))

            if end1 != end2:
                splits.append((end1, end2))

        lines = []
        o = self.get_offset()

        is_horizontal = self.is_horizontal()

        for b1, b2 in splits:

            if is_horizontal:
                line = AxisAligned2DLine((b1, o), (b2, o))
            else:
                line = AxisAligned2DLine((o, b1), (o, b2))

            lines.append(line)
        
        return lines

    def has_point(self, point):
        x, y = point
        b1, b2 = self.get_bounds()
        offset = self.get_offset()

        if self.is_horizontal():
            return y == offset and b1 <= x <= b2

        else:
            return x == offset and b1 <= y <= b2

    def is_equal(self, other):
        return self.__eq__(other)

    def __add__(self, line):
        return self.merge(line)

    def _get_canonical_form(self):
        '''
        Computes standard representation for this line.

        @rtype: tuple of tuple of 2 int/floats
        @return: (left/bottom point, right/top point)
        '''
        min_point = min(self.point1, self.point2)
        max_point = max(self.point1, self.point2)
        return (min_point, max_point)

    def __eq__(self, other):
        if other is None:
            return False

        fn1 = self._get_canonical_form
        fn2 = other._get_canonical_form

        eq = fn1() == fn2()
        return eq

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._get_canonical_form())

    def __str__(self):
        return 'AxisAligned2DLine(%s, %s)' % (self.point1, self.point2)

    def __repr__(self):
        return str(self)

class Polygon:
    '''
    A polygon in 2D space.
    '''

    def __init__(self, points, holes=None):
        '''
        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> poly = Polygon(points)
        >>> poly.points
        [(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), (0, 2)]
        >>> poly.holes
        []

        @type points: list of tuples
        @param points: where each tuple is (int/float, int/float)
            which is (x,y).

        @type holes: list of L{Polygon}s
        @param holes: holes in the polygon
        '''

        # Cannot form polygon without atleast 3 points
        assert(len(points) >=3 )

        if points[0] == points[-1]:
            points = points[:-1]

        self.points = points
        self.holes = holes or []

    def is_axis_aligned_rectangle(self):
        '''
        Is this polygon an axis-aligned rectangle?

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> poly = Polygon(points)
        >>> poly.is_axis_aligned_rectangle()
        False

        >>> points = [(0,0), (1,0), (1,1), (0,1)]
        >>> poly = Polygon(points)
        >>> poly.is_axis_aligned_rectangle()
        True

        @rtype: bool
        '''

        if len(self.points) != 4:
            return False

        points = set(self._get_bounding_box_points())

        if len(points.intersection(set(self.points))) == 4:
            return True
        else:
            return False

    def get_bounding_box(self):
        '''
        Get axis-aligned bounding box.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> poly = Polygon(points)
        >>> poly.get_bounding_box()
        AxisAligned2DRectangle((0, 2), (2, 0))

        @rtype: L{AxisAligned2DRectangle}
        @return: axis aligned bounding box
        '''

        bounding_points = self._get_bounding_box_points()
        point1 = bounding_points[0]
        point2 = bounding_points[-1]
        return AxisAligned2DRectangle(point1, point2)

    def get_lines(self):
        '''
        Get all the lines of this polygon.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> poly = Polygon(points)
        >>> poly.get_lines()
        [AxisAligned2DLine((0, 0), (1, 0)), AxisAligned2DLine((1, 0), (1, 1)), \
AxisAligned2DLine((1, 1), (2, 1)), AxisAligned2DLine((2, 1), (2, 2)), \
AxisAligned2DLine((2, 2), (0, 2)), AxisAligned2DLine((0, 2), (0, 0))]

        @rtype: list of L{AxisAligned2DLine}
        '''

        prev_point = None
        lines = []

        if not self.points:
            return lines

        for point in self.points:

            if prev_point is None:
                prev_point = point
                continue

            lines.append(AxisAligned2DLine(prev_point, point))
            prev_point = point

        # line from last point to first point
        lines.append(AxisAligned2DLine(prev_point, self.points[0]))

        return lines

    def _get_bounding_box_points(self):
        '''
        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> poly = Polygon(points)
        >>> poly._get_bounding_box_points()
        [(0, 2), (0, 0), (2, 2), (2, 0)]
        '''

        xvalues = [p[0] for p in self.points]
        yvalues = [p[1] for p in self.points]
        min_x = min(xvalues)
        max_x = max(xvalues)
        min_y = min(yvalues)
        max_y = max(yvalues)

        points = [(min_x, max_y), (min_x, min_y),
                 (max_x, max_y), (max_x, min_y)]

        return points

    def __eq__(self, other):
        return self.points == other.points

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(tuple(self.points))

    def __str__(self):
        return 'Polygon(points=%s, holes=%s)' % (self.points, self.holes)

    def __repr__(self):
        return str(self)

class OrthogonalPolygon(Polygon):
    '''
    A polygon in 2D space where internal angles
    are either 90 or 270 degrees.
    '''

    class SplitData:
        '''
        Data needed for identifying the
        rectangles which cover this polygon.
        '''

        def __init__(self, polygon):
            '''
            >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
            >>> ortho_poly = OrthogonalPolygon(points)
            >>> data = ortho_poly.SplitData(ortho_poly)

            >>> sorted(data.xvalues.items())
            [(0, [AxisAligned2DLine((0, 0), (1, 0)), \
AxisAligned2DLine((2, 2), (0, 2))]), \
(1, [AxisAligned2DLine((0, 0), (1, 0)), AxisAligned2DLine((1, 1), (2, 1)), \
AxisAligned2DLine((2, 2), (0, 2))]), \
(2, [AxisAligned2DLine((1, 1), (2, 1)), AxisAligned2DLine((2, 2), (0, 2))])]

            >>> sorted(data.yvalues.items())
            [(0, [AxisAligned2DLine((1, 0), (1, 1)), \
AxisAligned2DLine((0, 2), (0, 0))]), \
(1, [AxisAligned2DLine((1, 0), (1, 1)), AxisAligned2DLine((2, 1), (2, 2)), \
AxisAligned2DLine((0, 2), (0, 0))]), \
(2, [AxisAligned2DLine((2, 1), (2, 2)), AxisAligned2DLine((0, 2), (0, 0))])]

            >>> sorted(data.points.items())
            [((0, 0), set([AxisAligned2DLine((0, 0), (1, 0)), AxisAligned2DLine\
((0, 2), (0, 0))])), \
((0, 2), set([AxisAligned2DLine((2, 2), (0, 2)), \
AxisAligned2DLine((0, 2), (0, 0))])), \
((1, 0), set([AxisAligned2DLine((0, 0), (1, 0)), \
AxisAligned2DLine((1, 0), (1, 1))])), \
((1, 1), set([AxisAligned2DLine((1, 1), (2, 1)), \
AxisAligned2DLine((1, 0), (1, 1))])), \
((2, 1), set([AxisAligned2DLine((1, 1), (2, 1)), \
AxisAligned2DLine((2, 1), (2, 2))])), \
((2, 2), set([AxisAligned2DLine((2, 2), (0, 2)), \
AxisAligned2DLine((2, 1), (2, 2))]))]
            '''

            self.xvalues = xvalues = {} #: horizontal lines
            self.yvalues = yvalues = {} #: vertical lines
            self.points = {}            #: points to lines map
            self.lines = polygon.get_lines()
            self.hole_intercept_points = []

            lines = []

            for x, y in polygon.points:
                xvalues[x] = []
                yvalues[y] = []

            for line in self.lines:
                lines.append(line)

            # add hole information too.
            for hole in polygon.holes:
                self.hole_intercept_points = hole.get_points(90)

                for x, y in self.hole_intercept_points:
                    xvalues[x] = []
                    yvalues[y] = []

                for line in hole.get_lines():
                    lines.append(line)

            for line in lines:
                self.add_line(line)

        def add_line(self, line):
            '''
            Add I{line}.

            >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
            >>> ortho_poly = OrthogonalPolygon(points)
            >>> data = ortho_poly.SplitData(ortho_poly)

            >>> line = AxisAligned2DLine((0,0), (10,0))
            >>> data.add_line(line)
            >>> data.xvalues[0]
            [AxisAligned2DLine((0, 0), (1, 0)), \
AxisAligned2DLine((2, 2), (0, 2)), AxisAligned2DLine((0, 0), (10, 0))]

            >>> line = AxisAligned2DLine((0,0), (0,10))
            >>> data.add_line(line)
            >>> data.yvalues[0]
            [AxisAligned2DLine((1, 0), (1, 1)), \
AxisAligned2DLine((0, 2), (0, 0)), AxisAligned2DLine((0, 0), (0, 10))]
            '''

            (x1, y1), (x2, y2) = line.point1, line.point2

            self.points.setdefault((x1, y1), set()).add(line)
            self.points.setdefault((x2, y2), set()).add(line)

            if line.is_vertical():
                for y in self.yvalues:
                    if in_range(y, y1, y2):
                        self.yvalues[y].append(line)

            else:
                for x in self.xvalues:
                    if in_range(x, x1, x2):
                        self.xvalues[x].append(line)

        def remove_line(self, line):
            '''
            Remove I{line}.

            >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
            >>> ortho_poly = OrthogonalPolygon(points)
            >>> data = ortho_poly.SplitData(ortho_poly)

            >>> line = AxisAligned2DLine((0,0), (1,0))
            >>> data.remove_line(line)
            >>> data.xvalues[0]
            [AxisAligned2DLine((2, 2), (0, 2))]

            >>> line = AxisAligned2DLine((1,0), (1,1))
            >>> data.remove_line(line)
            >>> data.yvalues[0]
            [AxisAligned2DLine((0, 2), (0, 0))]
            '''

            (x1, y1), (x2, y2) = p1, p2 = line.point1, line.point2

            self.points[p1].remove(line)
            if not self.points[p1]:
                del self.points[p1]

            self.points[p2].remove(line)
            if not self.points[p2]:
                del self.points[p2]

            if line.is_vertical():
                for y in self.yvalues:
                    if in_range(y, y1, y2):
                        self.yvalues[y].remove(line)

            else:
                for x in self.xvalues:
                    if in_range(x, x1, x2):
                        self.xvalues[x].remove(line)

        def split_line(self, line, offset):
            '''
            Split I{line} at I{offset}.

            >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
            >>> ortho_poly = OrthogonalPolygon(points)
            >>> data = ortho_poly.SplitData(ortho_poly)

            >>> data.xvalues[0]
            [AxisAligned2DLine((0, 0), (1, 0)), AxisAligned2DLine((2, 2), (0, 2))]

            >>> line = AxisAligned2DLine((2, 2), (0, 2))
            >>> offset = 1
            >>> data.split_line(line, offset)

            >>> data.xvalues[0]
            [AxisAligned2DLine((0, 0), (1, 0)), AxisAligned2DLine((1, 2), (0, 2))]
            '''

            splits = line.split(offset)
            if not splits:
                return

            for split in splits:
                self.add_line(split)

            self.remove_line(line)

        def get_line_with_endpoints(self, epoint1, epoint2):
            '''
            Get a line with endpoints I{epoint1} and I{epoint2}.

            >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
            >>> ortho_poly = OrthogonalPolygon(points)
            >>> data = ortho_poly.SplitData(ortho_poly)

            >>> data.get_line_with_endpoints((0, 0), (1, 0))
            AxisAligned2DLine((0, 0), (1, 0))
            '''

            lines1 = self.points.get(epoint1, set())
            lines2 = self.points.get(epoint2, set())

            lines = lines1.intersection(lines2)

            if lines:
                return lines.pop()

    def __init__(self, points, holes=None):
        '''
        >>> points = [(0,0), (1,0), (1,1), (-2,1), (-2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        Traceback (most recent call last):
            raise InvalidData('sides intersect: %s' % (self.points,))
        InvalidData: sides intersect: [(0, 0), (1, 0), (1, 1), \
(-2, 1), (-2, 2), (0, 2)]

        @type points: list of tuples
        @param points: where each tuple is (int/float, int/float)
            which is (x,y).

        @type holes: list of L{Polygon}s
        @param holes: holes in the polygon
        '''
        Polygon.__init__(self, points, holes)

        if self._do_sides_intersect():
            raise InvalidData('sides intersect: %s' % (self.points,))

    def is_point_inside(self, point):
        '''
        Check whether I{point} is inside this polygon.
        (Point in Polygon test using Raycasting and checking
        if number of intersections are even/odd -
        http://en.wikipedia.org/wiki/Point_in_polygon).

        Note that when the point is on the boundary
        of the polygon, it is considered to be outside.

        >>> p = OrthogonalPolygon(((0,0), (10, 0), (10, 10), (0, 10)))

        >>> on_boundary_points = [(0, 0), (10, 0), (10, 10),
        ...                       (0, 10), (5, 0), (0, 5),
        ...                       (10, 5), (5, 10)]

        >>> inside_points = [(5, 5), (9, 2)]
        >>> outside_points = [(11, 11), (-1, 5), (15, 6), (-5, 10)]

        >>> [p.is_point_inside(point) for point in on_boundary_points]
        [False, False, False, False, False, False, False, False]

        >>> [p.is_point_inside(point) for point in inside_points]
        [True, True]

        >>> [p.is_point_inside(point) for point in outside_points]
        [False, False, False, False]

        @type point: tuple of 2 int/floats.
        @param point: point which is being checked

        @rtype: bool
        @return: True if point is inside
        '''
        lines = self.get_lines()
        bbox = self.get_bounding_box()

        if not bbox.has_point(point):
            return False

        # check if point is on boundary
        for line in lines:
            if line.has_point(point):
                return False

        # compute horizontal line beginning from
        # point and intersecting the bounding box
        # on the right hand side. If this line (ray)
        # intersects the sides of the polygon
        # odd number of times, then point is
        # inside polygon.
        x1, y1 = point

        # compute end point of ray
        # note: 1 is being added because the ray
        # will not pass the intersection test
        # with vertical line with x = x2 otherwise.
        x2 = bbox.max_x() + 1
        y2 = y1
        ray = AxisAligned2DLine((x1, y1), (x2, y2))

        intersect_count = 0

        for line in lines:
            if line.is_horizontal():
                continue

            ipoint = ray.get_intersection_point(line)
            if not ipoint:
                continue

            if ipoint in (line.point1, line.point2):
                # endpoint intersection
                # consider this intersection only if
                # other end of line is below ray
                ix, iy = line.get_other_endpoint(ipoint)
                if iy < y1:
                    intersect_count += 1
            else:
                # non endpoint intersection
                intersect_count += 1

        if not intersect_count:
            return False

        if is_even(intersect_count):
            return False

        else:
            return True

    def split(self):
        '''
        Decomposes this polygon into rectangles.

        Limitations:
            - No two points in this polygon can have the
              same coordinates.
            - Holes should be rectangular.
        '''

        # prepare datastructures
        data = self.SplitData(self)

        # generate intercepts from polygon points
        # and split lines that are intercepted.
        # the intercepts are generated only from
        # polygon points where the internal angle
        # is 270 degrees. In addition intercepts
        # are also generated from points on hole
        # polygons which have an internal angle of
        # 90 degrees.
        # FIXME: currently hole is not being handled
        # properly.
        ignore_points = set()
        intercept_points = self.get_points(270)
        intercept_points.extend(data.hole_intercept_points)

        for point in intercept_points:

            if point in ignore_points:
                continue

            intercept_line = self._intercept(point, data)

            if not intercept_line:
                continue

            endpoint = intercept_line.get_other_endpoint(point)
            ignore_points.add(endpoint)
        
        # Get all the split rectangles from the split data
        rectangles = self._get_rectangles(data)

        return rectangles
       
    def _get_rectangles(self, data):
        '''
        identify all rectangles formed by lines
        in L{data}.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> data = ortho_poly.SplitData(ortho_poly)

        >>> ortho_poly._get_rectangles(data)
        set([])

        >>> data = ortho_poly.SplitData(ortho_poly)

        >>> ortho_poly._intercept((1, 1), data)
        AxisAligned2DLine((1, 1), (1, 2))
        >>> sorted(ortho_poly._get_rectangles(data))
        [AxisAligned2DRectangle((0, 0), (1, 2)), \
AxisAligned2DRectangle((1, 2), (2, 1))]

        @type data: L{SplitData}

        @rtype: list of L{AxisAligned2DRectangle}s
        '''

        rectangles = set()
        for point in data.points.keys():
            fn = self._get_rectangles_around_point
            cur_rectangles = fn(point, data)
            rectangles.update(cur_rectangles)

            # remove the lines from data
            # so that they do not get considered
            # again
            for line in list(data.points.get(point, [])):
                data.remove_line(line)

        # remove rectangles representing holes
        hole_rectangles = [h.get_bounding_box() for h in self.holes]
        hole_rectangles = set(hole_rectangles)

        rectangles = rectangles - hole_rectangles

        return rectangles

    def _do_sides_intersect(self):
        '''
        Check if the sides of this polygon
        intersect each other.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> ortho_poly._do_sides_intersect()
        False

        >>> points = [(0,0), (1,0), (1,1), (-2,1), (-2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        Traceback (most recent call last):
            raise InvalidData('sides intersect: %s' % (self.points,))
        InvalidData: sides intersect: [(0, 0), (1, 0), (1, 1), \
(-2, 1), (-2, 2), (0, 2)]
        '''

        horizontal = True
        vertical = not horizontal

        lines = {horizontal: [], vertical: []}

        for line in self.get_lines():
            lines[line.is_horizontal()].append(line)

        for hline in lines[horizontal]:
            for vline in lines[vertical]:
                if hline.does_intersect(vline) and \
                    not hline.is_adjacent(vline):
                    return True

        return False
        
    def _get_rectangles_around_point(self, point, data):
        '''
        Get the rectangles around I{point}.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> data = ortho_poly.SplitData(ortho_poly)

        >>> ortho_poly._get_rectangles_around_point((1, 1), data)
        []

        >>> ortho_poly._intercept((1, 1), data)
        AxisAligned2DLine((1, 1), (1, 2))
        >>> ortho_poly._get_rectangles_around_point((1, 1), data)
        [AxisAligned2DRectangle((1, 1), (2, 2))]

        @type point: tuple of 2 int/floats.
        @type data: L{SplitData}

        @rtype: list
        @return: list of L{AxisAligned2DRectangle}s
        '''

        # get lines with point as endpoint
        lines = data.points.get(point)
        if not lines:
            return []

        horizontals = {}
        verticals = {}

        # segregate lines and key by the other
        # end point of lines
        for line in lines:

            endpoint = line.get_other_endpoint(point)

            if line.is_horizontal():
                horizontals[endpoint] = line
            else:
                verticals[endpoint] = line

        # collect rectangles
        rectangles = []

        for h_endpoint, hline in horizontals.iteritems():
            for v_endpoint, vline in verticals.iteritems():

                # point is one endpoint of the diagonal of a possible
                # rectangle. common_point is the other end of that
                # diagonal.
                common_point = h_endpoint[0], v_endpoint[1]

                fn = data.get_line_with_endpoints
                hline = fn(v_endpoint, common_point)
                vline = fn(h_endpoint, common_point)

                if hline and vline:
                    min_point = min(point, common_point)
                    max_point = max(point, common_point)
                    rectangle = AxisAligned2DRectangle(min_point, max_point)
                    rectangles.append(rectangle)

        return rectangles

    def _get_avoidable_directions(self, point, data):
        '''
        Get the directions in which an intercept line
        cannot be drawn because of presence of lines
        already.

        @type point: tuple of 2 int/floats
        @param point: point from which intercept line
            is going to start off

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> data = ortho_poly.SplitData(ortho_poly)

        >>> ortho_poly._get_avoidable_directions((0, 0), data)
        {'right': AxisAligned2DLine((0, 0), (1, 0)), 'up': AxisAligned2DLine((0,\
 2), (0, 0))}

        @type data: L{SplitData}

        @rtype: dict
        @return: direction -> line mapping
        '''

        avoid_directions = {}

        lines = data.points[point]
        x, y = point

        for line in lines:
            x1, y1 = line.get_other_endpoint(point)

            if line.is_horizontal():
                if x > x1:
                    avoid_directions[DIR_LEFT] = line
                else:
                    avoid_directions[DIR_RIGHT] = line

            else:
                if y > y1:
                    avoid_directions[DIR_DOWN] = line
                else:
                    avoid_directions[DIR_UP] = line

        return avoid_directions

    def _get_line_intercept(self, point, direction, data):
        '''
        Generate an intercept line starting from I{point} in
        I{direction}.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> data = ortho_poly.SplitData(ortho_poly)

        >>> ortho_poly._get_line_intercept((0, 0), DIR_LEFT, data)
        >>> ortho_poly._get_line_intercept((0, 0), DIR_UP, data)
        (0, AxisAligned2DLine((2, 2), (0, 2)))
        >>> ortho_poly._get_line_intercept((1, 1), DIR_UP, data)
        (1, AxisAligned2DLine((2, 2), (0, 2)))

        @type point: tuple of 2 int/floats
        @param point: point from which intercept line
            is going to start off

        @type direction: str
        @param direction: DIR_LEFT, DIR_RIGHT, DIR_UP, DIR_DOWN

        @type data: L{SplitData}
        '''

        x, y = point
        verticals = data.yvalues
        horizontals = data.xvalues
        lt = operator.lt
        gt = operator.gt

        if direction == DIR_LEFT:
            params = y, verticals, x, lt

        elif direction == DIR_RIGHT:
            params = y, verticals, x, gt

        elif direction == DIR_UP:
            params = x, horizontals, y, gt

        elif direction == DIR_DOWN:
            params = x, horizontals, y, lt

        else:
            raise GeometryException('invalid direction: %s' % direction)

        intercept, linespace, offset, comp = params
        lines = linespace[intercept]

        # pick line closest to point
        lines = [(abs(offset - l.get_offset()), l) for l in lines \
                    if comp(l.get_offset(), offset)]

        if not lines:
            return None

        lines.sort()
        difference, line = lines[0]

        return intercept, line

    def _get_point_in_direction(self, point, direction, ends_at):
        '''
        Given I{point} from which to start a line and
        a I{direction} and at where it I{ends_at}, compute
        the end point.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)

        >>> ortho_poly._get_point_in_direction((1, 1), DIR_UP, 2)
        (1, 2)
        >>> ortho_poly._get_point_in_direction((1, 1), DIR_UP, 3)
        (1, 3)
        >>> ortho_poly._get_point_in_direction((1, 1), DIR_LEFT, 0)
        (0, 1)

        @type point: tuple of 2 int/floats
        @param point: point from which line
            is going to start off

        @type direction: str
        @param direction: DIR_LEFT, DIR_RIGHT, DIR_UP, DIR_DOWN

        @type ends_at: int/float
        @param ends_at: for horizontal direction, indicates
            x value of endpoint. for vertical direction, indicates
            y value of endpoint.

        @rtype: tuple of 2 int/floats
        @return: end point
        '''
        
        x, y = point

        if direction in (DIR_LEFT, DIR_RIGHT):
            endpoint = ends_at, y

        elif direction in (DIR_UP, DIR_DOWN):
            endpoint = x, ends_at

        return endpoint

    def _get_adjacent_colinear_lines(self, line, point, data):
        '''
        Get lines which are colinear to I{line} but do not
        overlap it (i.e adjacent to it) and having
        I{point} common.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> data = ortho_poly.SplitData(ortho_poly)

        >>> intercept_line = ortho_poly._intercept((1, 1), data)
        >>> ortho_poly._get_adjacent_colinear_lines(intercept_line, (1, 1), data)
        [AxisAligned2DLine((1, 0), (1, 1))]

        @type line: L{AxisAligned2DLine}
        @param line: line for which colinear lines need
            to be found.

        @type point: tuple of 2 int/floats
        @param point: point common to line and colinear lines

        @type data: L{SplitData}

        @rtype: list of L{AxisAligned2DLine}s
        @return: list of colinear lines to I{line} at I{point}
        '''

        all_lines = data.points[point]
        ac_lines = [] #: adjacent-colinear lines

        for _line in all_lines:
            same_slope = line.is_horizontal() == _line.is_horizontal()
            no_overlap = not line.has_overlap(_line)

            if same_slope and no_overlap:
                ac_lines.append(_line)

        return ac_lines

    def _get_extension_lines(self, line, data):
        '''
        Find lines which are colinear and adjacent
        to I{line} and compute all combinations
        of merged lines.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> data = ortho_poly.SplitData(ortho_poly)
        >>> intercept_line = AxisAligned2DLine((1, 1), (1, 2))
        >>> ortho_poly._get_extension_lines(intercept_line, data)
        Traceback (most recent call last):
          avoid_directions[DIR_DOWN] = line
        KeyError: (1, 2)

        >>> intercept_line = ortho_poly._intercept((1, 1), data)
        >>> ortho_poly._get_extension_lines(intercept_line, data)
        [AxisAligned2DLine((1, 0), (1, 2))]

        @type line: L{AxisAligned2DLine}
        @param line: line for which merged adjacent-colinear
            lines need to be computed.
        
        @type data: L{SplitData}

        @rtype: list of L{AxisAligned2DLine}s
        @return: all combinations of merged lines
            involving I{line} and its adjacent-colinear lines
        '''

        lines = []

        start_point = line.point1
        end_point = line.point2

        fn = self._get_adjacent_colinear_lines
        opposite_lines = fn(line, start_point, data)
        forward_lines = fn(line, end_point, data)

        # opposite adjacent-colinear lines merged
        # with line
        for index, oline in enumerate(opposite_lines):
            oline = oline + line
            opposite_lines[index] = oline
            lines.append(oline)

        # forward adjacent-colinear lines merged with
        # line
        for index, fline in enumerate(forward_lines):
            fline = fline + line
            lines.append(fline)

        # opposite merged lines merged with forward lines
        # in all combinations
        for oline in opposite_lines:
            for fline in forward_lines:
                lines.append(oline + fline)

        return lines

    def _intercept(self, point, data):
        '''
        Generate an intercept line starting from I{point}.

        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> data = ortho_poly.SplitData(ortho_poly)
        >>> ortho_poly._intercept((1, 1), data)
        AxisAligned2DLine((1, 1), (1, 2))

        @type point: tuple of 2 int/floats
        @param point: point from which intercept line
            is going to start off

        @type data: L{SplitData}

        @rtype: None/L{AxisAligned2DLine}
        @return: intercepting line
        '''

        avoid_directions = self._get_avoidable_directions(point, data)
        intercepting_line = None

        for direction in DIRECTIONS:

            if direction in avoid_directions:
                continue

            line_intercept = self._get_line_intercept(point, direction, data)
            if not line_intercept:
                continue

            intercept, line = line_intercept

            fn = self._get_point_in_direction
            endpoint = fn(point, direction, line.get_offset())

            fn = self._use_intercept_line
            intercepting_line = fn(point, endpoint, line, intercept, data)
            break

        return intercepting_line

    def _use_intercept_line(self, start_point, end_point,
                            line, intercept, data):
        '''
        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> data = ortho_poly.SplitData(ortho_poly)
        >>> intercept, line = ortho_poly._get_line_intercept((1, 1), DIR_UP, data)
        >>> ortho_poly._use_intercept_line((1, 1), (1, 2), line, intercept, data)
        AxisAligned2DLine((1, 1), (1, 2))
        '''

        data.split_line(line, intercept)

        intercepting_line = AxisAligned2DLine(start_point, end_point)
        data.add_line(intercepting_line)

        extension_lines = []

        fn = self._get_extension_lines
        extension_lines = fn(intercepting_line, data)

        for line in extension_lines:
            data.add_line(line)

        return intercepting_line

    def _get_angles(self, a, b, c):
        '''
        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> ortho_poly._get_angles((0, 0), (1, 0), (1, 1))
        (90, 270)
        '''

        ax, ay = a
        bx, by = b
        cx, cy = c

        if ax == bx ==cx or ay == by == cy:
            return 180, 180

        if ax == bx:
            if ay > by:
                if cx > bx:     # down - right
                    return 90, 270
                elif bx > cx:   # down - left
                    return 270, 90 
            elif by > ay:
                if cx > bx:     # up - right
                    return 270, 90
                elif bx > cx:   # up - left
                    return 90, 270
        elif ay == by:
            if bx > ax:
                if cy > by:     # right - up
                    return 90, 270
                elif by > cy:   # right - down
                    return 270, 90
            elif ax > bx:
                if cy > by:     # left - up
                    return 270, 90
                elif by > cy:   # left - down
                    return 90, 270

        if not angles:
            raise GeometryException('invalid data a=%s, b=%s, c=%s' % \
                                    (a, b, c))

        return angles

    def get_internal_angles(self):
        '''
        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> ortho_poly.get_internal_angles()
        [90, 90, 270, 90, 90, 90]
        '''

        points = self.points[:]
        points = [points[-1]] + points + [points[0]]

        left_angles = []
        right_angles = []

        for index in xrange(len(self.points)):   
            a = points[index]
            b = points[index + 1]
            c = points[index + 2]

            left, right = self._get_angles(a, b, c)
            left_angles.append(left)
            right_angles.append(right)

        # the sum of all interior angles is always lesser
        # than the sum of all exterior angles. we use this
        # property to choose the internal angles.
        angles = [(sum(angles), angles) for angles in \
                        (left_angles, right_angles)] 
        _sum, angles = min(angles)
        return angles

    def get_points(self, internal_angle):
        '''
        >>> points = [(0,0), (1,0), (1,1), (2,1), (2,2), (0,2)]
        >>> ortho_poly = OrthogonalPolygon(points)
        >>> ortho_poly.get_points(270)
        [(1, 1)]
        '''

        points = []

        angles = self.get_internal_angles()
        for point, angle in izip(self.points, angles):
            if angle == internal_angle:
                points.append(point)
        
        return points

    def __str__(self):
        return 'OrthogonalPolygon(points=%s, holes=%s)' % \
            (self.points, self.holes)

    def __repr__(self):
        return str(self)

def in_range(value, a, b, inclusive=True):
    '''
    Check if I{value} is in range (a,b).

    @type value: comparable (int, float etc)
    @param value: value to be checked

    @type a: comparable (int, float etc)
    @param value: one bound of range

    @type b: comparable (int, float etc)
    @param value: another bound of range

    @type inclusive: bool
    @param inclusive: if True, then range
        checking will consider a and b values
        to be a part of the range.

    @rtype: bool
    @return: True if value in range of a,b
    '''
    a, b = min(a, b), max(a, b)

    if inclusive:
        b = b + 1
    else:
        a = a + 1
    
    return value in xrange(a, b)

def do_boxes_intersect(box1, box2):
    '''
    Checks if axis-aligned boxes, I{box1} and I{box2} intersect.

    @type box1: L{AxisAligned3DBox}
    @type box2: L{AxisAligned3DBox}

    @rtype: bool
    @return: True if the boxes intersect else False
    '''
    a = box1
    b = box2

    if (a.max_x() < b.min_x()) or (a.min_x() > b.max_x()):
        return False

    if (a.max_y() < b.min_y()) or (a.min_y() > b.max_y()):
        return False

    if (a.max_z() < b.min_z()) or (a.min_z() > b.max_z()):
        return False

    return True

def _split_rectangle(rectangle, x1, y1, x2, y2):
    r = rectangle

    xvalues = []
    xvalues.append(r.point1[0])
    xvalues.append(r.point2[0])

    if in_range(x1, r.min_x(), r.max_x(), inclusive=False):
        xvalues.append(x1)

    if in_range(x2, r.min_x(), r.max_x(), inclusive=False):
        xvalues.append(x2)

    yvalues = []
    yvalues.append(r.point1[1])
    yvalues.append(r.point2[1])

    if in_range(y1, r.min_y(), r.max_y(), inclusive=False):
        yvalues.append(y1)

    if in_range(y2, r.min_y(), r.max_y(), inclusive=False):
        yvalues.append(y2)

    xvalues.sort()
    yvalues.sort()
    yvalues.reverse()

    splits = set()

    for x in xrange(len(xvalues) - 1):
        for y in xrange(len(yvalues) - 1):
            x1, y1 = xvalues[x], yvalues[y]
            x2, y2 = xvalues[x + 1], yvalues[y + 1]
            r = AxisAligned2DRectangle((x1, y1), (x2, y2))
            splits.add(r)

    return splits

def split_overlapping_rectangles(rectangle1, rectangle2):
    '''
    Splits overlapping rectangles into smaller rectangles
    along overlap boundaries. Also finds overlapping
    rectangle.

    @type rectangle1: L{AxisAligned2DRectangle}
    @type rectangle2: L{AxisAligned2DRectangle}

    @rtype: (L{AxisAligned2DRectangle}, list)
    @return: (overlapping sub-rectangle, list of
        smaller split rectangles)
    '''

    a = rectangle1
    b = rectangle2

    # split rectangles
    (x1, y1), (x2, y2) = b.point1, b.point2
    a_splits = _split_rectangle(a, x1, y1, x2, y2)

    (x1, y1), (x2, y2) = a.point1, a.point2
    b_splits = _split_rectangle(b, x1, y1, x2, y2)

    # identify overlap rectangle
    overlap_rect = a_splits.intersection(b_splits)
    if not overlap_rect:
        raise GeometryException('rectangles %s and %s do not overlap' % (a, b))

    # all splits
    splits = list(a_splits.union(b_splits) - overlap_rect)
    overlap_rect = list(overlap_rect)[0]

    return overlap_rect, splits

class RectangleMerger:
    '''
    Merges axis-aligned rectangles to form
    orthogonal polygon(s).
    '''
    
    class MergeData:
        '''
        Data need for merging rectangles.
        '''

        def __init__(self, rectangles):
            '''
            >>> rect1 = AxisAligned2DRectangle((0, 0), (1, 2))
            >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))
            >>> rm = RectangleMerger()
            >>> data = rm.MergeData([rect1, rect2])

            >>> sorted(data.horizontals.items())
            [(0, [AxisAligned2DLine((0, 0), (1, 0))]), \
(1, [AxisAligned2DLine((2, 1), (1, 1))]), \
(2, [AxisAligned2DLine((1, 2), (0, 2)), \
AxisAligned2DLine((1, 2), (2, 2))])]

            >>> sorted(data.verticals.items())
            [(0, [AxisAligned2DLine((0, 0), (0, 2))]), \
(1, [AxisAligned2DLine((1, 2), (1, 0)), \
AxisAligned2DLine((1, 2), (1, 1))]), \
(2, [AxisAligned2DLine((2, 1), (2, 2))])]

            @type rectangles: list
            @param rectangles: list of L{AxisAligned2DRectangle}s
            '''

            # get lines from rectangles
            lines = []
            for r in rectangles:
                lines.extend(r.get_lines())

            #: horizontal lines indexed by line offset
            self.horizontals = horizontals = {}

            #: vertical lines indexed by line offset
            self.verticals = verticals = {}

            for line in lines:
                space = horizontals if line.is_horizontal() else verticals
                offset = line.get_offset()
                space.setdefault(offset, []).append(line)

            self.points = {}

            # for polygon-hole pairing
            self.parents = {}
            self.children = {}

        def prepare_points(self):
            '''
            Create a point -> lines map where
            each point can have at max two lines,
            one horizontal and one vertical.

            >>> rect1 = AxisAligned2DRectangle((0, 0), (1, 2))
            >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))
            >>> rm = RectangleMerger()
            >>> data = rm.MergeData([rect1, rect2])

            >>> data.points
            {}

            >>> data.prepare_points()
            >>> sorted(data.points.items())
            [((0, 0), {'H': AxisAligned2DLine((0, 0), (1, 0)), \
'V': AxisAligned2DLine((0, 0), (0, 2))}), \
((0, 2), {'H': AxisAligned2DLine((1, 2), (0, 2)), \
'V': AxisAligned2DLine((0, 0), (0, 2))}), \
((1, 0), {'H': AxisAligned2DLine((0, 0), (1, 0)), \
'V': AxisAligned2DLine((1, 2), (1, 0))}), \
((1, 1), {'H': AxisAligned2DLine((2, 1), (1, 1)), \
'V': AxisAligned2DLine((1, 2), (1, 1))}), \
((1, 2), {'H': AxisAligned2DLine((1, 2), (2, 2)), \
'V': AxisAligned2DLine((1, 2), (1, 1))}), \
((2, 1), {'H': AxisAligned2DLine((2, 1), (1, 1)), \
'V': AxisAligned2DLine((2, 1), (2, 2))}), \
((2, 2), {'H': AxisAligned2DLine((1, 2), (2, 2)), \
'V': AxisAligned2DLine((2, 1), (2, 2))})]
            '''
            
            self.points.clear()

            for space, key in ((self.horizontals, 'H'), (self.verticals, 'V')):
                for lines in space.itervalues():
                    for line in lines:
                        point1, point2 = line.point1, line.point2
                        self.points.setdefault(point1, {})[key] = line
                        self.points.setdefault(point2, {})[key] = line

        def remove_points(self, points):
            '''
            Remove I{points} from data.

            >>> rect1 = AxisAligned2DRectangle((0, 0), (1, 2))
            >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))
            >>> rm = RectangleMerger()
            >>> data = rm.MergeData([rect1, rect2])
            >>> data.prepare_points()

            >>> data.remove_points([(0, 1), (1, 0)])
            Traceback (most recent call last):
                del self.points[p]
            KeyError: (0, 1)

            >>> data.remove_points([(0, 0), (0, 2)])
            #check that the points are removed from the merge data
            >>> sorted(data.points.items())
            [((1, 0), {'H': AxisAligned2DLine((0, 0), (1, 0)), \
'V': AxisAligned2DLine((1, 2), (1, 0))}), \
((1, 1), {'H': AxisAligned2DLine((2, 1), (1, 1)), \
'V': AxisAligned2DLine((1, 2), (1, 1))}), \
((1, 2), {'H': AxisAligned2DLine((1, 2), \
(2, 2)), 'V': AxisAligned2DLine((1, 2), (1, 1))}), \
((2, 1), {'H': AxisAligned2DLine((2, 1), (1, 1)), \
'V': AxisAligned2DLine((2, 1), (2, 2))}), ((2, 2), \
{'H': AxisAligned2DLine((1, 2), (2, 2)), \
'V': AxisAligned2DLine((2, 1), (2, 2))})]

            @type points: list of tuples
            @param points: tuple has 2 int/floats
            '''
            for p in points:
                del self.points[p]

        def remove_lines(self, lines):
            '''
            >>> rect1 = AxisAligned2DRectangle((0, 0), (1, 2))
            >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))
            >>> rm = RectangleMerger()
            >>> data = rm.MergeData([rect1, rect2])

            >>> line = data.horizontals[0]
            >>> data.remove_lines(line)
            >>> line = data.horizontals[0]
            Traceback (most recent call last):
            KeyError: 0

            >>> data.horizontals
            {1: [AxisAligned2DLine((2, 1), (1, 1))], \
2: [AxisAligned2DLine((1, 2), (0, 2)), AxisAligned2DLine((1, 2), (2, 2))]}

            @type lines: list of L{AxisAligned2DLine}s
            @param lines: lines that need to be removed
            '''

            horizontal = True
            vertical = not horizontal

            spaces = {horizontal: self.horizontals,
                      vertical: self.verticals}

            for line in lines:
                space = line.is_horizontal()
                offset = line.get_offset()

                o_lines = spaces[space][offset]
                o_lines.remove(line)
                if not o_lines:
                    del spaces[space][offset]

    def _simplify_colinear_lines(self, lines, data):
        '''
        Merges adjacent co-linear lines and removes
        overlapping regions of co-linear lines.

        >>> rect1 = AxisAligned2DRectangle((0, 0), (1, 2))
        >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))
        >>> rm = RectangleMerger()
        >>> data = rm.MergeData([rect1, rect2])

        >>> data.horizontals[2]
        [AxisAligned2DLine((1, 2), (0, 2)), AxisAligned2DLine((1, 2), (2, 2))]
        >>> rm._simplify_colinear_lines(data.horizontals[2], data)
        [AxisAligned2DLine((0, 2), (2, 2))]

        >>> rm._simplify_colinear_lines(data.horizontals[3], data)
        Traceback (most recent call last):
        KeyError: 3
        
        @type lines: list of L{AxisAligned2DLine}s
        @param lines: lines that are co-linear

        @data: L{MergeData}

        @rtype: list of L{AxisAligned2DLine}s
        @return: list of merged L{AxisAligned2DLine}s
        '''

        # sort in order of bounds
        lines = [(x.get_bounds(), x) for x in lines]
        lines.sort()
        lines = [x[1] for x in lines]

        for i in xrange(len(lines) - 1):

            cur_line = lines[i]
            next_line = lines[i + 1]

            if None in (cur_line, next_line):
                continue

            if cur_line.is_adjacent(next_line):
                merged_line = cur_line.merge(next_line)
                lines[i] = None
                lines[i + 1] = merged_line

            elif cur_line.has_overlap(next_line):
                splits = cur_line.symmetric_difference(next_line)

                # pad splits with None items to ensure it has
                # two items
                splits = [None] * (2 - len(splits)) + splits

                lines[i], lines[i + 1] = splits

        lines = [x for x in lines if x is not None]
        return lines

    def _choose_start_point(self, data):
        '''
        Choose the "start" point. This point
        can be used as the beginning point from
        which the polygon's perimeter can be
        traversed in an anti-clockwise direction.

        >>> rect1 = AxisAligned2DRectangle((0, 0), (1, 2))
        >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))
        >>> rm = RectangleMerger()
        >>> data = rm.MergeData([rect1, rect2])

        >>> rm._choose_start_point(data)
        (0, 0)
        
        @type data: L{MergeData}

        @rtype: tuple of 2 int/floats
        @return: start point
        '''

        left_most_y_offset = min(data.verticals)
        left_most_lines = data.verticals[left_most_y_offset]

        lines = left_most_lines
        lines = [(x.get_bounds(), x) for x in lines]
        lines.sort()
        lines = [x[1] for x in lines]

        line = lines[0]
        start_point = min(line.point1, line.point2)
        return start_point

    def _get_polygon(self, start_point, data):
        '''
        Traverse the perimeter of a polygon in I{data}
        starting at I{start_point}.

        >>> rm = RectangleMerger()
        >>> data = Mock('MergeData')
        >>> data.points = {(0, 0): {'H': AxisAligned2DLine((0, 0), (1, 0)),
        ... 'V': AxisAligned2DLine((0, 0), (0, 2))},
        ... (2, 1): {'H': AxisAligned2DLine((2, 1), (1, 1)),
        ... 'V': AxisAligned2DLine((2, 1), (2, 2))},
        ... (0, 2): {'H': AxisAligned2DLine((0, 2), (2, 2)),
        ... 'V': AxisAligned2DLine((0, 0), (0, 2))},
        ... (2, 2): {'H': AxisAligned2DLine((0, 2), (2, 2)),
        ... 'V': AxisAligned2DLine((2, 1), (2, 2))},
        ... (1, 0): {'H': AxisAligned2DLine((0, 0), (1, 0)),
        ... 'V': AxisAligned2DLine((1, 0), (1, 1))},
        ... (1, 1): {'H': AxisAligned2DLine((2, 1), (1, 1)),
        ... 'V': AxisAligned2DLine((1, 0), (1, 1))}}
        >>> rm._get_polygon((0,0), data)
        (OrthogonalPolygon(points=[(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), \
(0, 2)], holes=[]), \
[AxisAligned2DLine((0, 0), (1, 0)), AxisAligned2DLine((1, 0), (1, 1)), \
AxisAligned2DLine((2, 1), (1, 1)), AxisAligned2DLine((2, 1), (2, 2)), \
AxisAligned2DLine((0, 2), (2, 2)), AxisAligned2DLine((0, 0), (0, 2))])

        @type start_point: tuple of 2 int/floats
        @param start_point: start point

        @type data: L{MergeData}

        @rtype: L{OrthogonalPolygon}, list
        @return: polygon and list of lines
            traversed belonging to polygon
        '''

        space = 'H' # traverse horizontal direction to start
        cur_point = start_point

        points = [cur_point]
        seen_points = set(points)
        lines = []

        while 1:

            line = data.points[cur_point][space]
            endpoint = line.get_other_endpoint(cur_point)

            lines.append(line)

            if endpoint in seen_points:
                break

            points.append(endpoint)
            seen_points.add(endpoint)

            cur_point = endpoint

            # change direction
            space = 'H' if space == 'V' else 'V'

        polygon = OrthogonalPolygon(points)
        return polygon, lines

    def _get_polygons(self, data):
        '''
        Get all orthogonal polygons from I{data}.

        @type data: L{MergeData}
        '''

        polygons = []
        data.prepare_points()

        while data.points:

            start_point = self._choose_start_point(data)

            polygon, lines = self._get_polygon(start_point, data)
            polygons.append(polygon)

            data.remove_points(polygon.points)
            data.remove_lines(lines)

        return polygons

    def _is_polygon_in_polygon(self, p1, p2):
        return p1.is_point_inside(p2.points[0])

    def _pair_polygons_and_holes(self, polygons):

        parents = {}
        children = {}

        for p in polygons:
            parents[p] = []
            children[p] = []

        for p1 in polygons:
            for p2 in polygons:
                if self._is_polygon_in_polygon(p1, p2):
                    parents.setdefault(p2, []).append(p1)
                    children.setdefault(p1, []).append(p2)

        paired_polygons = []

        for polygon, parents in parents.iteritems():

            num_parents = len(parents)

            if is_odd(num_parents):
                # is a hole.
                
                # choose immediate parent (the one
                # with least number of children containing
                # polygon)
                parents = [(len(children.get(p, [])), p) for p in parents]
                parents.sort()
                num_children, parent = parents[0]

                parent.holes.append(polygon)

            else:
                # is a container.
                paired_polygons.append(polygon)

        return paired_polygons

    def merge(self, rectangles):
        '''
        Merges axis-aligned 2D rectangles
        and returns one or more polygons.
        May return polygons with holes.

        >>> rect1 = AxisAligned2DRectangle((0, 0), (1, 2))
        >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))
        >>> rm = RectangleMerger()
        >>> rm.merge([rect1, rect2])
        [OrthogonalPolygon(points=[(0, 0), (1, 0), (1, 1), (2, 1), (2, 2), \
(0, 2)], holes=[])]

        @type rectangles: list
        @param rectangles: list of L{AxisAligned2DRectangle}s

        @rtype: list
        @return: list of L{OrthogonalPolygon}s
        '''

        data = self.MergeData(rectangles)

        remove_offsets = []
        
        for space in (data.horizontals, data.verticals):
            for offset, lines in space.iteritems():
                lines = self._simplify_colinear_lines(lines, data)
                if lines:
                    space[offset] = lines
                else:
                    remove_offsets.append((space, offset))

        for space, offset in remove_offsets:
            del space[offset]
        
        polygons = self._get_polygons(data)
        polygons = self._pair_polygons_and_holes(polygons)

        return polygons

class PolygonGenerator:

    class Config:
        max_xoffset = 50
        max_yoffset = 50

        min_side_length = 1
        max_side_length = 5

        min_rectangles = 3
        max_rectangles = 50

        min_points = 6
        max_points = 100

        min_holes = 1
        max_holes = 10

    def __init__(self, config=None):
        self.polygons = []
        self.config = config

    def _get_random_offset(self):
        '''
        >>> c = PolygonGenerator.Config()
        >>> pg = PolygonGenerator(c)
        >>> rand_offset = pg._get_random_offset()
        >>> x, y = pg._get_random_offset()
        >>> 0 <= x <= c.max_xoffset
        True
        >>> 0 <= y <= c.max_yoffset
        True
        '''
        c = self.config
        x = random.randint(0, c.max_xoffset)
        y = random.randint(0, c.max_xoffset)
        return x, y

    def _get_random_rectangle(self):
        '''
        >>> c = PolygonGenerator.Config()
        >>> pg = PolygonGenerator(c)
        >>> rect = pg._get_random_rectangle()
        >>> len = rect.max_x() - rect.min_x()
        >>> c.min_side_length <= len <= c.max_side_length
        True
        '''
        x, y = self._get_random_offset()
        c = self.config
        length = random.randint(c.min_side_length, c.max_side_length)
        height = random.randint(c.min_side_length, c.max_side_length)

        point1 = x, y
        point2 = x + length, y + height

        return AxisAligned2DRectangle(point1, point2)

    def _split_rectangle(self, rectangle, with_rect):
        '''
        >>> rect1 = AxisAligned2DRectangle((0, 0), (2, 2))
        >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))
        >>> sorted(pg._split_rectangle(rect1, rect2))
        [AxisAligned2DRectangle((0, 1), (1, 0)), \
AxisAligned2DRectangle((0, 2), (1, 1)), \
AxisAligned2DRectangle((1, 1), (2, 0))]
        '''
        (x1, y1), (x2, y2) = with_rect.point1, with_rect.point2

        overlap, dummy = split_overlapping_rectangles(rectangle, with_rect)
        pieces = _split_rectangle(rectangle, x1, y1, x2, y2)

        pieces.remove(overlap)
        return pieces

    def _add_rectangle(self, rectangle, space):
        '''
        >>> rect1 = AxisAligned2DRectangle((0, 0), (2, 2))
        >>> rect2 = AxisAligned2DRectangle((2, 1), (1, 2))

        >>> space = []
        >>> pg._add_rectangle(rect1, space)
        >>> pg._add_rectangle(rect2, space)
        >>> sorted(space)
        [AxisAligned2DRectangle((0, 0), (2, 2))]

        >>> space = []
        >>> pg._add_rectangle(rect2, space)
        >>> pg._add_rectangle(rect1, space)
        >>> sorted(space)
        [AxisAligned2DRectangle((0, 1), (1, 0)), \
AxisAligned2DRectangle((0, 2),(1, 1)), \
AxisAligned2DRectangle((1, 1), (2, 0)), \
AxisAligned2DRectangle((2, 1), (1, 2))]
        '''
        splits = [rectangle]

        for index, s in enumerate(splits):

            pieces = []
            has_overlap = False

            for r in space:
                if s.has_overlap(r):
                    has_overlap = True
                    cur_pieces = self._split_rectangle(s, r)
                    pieces.extend(cur_pieces)

            splits.extend(pieces)
            if not has_overlap and not pieces:
                # add the split as it is to the space
                # because the split does not overlap
                # any rectangle in "space"
                space.append(s)

    def _get_polygons(self):
       
        c = self.config
        num = random.randint(c.min_rectangles, c.max_rectangles)
        rectangles = [self._get_random_rectangle() for i in xrange(num)]

        space = []
        space.append(rectangles.pop(0))

        for r in rectangles:
            self._add_rectangle(r, space)

        m = RectangleMerger()
        polygons = m.merge(space)
        return polygons

    def __iter__(self):

        if not self.config:
            self.config = self.Config

        c = self.config
        min_points, max_points = c.min_points, c.max_points
        min_holes, max_holes = c.min_holes, c.max_holes

        while 1:
        
            if not self.polygons:
                try:
                    self.polygons = self._get_polygons()
                except InvalidData:
                    continue

            for p in self.polygons:
                num_points = len(p.points)
                num_holes = len(p.holes)

                has_enough_points = min_points <= num_points <= max_points
                has_enough_holes = min_holes <= num_holes <= max_holes
                
                if has_enough_points and has_enough_holes:
                    yield p

            self.polygons = []
