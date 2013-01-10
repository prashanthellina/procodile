'''
Materials and textures handling.

G{importgraph}
'''

class Texture:
    '''
    Represents a texture to be used as a part
    of a material definition.
    '''

    def __init__(self, fpath):
        self.fpath = fpath

    def load(self):
        '''
        Load the texture from fpath into memory.
        '''
        pass

    def __eq__(self, other):
        if isinstance(other, (str, unicode)):
            return self.fpath == other

        else:
            return self.fpath == other.fpath

    def __hash__(self):
        return hash(self.fpath)

class Material(object):
    '''
    Represents a material that can be applied to the surface
    of a geom created using the draw module.
    '''

    # Filtering modes
    LINEAR = 0
    BILINEAR = 1
    TRILINEAR = 2
    ANISOTROPIC = 3

    def __init__(self, **kwargs):

        self.name = None

        self.ambient = (0.1, 0.1, 0.1)
        self.diffuse = (0.4, 0.4, 0.4)
        self.emissive = (0.0, 0.0, 0.0)
        self.specular = (0.1, 0.1, 0.1)
        self.shininess = 0.1

        self._texture = Texture(None)
        self.num_mipmaps = 0
        self.address_mode = 'wrap' #: 'clamp', 'mirror'
        self.filtering_mode = self.BILINEAR
        self.scroll = (0.0, 0.0)
        self.rotate = 0
        self.scale = (1.0, 1.0)
       
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def _get_texture(self):
        return self._texture

    def _set_texture(self, texture):
        if not isinstance(texture, Texture):
            texture = Texture(texture)

        self._texture = texture

    texture = property(_get_texture, _set_texture)

    def _canonical_form(self):
        s = self
        return (s.ambient, s.diffuse, s.emissive, s.specular, s.shininess,
                s.texture.fpath, s.num_mipmaps, s.address_mode,
                s.filtering_mode, s.scroll, s.rotate, s.scale)

    def __eq__(self, other):
        return self._canonical_form() == other._canonical_form()

    def __hash__(self):
        return hash(self._canonical_form())

    def _pick_ntuple(self, t, picker):
        if isinstance(t, list):
            return picker.pick(t)

        elif isinstance(t, tuple):
            return tuple(picker.pick(x) for x in t)

        else:
            return t

    def __pick__(self, picker):

        m = Material(name=self.name)
        
        m.ambient = self._pick_ntuple(self.ambient, picker)
        m.diffuse = self._pick_ntuple(self.diffuse, picker)
        m.emissive = self._pick_ntuple(self.emissive, picker)
        m.specular = self._pick_ntuple(self.specular, picker)
        m.shininess = picker.pick(self.shininess)

        m.texture = picker.pick(self.texture)
        m.num_mipmaps = picker.pick(self.num_mipmaps)
        m.address_mode = picker.pick(self.address_mode)
        m.filtering_mode = picker.pick(self.filtering_mode)
        m.scroll = self._pick_ntuple(self.scroll, picker)
        m.rotate = picker.pick(self.rotate)
        m.scale = self._pick_ntuple(self.scale, picker)

        return m
