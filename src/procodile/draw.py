'''
Drawing API - Uses GTS for CAD functionality.

G{importgraph}
'''

import math

import gts as _gts

from procodile.utils import Vector, drange, fequals

NUM_MERIDIANS = 20
PI = math.pi

class Object(object):

    def __init__(self):

        #: Underlying GTS object
        self._obj = None
        
        #: Tags assigned to geom by generator; These are
        #   useful for spatial querying.
        self.tags = []

        #: The generator which produced this geom
        self.generator = None

        #: If False, then this geom will not be rendered.
        self.visible = True

        #: Vertex normals for lighting calculations
        self.vnormals = {}

        #: Texture coordinates
        self.tcoords = {}

        #: Material (Texture or color)
        self.material = None
        
        #: updates of vertex normals and texture coordinates
        #   will be sent to this object if defined.
        self._update_target = None
   
    def translate(self, x, y, z):
        # TODO: the vertex normals of object
        # have to be tranformed too.
        self._obj.translate(x, y, z)

    def rotate(self, dx, dy, dz, angle):
        # TODO: the vertex normals of object
        # have to be tranformed too.
        self._obj.rotate(dx, dy, dz, angle)

    def transform(self, matrix):
        # TODO: Check this logic. It is almost definitely
        #   broken ;)
        translation = matrix.get_translation()
        angle, axis, point = matrix.get_rotation()

        self._obj.translate(*translation)
        dx, dy, dz = axis
        self._obj.rotate(dx, dy, dz, angle) #TODO: what about "point"?

        # TODO: the vertex normals of object
        # have to be tranformed too.

    def get_bound_box(self):

        vertices = self.vertices

        xvalues = [v.x for v in vertices]
        min_x = min(xvalues)
        max_x = max(xvalues)

        yvalues = [v.y for v in vertices]
        min_y = min(yvalues)
        max_y = max(yvalues)

        zvalues = [v.z for v in vertices]
        min_z = min(zvalues)
        max_z = max(zvalues)

        return (min_x, min_y, min_z,
                max_x, max_y, max_z)

    def _update_normal(self, vertex_id, normal):
        self.vnormals[vertex_id] = normal
        if self._update_target:
            self._update_target._update_normal(vertex_id, normal)

    def _update_tcoord(self, vertex_id, tcoord):
        self.tcoords[vertex_id] = tcoord
        if self._update_target:
            self._update_target._update_tcoord(vertex_id, tcoord)

    def __eq__(self, other):
        return other._obj.id == self._obj.id

    def __ne__(self, other):
            return not self.__eq__(other)

    def __hash__(self):
        return self._obj.id

    @property
    def id(self):
        return self._obj.id

class Vertex(Object):

    def __init__(self, *args):
        Object.__init__(self)

        if len(args) == 0:
            return

        elif len(args) == 1:
            self._obj = _gts.Vertex(*args[0])

        elif len(args) == 3:
            self._obj = _gts.Vertex(*args)

        else:
            raise Exception('bad arguments')

    def _get_x(self):
        return self._obj.x

    def _set_x(self, value):
        self._obj.x = value
    
    x = property(_get_x, _set_x)

    def _get_y(self):
        return self._obj.y

    def _set_y(self, value):
        self._obj.y = value
    
    y = property(_get_y, _set_y)
    
    def _get_z(self):
        return self._obj.z

    def _set_z(self, value):
        self._obj.z = value
    
    z = property(_get_z, _set_z)

    def _get_position(self):
        o = self._obj
        return (o.x, o.y, o.z)

    def _set_position(self, position):
        o = self._obj
        o.x, o.y, o.z = position

    position = property(_get_position, _set_position)

    def _set_normal(self, normal):
        self.vnormals[self.id] = normal

        if self._update_target:
            self._update_target._update_normal(self.id, normal)

    def _get_normal(self):
        return self.vnormals.get(self.id)

    normal = property(_get_normal, _set_normal)

    def _set_tcoord(self, tcoord):
        self.tcoords[self.id] = tcoord

        if self._update_target:
            self._update_target._update_tcoord(self.id, tcoord)

    def _get_tcoord(self):
        return self.tcoords.get(self.id)

    tcoord = property(_get_tcoord, _set_tcoord)

    def distance(self, object):
        return self._obj.distance(object._obj)

