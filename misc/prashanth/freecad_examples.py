import procodile.draw as draw

def create_vertex():
    v = draw.Vertex(10, 10, 10)
    return v

def create_linesegment():
    start_point = (0, 0, 0)
    end_point = (10, 0, 0)
    ls = draw.makeLine(start_point, end_point)
    return ls

def create_circle():
    c = draw.Circle()
    c = c.toShape()
    return c

def create_circle1():
    c = draw.makeCircle(1)
    return c

def create_circle_face():
    c = draw.makeCircle(2)
    w = draw.Wire(c)
    f = draw.Face(w)
    return f

def create_cuboid():
    c = draw.makeBox(2, 4, 6)
    return c

def create_cone():
    c = draw.makeCone(0, 4, 5)
    return c

def create_plane():
    p = draw.makePlane(10, 20)
    return p
