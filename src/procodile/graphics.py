'''
Contains graphics functionality to aid in rendering

G{importgraph}
'''

__version__ = 'dev'

import operator
import colorsys
import logging

import ogre.renderer.OGRE as ogre

from procodile.utils import ignore, percent, restrict_value
from procodile.utils import get_function_call_info
from procodile.utils import fequals, fequals_sequence

L = logging.getLogger()

COLORS = {
            # color_name: (DIFFUSE, SPECULAR, AMBIENT, SHININESS)
            'red':      ((0.7, 0, 0), (1.0, 0, 0), (0.3, 0, 0), 0.1),
            'green':    ((0, 0.7, 0), (0, 1.0, 0), (0, 0.3, 0), 0.1),
            'blue':     ((0, 0, 0.7), (0, 0, 1.0), (0, 0, 0.3), 0.1),
            'black':    ((0, 0, 0),),
            'white':    ((1, 1, 1),),
            'grey':     ((0.8, 0.8, 0.8),),
            'brown':    ((0.54, 0.04, 0.04), (0.55, 0.04, 0.04),
                         (0.52, 0.02, 0.02), 0.1),
            'dark_brown': ((0.33, 0.16, 0),)
         }

def create_material(name,
                    diffuse_colour,
                    specular_colour = None,
                    ambient_colour = None,
                    shininess = 0.0,
                    scene_blending = ogre.SBT_TRANSPARENT_ALPHA,
                    vertex_colour_tracking = ogre.TVC_NONE
                    ):
    '''
    Creates an ogre material.

    @type name: str
    @param name: name of the material

    @type diffuse_colour: tuple of floats
    @param diffuse_colour: (R, G, B, [A])

    @type specular_colour: tuple of floats
    @param specular_colour: (R, G, B, [A])

    @type ambient_colour: tuple of floats
    @param ambient_colour: (R, G, B, [A])

    @type shininess: float
    @param shininess: 0.0 to 1.0

    @param vertex_colour_tracking: The vertex colour should override which
        of the material colours (diffuse, specular, ambient)

    @return: ogre material
    '''

    L.debug(get_function_call_info())

    specular_colour = specular_colour or diffuse_colour
    ambient_colour = ambient_colour or diffuse_colour

    m = ogre.MaterialManager.getSingleton().create(name, "General")

    m.setReceiveShadows(True)
    m.getTechnique(0).setLightingEnabled(True)
    m.getTechnique(0).getPass(0).setColourWriteEnabled(True)

    m.getTechnique(0).getPass(0).setDiffuse(diffuse_colour)
    m.getTechnique(0).getPass(0).setAmbient(ambient_colour)
    m.getTechnique(0).getPass(0).setShininess(shininess)
    m.getTechnique(0).getPass(0).setSpecular(specular_colour)
    m.getTechnique(0).getPass(0).setSceneBlending(scene_blending)
    m.getTechnique(0).getPass(0).setVertexColourTracking(vertex_colour_tracking)

    return m

def destroy_material(name):
    '''
    Destroy an Ogre material.

    @type name: str
    @param name: name of the material
    '''
    ogre.MaterialManager.getSingleton().remove(name)

def create_mesh(name, mesh, scene_manager, material_manager):
    '''
    Creates an ogre mesh from procodile mesh.

    @type name: str
    @param name: name to used for ogre mesh.
    
    @type mesh: Mesh object
    @param mesh: procodile mesh

    @param scene_manager: ogre scene manager

    @type material_manager: L{MaterialManager}
    @param material_manager: world's material manager
    '''

    obj = scene_manager.createManualObject(name)
    obj.setDynamic(True)

    for sub_mesh, color in mesh.get_sub_meshes():

        material = material_manager.get_material(color)
        obj.begin(material, ogre.RenderOperation.OT_TRIANGLE_LIST)

        i = 0
        for quad in sub_mesh.quads:
            a, b, c, d = quad.points
            obj.position(*a)
            obj.normal(*quad.normal)
            obj.position(*b)
            obj.position(*c)
            obj.position(*d)

            obj.quad(i, i+1, i+2, i+3)
            i += 4

        obj.end()

    obj.convertToMesh(name)
    scene_manager.destroyManualObject(name)

def hsv_to_rgb(hsv):
    '''
    Convert from HSV to RGB.

    >>> r,g,b = hsv_to_rgb((0.4046, 0.99857, 0.7))
    >>> fequals(.001001, r), fequals(.7, g), fequals(.2998929, b)
    (True, True, True)

    @type hsv: tuple of three floats
    @param hsv: 
    '''
    rgb = colorsys.hsv_to_rgb(*hsv)
    return rgb