def _wrap_vertex(vertex, container):
    v = Vertex()
    v._obj = vertex
    v.normal = container.vnormals.get(v.id)
    v.tcoord = container.tcoords.get(v.id)
    v._update_target = container
    return v

def _wrap_edge(edge, container):
    e = Edge()
    e._obj = edge
    _distribute_vertex_data(container, e)
    e._update_target = container
    return e

def _wrap_face(face, container):
    f = Face()
    f._obj = face
    _distribute_vertex_data(container, f)
    f._update_target = container
    return f

def _merge_vertex_data(container, containees):
    for c in containees:
        container.vnormals.update(c.vnormals)
        container.tcoords.update(c.tcoords)

def _distribute_vertex_data(container, containee):
    for v in containee.vertices:
        containee.vnormals[v.id] = container.vnormals[v.id]
        containee.tcoords[v.id] = container.tcoords[v.id]

class Edge(Object):

    def __init__(self, *args):
        Object.__init__(self)

        if len(args) == 0:
            return
        
        elif len(args) == 1 and len(args[0]) == 2:
            v1, v2 = args[0]

        elif len(args) == 2:
            v1, v2 = args

        else:
            raise Exception('bad arguments')


        self._obj = _gts.Edge(v1._obj, v2._obj)
        _merge_vertex_data(self, (v1, v2))

    @property
    def v1(self):
        return _wrap_vertex(self._obj.v1, self)

    @property
    def v2(self):
        return _wrap_vertex(self._obj.v2, self)

    @property
    def vertices(self):
        return (self.v1, self.v2)

class Face(Object):

    def __init__(self, *args):
        Object.__init__(self)

        if len(args) == 0:
            return
            
        elif len(args) == 1 and len(args[0]) == 3:
            e1, e2, e3 = args[0]

        elif len(args) == 3:
            e1, e2, e3 = args

        else:
            raise Exception('bad arguments')

        self._obj = _gts.Face(e1._obj, e2._obj, e3._obj)
        _merge_vertex_data(self, (e1, e2, e3))

    @property
    def mesh(self):
        s = Surface()
        s.add(self)
        return s.mesh

    @property
    def e1(self):
        return _wrap_edge(self._obj.e1, self)

    @property
    def e2(self):
        return _wrap_edge(self._obj.e2, self)

    @property
    def e3(self):
        return _wrap_edge(self._obj.e3, self)

    @property
    def vertices(self):
        return [_wrap_vertex(v, self) for v in self._obj.vertices()]

    @property
    def normal(self):
        return self._obj.normal()

