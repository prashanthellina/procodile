'''
Building model and generator.

G{importgraph}
'''

from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw
import math

from level import Generator as LevelGenerator

class Generator(BaseGenerator):
        
    CONFIG = (
                'length', (20, 40),
                'width', (20, 40),
                'num_levels', (1, 1),
                'height', (10, 500),
                'slab_height', (0.1, 0.3),
                'level_height', (3, 5),
                'corridor_length', (4, 6),
                'corridor_width', (4, 6),
                'wall_thickness', (.1, .3),
             )

    SUB_GENERATORS = {
                        'level': LevelGenerator
                     }

    def generate(self, config):
       
        C = config
        C.num_levels = None
        box = draw.makeBox(C.length, C.width, C.height)
        building_id = self.get_material('building', M(texture='building.jpg'))
        x = C.length/100.0
        y = C.height/100.0
        box.set_material(building_id, texture_coords=[(x, 0.0), (x, y), (0.0, y), (0.0, 0.0)], face='front')
        box.set_material(building_id, texture_coords=[(x, 0.0), (x, y), (0.0, y), (0.0, 0.0)], face='left')
        box.set_material(building_id, texture_coords=[(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)], face='right')
        box.set_material(building_id, texture_coords=[(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)], face='back')
        self.add_geoms(box)
        return
        num_levels, slab_height, level_height = \
            self.compute_height_params(self.picker,
                                       C.height,
                                       C.slab_height,
                                       C.level_height,
                                       C.num_levels)

        for i in xrange(num_levels):
            zoffset = (slab_height + level_height) * i
            slab = draw.makeBox(C.length, C.width, slab_height)
            origin = (0, 0, zoffset)
            slab.translate(origin)
            self.add_geom(slab)

        for i in xrange(num_levels):
            zoffset = slab_height + \
                        (slab_height + level_height) * i
                        
            origin = (0, 0, zoffset)
            self.subgen('level', origin,
                        C.length, C.width, level_height, None,
                        C.wall_thickness, C.corridor_length,
                        C.corridor_width)

    def compute_height_params(self, P, height, slab_height,
                                level_height, num_levels):
        if height and num_levels:
            raise Exception('please specify height or num_levels')

        if height:
            num_levels = height / (slab_height + level_height)
         
        return num_levels, slab_height, level_height

class CurvedBuilding(BaseGenerator):

    CONFIG = (
                'length', (20, 40),
                'width', (20, 40),
                'num_levels', (1, 1),
                'height', (10, 500),
                'slab_height', (0.1, 0.3),
                'level_height', (3, 5),
                'corridor_length', (4, 6),
                'corridor_width', (4, 6),
                'wall_thickness', (.1, .3),
             )

    def generate(self, config):

        C = config

#        C.length = 6
#        C.width = 7
#        C.height = 12
        print C.length, C.width, C.height

        curve_len = C.width/2. if C.width < C.length else C.length/2.

        V1 = (curve_len,0,0)
        V2 = (C.length-curve_len, 0, 0)
        V3 = (C.length-curve_len, C.width, 0)
        V4 = (curve_len, C.width, 0)

        VC1 = (0, curve_len, 0)
        C1 = draw.Arc(V1,VC1,V4).unwrap()

        VC2 = (C.length, curve_len, 0)
        C2 = draw.Arc(V2,VC2,V3).unwrap()
        
        L1 = None
        L2 = None
        
        if V1 != V2:
            L1 = draw.Line(V1,V2).unwrap()
        if V4 != V3:
            L2 = draw.Line(V4,V3).unwrap()

        S1 = draw.Shape([C1, C2, L1, L2])
        W = draw.Wire(S1.Edges)
        F = draw.Face(W)
        self.add_geoms(F)
        aTrsf=draw.Matrix()
        aTrsf.rotateX(math.pi)
        aTrsf.move((0,0,curve_len*2))
        F1=F.transform(aTrsf)
#        P = F.extrude((0, 0, C.height))

        self.add_geoms(F1)

class Block(BaseGenerator):

    CONFIG = (
                'length', (40, 80),
                'width', (20, 40),
                'height', (10, 50),
             )

    def generate(self, config):
        C = config
        try:
            box = draw.makeBox(C.length, C.width, C.height)
            building_id = self.get_material('building', M(texture='building.jpg'))
            x = C.length/100.0
            y = C.height/100.0
            box.set_material(building_id, texture_coords=[(x, 0.0), (x, y), (0.0, y), (0.0, 0.0)], face='front')
            box.set_material(building_id, texture_coords=[(x, 0.0), (x, y), (0.0, y), (0.0, 0.0)], face='left')
            box.set_material(building_id, texture_coords=[(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)], face='right')
            box.set_material(building_id, texture_coords=[(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)], face='back')
            self.add_geoms(box)

        except:
            print 'length of box too small ', C.length, C.width, C.height

