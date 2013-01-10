from itertools import chain

def make_collada(doc, positions, indices, normals):

    asset = doc.asset
    asset.created.text = '2009-09-18T21:23:22Z'
    asset.modified.text = '2009-09-18T21:23:22Z'
    unit = asset.unit
    unit.attrs = {'meter': '1', 'name': 'meter'}
    asset.up_axis.text = 'Z_UP'

    library_effects = doc.library_effects
    effect = library_effects.effect
    effect.attrs = {'id': 'Material_001-fx', 'name': 'Material_001-fx'}
    profile_COMMON = effect.profile_COMMON
    technique = profile_COMMON.technique
    phong = technique.phong

    phong.emission.color.text = '0.00000 0.00000 0.00000 1'
    phong.ambient.color.text = '0.40000 0.40000 0.40000 1'
    phong.diffuse.color.text = '0.80000 0.80000 0.80000 1'
    phong.specular.color.text = '0.50000 0.50000 0.50000 1'
    phong.shininess.float.text = '12.5'
    phong.reflective.color.text = '1.00000 1.00000 1.00000 1'
    phong.reflectivity.float.text = '0.0'
    phong.transparent.color.text = '1 1 1 1'
    phong.transparency.float.text = '0.0'

    library_materials = doc.library_materials
    material = library_materials.material
    material.attrs = {'id': "Material_001", 'name': "Material_001"}
    material.instance_effect.attrs = {'url': "#Material_001-fx"}

    
    visual_scene = doc.library_visual_scenes.visual_scene
    visual_scene.attrs = {'id': 'Scene', 'name': 'Scene'}

    for i, p in enumerate(positions):
        _id = 'solid-%s' % i

        geometry = doc.library_geometries.geometry
        geometry.attrs = {'id': _id, 'name': _id}

        mesh = geometry.mesh

        add_source(mesh, positions[i], '%s-positions' %_id)
        add_source(mesh, normals[i], '%s-normals' %_id)

        add_vertices(mesh, _id)
        add_triangles(mesh, indices[i], _id)

        node = visual_scene.node
        node.attrs = {'layer': "L1", 'id': _id, 'name': _id}

        node.translate.attrs = {'sid': "translate"}
        node.translate.text = '0.00000 0.00000 0.00000'

        node.rotate.attrs = {'sid': "rotateZ"}
        node.rotate.text = '0 0 1 0.00000'
        node.rotate.attrs = {'sid': "rotateY"}
        node.rotate.text = '0 1 0 -0.00000'
        node.rotate.attrs = {'sid': "rotateX"}
        node.rotate.text = '1 0 0 0.00000'

        node.scale.attrs = {'sid': 'scale'}
        node.scale.text = '1.00000 1.00000 1.00000'

        instance_geometry = node.instance_geometry
        instance_geometry.attrs = {'url': '#%s' %_id}

        bind_material = instance_geometry.bind_material
        technique_common = bind_material.technique_common
        instance_material = technique_common.instance_material
        instance_material.attrs = {'symbol': "Material_001",
                                   'target': "#Material_001"}
        bind_vertex_input = instance_material.bind_vertex_input
        bind_vertex_input.attrs = {'input_semantic': "TEXCOORD",
                                    'input_set': "1",
                                    'semantic': "CHANNEL1"}


    doc.scene.instance_visual_scene.attrs = {'url': "#Scene"}

    return doc

def add_vertices(mesh, _id):
    vertices = mesh.vertices
    vertices.attrs = {'id': '%s-vertices' %_id}
    vertices.input.attrs = {'semantic': 'POSITION',
                            'source': "#%s-positions" %_id}

def add_triangles(mesh, indices, _id):
    data = list(chain(*[(str(x), str(x)) for t in indices for x in t ]))
    triangles = mesh.triangles
    triangles.attrs = {'count': len(indices), 'material': 'BlueSG'}
    triangles.input.attrs = {'offset': '0', 'semantic': 'VERTEX',
                            'source': "#%s-vertices" %_id}
    triangles.input.attrs = {'offset': '1', 'semantic': 'NORMAL',
                            'source': "#%s-normals" %_id}
    
    triangles.p.text = ' '.join(data)

def add_source(mesh, data, _id):
    source = mesh.source
    source.attrs = {'id': _id, 'name': _id}
    float_array = source.float_array
    data = list(chain(*data))
    float_array.attrs = {'id': '%s-array' % _id, 'count': len(data)}
    float_array.text = ' '.join([str(x) for x in data])

    accessor = source.technique_common.accessor
    accessor.attrs = {'count': repr(len(data) / 3), 'offset': '0',
                      'source': '#%s-array' % _id, 'stride': '3'}

    accessor.param.attrs = {'name': 'X', 'type': 'float'}
    accessor.param.attrs = {'name': 'Y', 'type': 'float'}
    accessor.param.attrs = {'name': 'Z', 'type': 'float'}

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