class Surface(Object):

    def __init__(self, *args):
        Object.__init__(self)

        parts = None

        if len(args) == 0:
            parts = []

        if len(args) == 1:
            if isinstance(args[0], (Face, Surface)):
                parts = args

            elif isinstance(args[0], (list, tuple, set)):
                parts = args[0]

            else:
                raise Exception('bad arguments')

        else:
            parts = args

        self._obj = _gts.Surface()
        for p in parts:
            self.add(p)

    def add(self, *parts):

        _parts = None

        if len(parts) == 1:
            _parts = parts if isinstance(parts, (list, tuple)) else [parts]
        elif len(parts) > 1:
            _parts = parts
        else:
            raise Exception('bad arguments')

        for p in _parts:
            self._obj.add(p._obj)
            _merge_vertex_data(self, (p,))

    def remove(self, part):
        self._obj.remove(part)
        # FIXME: the tcoords and vertex normals of removed part
        #   have to be purged.

    @property
    def mesh(self):
        vertices = self.vertices
        _vertices = tuple([v._obj for v in vertices])
        indices = self._obj.face_indices(_vertices)
        tcoords = [self.tcoords.get(v.id) for v in vertices]

        no_normal_verts = [v for v in vertices if v.id not in self.vnormals]
        _vnormals = {}

        for v in no_normal_verts:
            fnormals = [f.normal() for f in v._obj.faces()]
            fnormals = [Vector(*fn).normalize() for fn in fnormals]

            vnormal = Vector()
            for fn in fnormals:
                vnormal = vnormal + fn

            vnormal = vnormal.normalize()

            vnormal = (vnormal.x, vnormal.y, vnormal.z)
            _vnormals[v.id] = vnormal

        normals = []
        for index, v in enumerate(vertices):
            n = self.vnormals.get(v.id) or _vnormals[v.id]
            normals.append(n)
            vertices[index] = v.position
       
        return vertices, indices, normals, tcoords

    @property
    def vertices(self):
        return [_wrap_vertex(v, self) for v in self._obj.vertices()]

    @property
    def faces(self):
        return [_wrap_face(f, self) for f in self._obj.faces()]

    @property
    def area(self):
        return self._obj.area()

    def invert(self):
        for f in self._obj.faces():
            f.revert()

class SurfaceGroup(Object):
    
    def __init__(self):
        self.surfaces = {}
        Object.__init__(self)

        del self.vnormals
        del self.tcoords
        del self._obj
        del self._update_target

    def _get_unused_name(self):
        for i in xrange(10000000000):
            if str(i) not in self.surfaces:
                return str(i)

    def add(self, surface, name=None):
        name = name or self._get_unused_name()
        self.surfaces[name] = surface

    def remove(self, surface):
        if isinstance(surface, (str, unicode)) and surface in self.surfaces:
            del self.surfaces[surface]

        else:
            name = None
            for _name, _surface in self.surfaces.iteritems():
                if _surface == surface:
                    name = _name

            if name:
                del self.surfaces[name]

    def translate(self, x, y, z):
        for name, surface in self.surfaces.iteritems():
            surface.translate(x, y, z)

    def rotate(self, dx, dy, dz, angle):
        for name, surface in self.surfaces.iteritems():
            surface.rotate(dx, dy, dz, angle)

    def transform(self, matrix):
        for name, surface in self.surfaces.iteritems():
            surface.transform(matrix)

    def _get_material(self):
        return dict((n, s.material) for n, s in self.surfaces.iteritems())

    def _set_material(self, material, name=None):
        if name:
            self.surfaces[name].material = material
        
        else:
            for surface in self.surfaces.itervalues():
                surface.material = material

    material = property(_get_material, _set_material)

    def get_bound_box(self):
        bboxes = []

        for name, surface in self.surfaces.iteritems():
            bboxes.append(surface.get_bound_box())

        min_x = min(b[0] for b in bboxes)
        min_y = min(b[1] for b in bboxes)
        min_z = min(b[2] for b in bboxes)
        max_x = max(b[3] for b in bboxes)
        max_y = max(b[4] for b in bboxes)
        max_z = max(b[5] for b in bboxes)

        return (min_x, min_y, min_z, max_x, max_y, max_z)

    @property
    def area(self):
        return self._obj.area()

    def _canonical_form(self):
        return tuple([s.id for s in self.surfaces.itervalues()])

    def __eq__(self, other):
        return other._canonical_form() == self._canonical_form()

    def __ne__(self, other):
            return not self.__eq__(other)

    def __hash__(self):
        return hash(self._canonical_form())

