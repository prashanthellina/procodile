
__author__="karthik"
__date__ ="$Sep 18, 2009 11:00:29 AM$"

from cStringIO import StringIO as stringio
import xmlrpclib

from procodile.xmlwriter import XMLNode

def transmit_buildtree(data, host):
    address = 'http://%s' % host
    sp = xmlrpclib.ServerProxy(address)
    sp.clear()
    return sp.load(data)

def get_buildtree(vertices, indices, normals):

    doc = XMLNode('buildspace')
    gen = doc.generator
    gen.config.attrs = {'a':10}
    gen.attrs = (('id', "1"), ('seed', "1"), ('name', "generator"),
                 ('location', "None"), ('bbox', "None"))

    gen_geoms = gen.geoms
    geom = gen_geoms.geom

    geom.attrs = (('shape', "geom"), ('bbox', "None"), ('area', "None"),
                  ('volume', "None"), ('location', "None"), ('visible', 1))

    geom.mesh = '%s;\n%s;\n%s;' % (repr(vertices), repr(normals), repr(indices))
    sgen = gen.sub_generators

    s = stringio()
    doc.serialize(s)
    build_tree = s.getvalue()

    return build_tree

def parse_mesh(stream):
    
    f = stream

    parse_line = lambda f, t: [t(x) for x in f.readline().strip().split(' ')]

    n_vertices = int(f.readline())
    vertices = [parse_line(f, float) for i in xrange(n_vertices)]

    n_indices = int(f.readline())
    indices = [parse_line(f, int) for i in xrange(n_indices)]

    n_normals = f.readline()
    n_normals = int(n_normals) if n_normals else 0
    normals = [parse_line(f, float) for i in xrange(n_normals)]
    
    return vertices, indices, normals