class Park(BaseGenerator):
    CONFIG = (
                'length', (80, 150),
                'width', (40,80),
                'height', (40,80),
             )

    def generate(self, config):
        C = config
        try:
            park = draw.makeBox(C.length, C.width, C.height)
            park_id = self.get_material('grass', M(texture='grass.jpg'))
            x = self.picker.pick((1.0))
            park.set_material(park_id, texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)])
            self.add_geoms(park)
        except:
            print 'length of box too small ', C.length, C.width, C.height

class LBuildings(BaseGenerator):

    CONFIG = (
                'total_length', (80, 150),
                'total_width', (40,80),
                'length', (40, 80),
                'width', (20, 40),
                'height', (10, 50),
                'num_blocks', (2, 6),
                'blocks', [['FL', 'FM', 'FR', 'BL', 'BM', 'BR'],],
             )

    SUB_GENERATORS = {
                        'block':Block,
                        'park': Park
                     }

    def generate(self, config):
        C = config
        self._width = C.total_width/4
        self._length = C.total_length
        self.center = C.total_width/2 - self._width/2

        self.subgen('block', (0, self.center, 0), self._length, self._width, C.height)

        self.blocks = []
        config_blocks = C.blocks[:]
        for i in xrange(C.num_blocks):
            b = self.picker.pick(config_blocks)
            self.blocks.append(b)
            config_blocks.remove(b)

        self.block_length = self.center
        self.block_width = C.total_length/4
        self.block_height = C.height

        self.add_blocks()
        self.add_parks()

    def add_blocks(self):
        for block in self.blocks:
            location = self.get_block_location(block)
            self.subgen('block', location, self.block_length, self.block_width,
                        self.block_height)

    def get_block_location(self, block):
        location = None
        s = self

        if block == 'FL':
            location = ((0,s.center,0), (-math.pi / 2, (0, 0, 1)))

        elif block == 'FM':
            location = ((s._length/2-s.block_width/2,s.center,0),
                        (-math.pi / 2, (0, 0, 1)))

        elif block == 'FR':
            location = ((s._length-s.block_width,s.center,0),
                        (-math.pi / 2, (0, 0, 1)))

        elif block == 'BR':
            location = ((s._length,s._width+s.center,0), (math.pi / 2, (0, 0, 1)))

        elif block == 'BM':
            location = ((s._length/2+s.block_width-s.block_width/2,s._width+s.center,0),
                        (math.pi / 2, (0, 0, 1)))

        elif block == 'BL':
            location = ((0+s.block_width,s._width+s.center,0),
                        (math.pi / 2, (0, 0, 1)))

        return location

    def add_parks(self):
        C = self.config
        s = self

        min_park_space = C.total_length - s.block_width*3
        
        fp1_origin = (0, 0, 0)
        fp1_length = C.total_length
        fp1_width = s.center

        fp2_origin = (s.block_width*2 + min_park_space/2, 0, 0)
        fp2_length = None
        fp2_width = s.center

        bp1_origin = ((C.total_length, C.total_width, 0),  (math.pi, (0, 0, 1)))
        bp1_length = C.total_length
        bp1_width = s.center

        bp2_origin = ((C.total_length-s.block_width*2 - min_park_space/2, C.total_width, 0), (math.pi, (0, 0, 1)))
        bp2_length = None
        bp2_width = s.center

        fp2_length = bp2_length = C.total_length - (s.block_width*2 + min_park_space/2)
        

        if 'FL' in s.blocks:
            fp1_origin = (s.block_width, 0, 0)
            fp1_length -= s.block_width

        if 'FR' in s.blocks:
            fp1_length -= s.block_width
            fp2_length -= s.block_width

        if 'FM' in s.blocks:
            if 'FR' in s.blocks:
                fp1_length = fp1_length - (s.block_width + min_park_space/2)
            else:
                fp1_length = fp1_length - (s.block_width*2 + min_park_space/2)
            if fp1_length < min_park_space/2:
                fp1_length = min_park_space/2
            if fp1_length > s.block_width + min_park_space/2:
                fp1_length -= s.block_width

        if 'BR' in s.blocks:
            bp1_origin = ((C.total_length - s.block_width, C.total_width, 0),  (math.pi, (0, 0, 1)))
            bp1_length -= s.block_width

        if 'BL' in s.blocks:
            bp1_length -= s.block_width
            bp2_length -= s.block_width

        if 'BM' in s.blocks:
            if 'BL' in s.blocks:
                bp1_length = bp1_length - (s.block_width + min_park_space/2)
            else:
                bp1_length = bp1_length - (s.block_width*2 + min_park_space/2)
            if bp1_length < min_park_space/2:
                bp1_length = min_park_space/2
            if bp1_length > s.block_width + min_park_space/2:
                bp1_length -= s.block_width

        self.subgen('park', fp1_origin, fp1_length, fp1_width, 0.1)
        if 'FM' in s.blocks:
            self.subgen('park', fp2_origin, fp2_length, fp2_width, 0.1)

        self.subgen('park', bp1_origin, bp1_length, bp1_width, 0.1)
        if 'BM' in s.blocks:
            self.subgen('park', bp2_origin, bp2_length, bp2_width, 0.1)
            