class Rectangle(Surface):
    
    def __init__(self, length=1, height=1):
        Surface.__init__(self)

        x, z = length, height

        a = Vertex(0, 0, 0); a.tcoord = (0.0, 0.0)
        b = Vertex(x, 0, 0); b.tcoord = (1.0, 0.0)
        c = Vertex(x, 0, z); c.tcoord = (1.0, 1.0)
        d = Vertex(0, 0, z); d.tcoord = (0.0, 1.0)

        ab = Edge(a, b)
        bd = Edge(b, d)
        da = Edge(d, a)
        abd = Face(ab, bd, da)

        bc = Edge(b, c)
        cd = Edge(c, d)
        db = Edge(d, b)
        bcd = Face(bc, cd, db)

        self.add(abd, bcd)

def _center_of_point_cloud(vertices):
    x, y, z = 0, 0, 0

    for v in vertices:
        x += v.x
        y += v.y
        z += v.z

    length = float(len(vertices))
    x = x / length
    y = y / length
    z = z / length

    c = Vertex(x, y, z)
    c.tcoord = (0.0, 0.0)
    return c
   
class Fan(Surface):
    
    def __init__(self, vertices, center=None):
        Surface.__init__(self)

        c = center or _center_of_point_cloud(vertices)
        self.center = c

        num_vertices = len(vertices)
        if len(vertices) < 2:
            raise Exception('insufficient vertices')

        normal = self._compute_normal(c, vertices)
        v1 = vertices[0]
        i = Vector(v1.x - c.x, v1.y - c.y, v1.z - c.z)
        j = i.cross(normal)

        vertices = vertices[:]
        vertices.append(vertices[0])

        s = Surface()
        for index in xrange(num_vertices):
            a = vertices[index]
            b = vertices[index+1]

            a1 = Vector(a.x - c.x, a.y - c.y, a.z - c.z)
            a.tcoord = (a1.dot(i), a1.dot(j))

            face = Face(Edge(c, a), Edge(a, b), Edge(b, c))
            s.add(face)

        self.add(s)

    def _compute_normal(self, center, vertices):
        
        normals = []
        c = center
        v1 = vertices[0]
        v1 = Vector(v1.x - c.x, v1.y - c.y, v1.z - c.z)

        for v in vertices[1:2]:
            v = Vector(v.x - c.x, v.y - c.y, v.z - c.z)
            n = v1.cross(v)
            normals.append(n.normalize())

        normal = Vector()
        for _n in normals:
            normal =  normal + _n
        
        return normal.normalize()

class Disc(Fan):

    def __init__(self, radius=1, meridians=NUM_MERIDIANS):
        self.radius = radius
        self.meridians = meridians

        if meridians < 3:
            raise Exception('meridians should be >= 3')

        center = Vertex(0, 0, 0)
        center.tcoord = (0.0, 0.0)
        self.disc_vertices = self.compute_vertices(radius, meridians)

        Fan.__init__(self, self.disc_vertices, center)
    
    @staticmethod
    def compute_vertices(radius, meridians, z=0):

        r = radius
        
        vertices = []
        for theta in drange(0, 2 * PI, 2 * PI / meridians):
            v = Vertex(r * math.cos(theta), r * math.sin(theta), z)
            vertices.append(v)

        return vertices

class Sections(Surface):

    def __init__(self, sections):

        Surface.__init__(self)

        if len(sections) < 2:
            raise Exception('not enough sections')

        num_points = len(sections[0])
        for s in sections:
            if len(s) != num_points:
                raise Exception('all sections should have same '\
                                'number of points')

        centers = [_center_of_point_cloud(s) for s in sections]
        sections = [list(s) for s in sections]

        height = 0.0
        self._assign_texture_coords(sections[0], height)

        for index in xrange(len(sections)-1):
            s1 = sections[index]
            s2 = sections[index+1]
            c1 = centers[index]
            c2 = centers[index+1]
            height += c2.distance(c1)
            self._assign_texture_coords(s2, height)
           
            for index in xrange(num_points):
                a = s1[index]
                b = s1[index+1]
                c = s2[index+1]
                d = s2[index]

                face1 = Face(Edge(a, b), Edge(b, d), Edge(d, a))
                face2 = Face(Edge(b, c), Edge(c, d), Edge(d, b))
                self.add(face1)
                self.add(face2)

    def _assign_texture_coords(self, section, height):
        section.append(Vertex(section[0].position))

        lengths = []
        for index in xrange(len(section) - 1):
            p1 = section[index]
            p2 = section[index+1]
            lengths.append(p2.distance(p1))

        perimeter = float(sum(lengths))

        if fequals(perimeter, 0):
            lengths = [1./len(lengths)] * len(lengths)
            perimeter = 1.

        tcoord = 0.0
        for index, length in enumerate(lengths):
            section[index].tcoord = (tcoord, height)
            increment = length / perimeter
            tcoord = tcoord + increment
            section[index]

        section[-1].tcoord = (1.0, height)