class Color:
    '''
    Represents color; Supports hsv and rgb and conversions
    Values of components for both rgb and hsv have to be
    in the 0.0 to 1.0 range.
    '''

    COMPONENT_MIN = 0.0
    COMPONENT_MAX = 1.0

    def __init__(self, rgb=None, hsv=None):
        '''
        >>> col = Color((0.001, 0.7, 0.3))

        >>> fequals(col.red, 0.001)
        True

        >>> fequals(col.green, 0.7)
        True

        >>> fequals(col.blue, 0.3)
        True

        >>> col = Color('red')
        >>> fequals(col.red, 1.0)
        True

        @type rgb: tuple
        @param rgb: of three floats

        @type hsv: tuple
        @param hsv: of three floats
        '''
        assert(not (rgb and hsv))

        self.red = self.COMPONENT_MIN
        self.green = self.COMPONENT_MIN
        self.blue = self.COMPONENT_MIN

        if rgb:
            if isinstance(rgb, (str, unicode)):
                rgb = COLORS[rgb]
            self.set_rgb(rgb)

        if hsv:
            self.set_hsv(hsv)

    def set_hsv(self, hsv):
        '''
        Set HSV value.

        @type hsv: tuple of three floats
        @param hsv: 
        '''
        r, g, b = hsv_to_rgb(hsv)
        self.set_rgb((r, g, b))

    def set_rgb(self, rgb):
        '''
        Set RGB value.

        @type rgb: tuple of three floats
        @param rgb: 
        '''
        _min = Color.COMPONENT_MIN
        _max = Color.COMPONENT_MAX
        r, g, b = [restrict_value(x, _min, _max) for x in rgb]
        self.red, self.green, self.blue = r, g, b

    def get_rgb(self):
        '''
        @return: RGB value (tuple of three floats)
        '''
        return self.red, self.green, self.blue

    def get_hsv(self):
        '''
        >>> col = Color((0.001, 0.7, 0.3))
        >>> h,s,v = col.get_hsv()
        >>> fequals(h,0.40462565569861714), fequals(s, 0.99857142857142855), \
            fequals(v, 0.69999999999999996)
        (True, True, True)
        '''
        return self.rgb_to_hsv()

    def rgb_to_hsv(self, rgb=None):
        '''
        Convert RGB value TO HSV.
        if I{rgb} is not specified, the RGB value of self is taken.

        @type rgb: tuple of three floats
        @param rgb: 
        '''
        rgb = rgb or (self.red, self.green, self.blue)
        return colorsys.rgb_to_hsv(*rgb)

    def __eq__(self, color):
        '''
        Check if this color is the same as I{color}.

        >>> c1 = Color((0.5, 0.6, 0.7))
        >>> c2 = Color((0.5, 0.6000000001, 0.700000002))
        >>> c3 = Color((0.5, 0.6001, 0.7002))

        >>> c1 == c2
        True

        >>> c1 == c3
        False
        '''
        equality = fequals_sequence(color.get_rgb(), self.get_rgb())
        return False not in equality