class Box(SurfaceGroup):

    def __init__(self, length=1, depth=1, height=1):

        SurfaceGroup.__init__(self)

        self.length = length
        self.depth = depth
        self.height = height

        self._make_mesh()

    def _make_mesh(self):
        x, y, z = self.length, self.depth, self.height

        a = Vertex(0, 0, 0); a.tcoord = (0.0, 0.0)
        b = Vertex(x, 0, 0); b.tcoord = (1.0, 0.0)
        c = Vertex(x, 0, z); c.tcoord = (1.0, 1.0)
        d = Vertex(0, 0, z); d.tcoord = (0.0, 1.0)

        ab = Edge(a, b)
        bd = Edge(b, d)
        da = Edge(d, a)
        abd = Face(ab, bd, da)

        bc = Edge(b, c)
        cd = Edge(c, d)
        db = Edge(d, b)
        bcd = Face(bc, cd, db)

        front = Surface(abd, bcd)
        self.add(front, 'front')

        f = Vertex(x, y, 0); f.tcoord = (0.0, 0.0)
        e = Vertex(0, y, 0); e.tcoord = (1.0, 0.0)
        h = Vertex(0, y, z); h.tcoord = (1.0, 1.0)
        g = Vertex(x, y, z); g.tcoord = (0.0, 1.0)

        eh = Edge(e, h)
        hf = Edge(h, f)
        fe = Edge(f, e)
        ehf = Face(eh, hf, fe)

        hg = Edge(h, g)
        gf = Edge(g, f)
        fh = Edge(f, h)
        hgf = Face(hg, gf, fh)

        back = Surface(ehf, hgf)
        self.add(back, 'back')

        e = Vertex(0, y, 0); e.tcoord = (0.0, 0.0)
        a = Vertex(0, 0, 0); a.tcoord = (1.0, 0.0)
        d = Vertex(0, 0, z); d.tcoord = (1.0, 1.0)
        h = Vertex(0, y, z); h.tcoord = (0.0, 1.0)

        he = Edge(h, e)
        ea = Edge(e, a)
        ah = Edge(a, h)
        hea = Face(he, ea, ah)

        ad = Edge(a, d)
        dh = Edge(d, h)
        ha = Edge(h, a)
        adh = Face(ad, dh, ha)

        left = Surface(hea, adh)
        self.add(left, 'left')

        b = Vertex(x, 0, 0); b.tcoord = (0.0, 0.0)
        f = Vertex(x, y, 0); f.tcoord = (1.0, 0.0)
        g = Vertex(x, y, z); g.tcoord = (1.0, 1.0)
        c = Vertex(x, 0, z); c.tcoord = (0.0, 1.0)

        cb = Edge(c, b)
        bf = Edge(b, f)
        fc = Edge(f, c)
        cbf = Face(cb, bf, fc)

        fg = Edge(f, g)
        gc = Edge(g, c)
        cf = Edge(c, f)
        fgc = Face(fg, gc, cf)

        right = Surface(cbf, fgc)
        self.add(right, 'right')

        d = Vertex(0, 0, z); d.tcoord = (0.0, 0.0)
        c = Vertex(x, 0, z); c.tcoord = (1.0, 0.0)
        g = Vertex(x, y, z); g.tcoord = (1.0, 1.0)
        h = Vertex(0, y, z); h.tcoord = (0.0, 1.0)

        hd = Edge(h, d)
        dc = Edge(d, c)
        ch = Edge(c, h)
        hdc = Face(hd, dc, ch)

        cg = Edge(c, g)
        gh = Edge(g, h)
        hc = Edge(h, c)
        cgh = Face(cg, gh, hc)

        top = Surface(hdc, cgh)
        self.add(top, 'top')

        e = Vertex(0, y, 0); e.tcoord = (0.0, 0.0)
        f = Vertex(x, y, 0); f.tcoord = (1.0, 0.0)
        b = Vertex(x, 0, 0); b.tcoord = (1.0, 1.0)
        a = Vertex(0, 0, 0); a.tcoord = (0.0, 1.0)

        ae = Edge(a, e)
        ef = Edge(e, f)
        fa = Edge(f, a)
        aef = Face(ae, ef, fa)

        fb = Edge(f, b)
        ba = Edge(b, a)
        af = Edge(a, f)
        fba = Face(fb, ba, af)

        bottom = Surface(aef, fba)
        self.add(bottom, 'bottom')
        
class Cylinder(SurfaceGroup):

    def __init__(self, radius=1, height=1,
                       meridians=NUM_MERIDIANS,
                       segments=None):
        SurfaceGroup.__init__(self)

        self.radius = radius
        self.height = height
        self.meridians = meridians
        self.segments = segments

        self._make_mesh()

    def _radius_at_height(self, height):
        return self.radius

    def _compute_segments(self):
        nsegments = self.segments

        if nsegments is None:
            # compute number of segments to use in making cylinder
            # in such a way as to ensure that no triangle becomes too long
            # and narrow
            circumference = 2 * PI * self.radius
            meridian_width = circumference / float(self.meridians)
            nsegments = int(math.floor(self.height / meridian_width))
            nsegments = nsegments / 2

        segments = []
        sheight = self.height / float(nsegments)

        for i in xrange(1, nsegments+1):
            h = sheight * i
            r = self._radius_at_height(h)
            verts = Disc.compute_vertices(r, self.meridians, h)
            segments.append(verts)

        return segments

    def _make_mesh(self):
        
        tcap = Disc(self.radius, self.meridians)
        tcap.translate(0, 0, self.height)

        bcap = Disc(self.radius, self.meridians)
        bcap.invert()

        t_vertices = [Vertex(v.position) for v in tcap.disc_vertices]
        b_vertices = [Vertex(v.position) for v in bcap.disc_vertices]

        sections = [b_vertices]
        sections.extend(self._compute_segments())
        sections.append(t_vertices)

        side = Sections(sections)

        self.add(tcap, 'top')
        self.add(bcap, 'bottom')
        self.add(side, 'side')

class Cone(Cylinder):
    
    def __init__(self, radius=1, height=1, meridians=NUM_MERIDIANS):
        Cylinder.__init__(self, radius, height, meridians)

    def _radius_at_height(self, height):
        h = self.height
        h1 = self.height - height
        
        r1 = self.radius * h1 / h
        return r1

    def _make_mesh(self):
 
        tcap = Disc(0, self.meridians)
        tcap.translate(0, 0, self.height)

        bcap = Disc(self.radius, self.meridians)
        bcap.invert()

        t_vertices = [Vertex(v.position) for v in tcap.disc_vertices]
        b_vertices = [Vertex(v.position) for v in bcap.disc_vertices]

        sections = [b_vertices]
        sections.extend(self._compute_segments())
        sections.append(t_vertices)

        side = Sections(sections)

        self.add(bcap, 'bottom')
        self.add(side, 'side')