class MaterialColor(Color):
    #pylint: disable-msg=R0902
    '''
    Represents color assigned to a material.
        - Diffuse color (base color of material)
        - Specular color (highlight area color when light shines)
        - Ambient color (shade color, color when only ambient light is present)
        - Emissive color (color that the material emits even when no light is present)
        - Shininess (nature of highlight area when light shines on surface)

    By default the ambient and specular colors are computed based on the
    base/diffuse color. To prevent this computation and take complete control
    over the values, assign color to diffuse member variable.
    '''

    def __init__(self, rgb=None, hsv=None):
        '''
        The components of rgb and hsv have to be
        defined in 0.0 to 1.0 range.

        >>> col = Color((0.001, 0.7, 0.3))
        >>> mat = MaterialColor(col.get_rgb())
        >>> fequals(mat.ambient_change, -0.20000000000000001)
        True

        >>> fequals(mat.specular_change, 0.20000000000000001)
        True
        '''

        m = self.COMPONENT_MIN

        self.diffuse = self
        self.ambient = Color((m, m, m))
        self.specular = Color((m, m, m))
        self.emissive = Color((m, m, m))

        self.shininess = 0.0

        self.ambient_change = -percent(20)
        self.specular_change = percent(20)

        Color.__init__(self, rgb, hsv)

    def diffuse_to_ambient(self, change):
        '''
        Compute ambient color based on the diffuse color.
        Ambient color is a darker shade of diffuse color by default.
        To override that change the value of ambient_change (0.0 to 1.0)

        @type change: float
        @param change: between 0.0 and 1.0
        '''
        h, s, v = self.diffuse.get_hsv()
        _min, _max = self.COMPONENT_MIN, self.COMPONENT_MAX
        v = restrict_value(v + (v * change), _min, _max)
        self.ambient.set_hsv((h, s, v))

    def diffuse_to_specular(self, change):
        '''
        Compute specular color based on the diffuse color.
        Specular color is a lighter shade of diffuse color by default.
        To override that change the value of specular_change (0.0 to 1.0)

        @type change: float
        @param change: between 0.0 and 1.0
        '''
        h, s, v = self.diffuse.get_hsv()
        _min, _max = self.COMPONENT_MIN, self.COMPONENT_MAX
        v = restrict_value(v + (v * change), _min, _max)
        self.specular.set_hsv((h, s, v))

    def set_rgb(self, rgb):
        '''
        Set RGB value.

        @type rgb: tuple of three floats
        @param rgb: 
        '''
        if self.diffuse != self:
            self.diffuse.set_rgb(rgb)
        else:
            self.red, self.green, self.blue = rgb
            self.diffuse_to_ambient(self.ambient_change)
            self.diffuse_to_specular(self.specular_change)

    def update(self):
        '''
        To re-calculate ambient and specular colors after
        modification of 'change' values.

        >>> col = Color((0.001, 0.7, 0.3))
        >>> mat = MaterialColor(col.get_rgb())

        >>> r,g,b = mat.ambient.get_rgb()
        >>> fequals(r, 0.00080000000000000947), fequals(g, 0.55999999999999994), \
                fequals(b, 0.24000000000000013)
        (True, True, True)

        >>> r,g,b = mat.specular.get_rgb()
        >>> fequals(r, 0.0012000000000000144), fequals(g, 0.83999999999999997), \
                fequals(b, 0.36000000000000021)
        (True, True, True)

        >>> mat.ambient_change = 30
        >>> mat.specular_change = 35
        >>> mat.update()

        >>> r,g,b = mat.ambient.get_rgb()
        >>> fequals(r, 0.0014285714285714457), fequals(g, 1.0), \
                fequals(b, 0.42857142857142883)
        (True, True, True)

        >>> r,g,b = mat.specular.get_rgb()
        >>> fequals(r, 0.0014285714285714457), fequals(g, 1.0), \
                fequals(b, 0.42857142857142883)
        (True, True, True)
        '''
        self.set_rgb(self.get_rgb())

    def set_emissive_value(self, value):
        '''
        The emissive color of the object is the same as
        the diffuse color except the 'value' (of HSV) model
        is modified.
        '''
        h, s, v = self.get_hsv()
        ignore(v)
        self.emissive.set_hsv((h, s, value))

    def __eq__(self, color):
        '''
        Check if this material color is equal to I{color}.

        >>> c1 = MaterialColor((0.5, 0.6, 0.7))
        >>> c2 = MaterialColor((0.5, 0.6, 0.70000000000002))

        >>> c1 == c2
        True

        >>> c2.blue = 0.7002 
        >>> c1 == c2
        False

        >>> c2.blue = 0.7
        >>> c2.shininess = 0.01
        >>> c1 == c2
        False
        '''
        equality = [Color.__eq__(color.diffuse, self.diffuse),
                    color.ambient == self.ambient,
                    color.specular == self.specular,
                    color.emissive == self.emissive,
                    fequals(color.shininess, self.shininess)]
        return False not in equality

def make_color(diffuse, specular=None, ambient=None, shininess=None):
    m = MaterialColor(diffuse)

    if specular:
        m.specular = Color(specular)

    if ambient:
        m.ambient = Color(ambient)

    if shininess:
        m.shininess = shininess

    return m

class MaterialManager:
    '''
    Manage materials used.
    '''

    def __init__(self):
        #: mapping of material color to ogre material name
        self.materials = []

        for name, color in COLORS.iteritems():
            color = make_color(*color)
            self.get_material(color, name)

    def get_material(self, color, name=None):
        '''
        Get Ogre material for given Material Color.

        @type color: L{MaterialColor}, str
        @param color: material color for which material is required

        @rtype: str
        @return: Ogre material name
        '''

        material = None

        for m, c in self.materials:
            if isinstance(color, (str, unicode)):
                if m == color:
                    material = m
                    break
            else:
                if c == color:
                    material = m
                    break

        if material:
            return material
       
        if not name:
            name = '%d_material' % len(self.materials)

        create_material(name, color.diffuse.get_rgb(),
                              color.specular.get_rgb(),
                              color.ambient.get_rgb(),
                              color.shininess)
        self.materials.append((name, color))

        return name

    def set_shading_mode(self, mode):
        mm = ogre.MaterialManager.getSingleton()

        for m, c in self.materials:
            material = mm.getByName(m)
            material.setShadingMode(mode)

    def reset(self):
        '''
        Remove all materials from cache.
        '''
        for name, color in self.materials:
            ignore(color)
            destroy_material(name)
       
        self.materials = []
