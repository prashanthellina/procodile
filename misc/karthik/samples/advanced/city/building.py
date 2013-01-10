'''
Building model and generator.

G{importgraph}
'''

import math

from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw

from tree import Tree

class Generator(BaseGenerator):
        
    CONFIG = (
                'length', (20, 40),
                'width', (20, 40),
                'height', (10, 500),
             )

    SUB_GENERATORS = {
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

class CurvedBlock(BaseGenerator):

    CONFIG = (
                'length', (20, 40),
                'width', (20, 40),
                'height', (10, 500),
                'pavement', (0, 14)
             )

    pavements = [
        ('textures/pavement_0.jpg', .4),
        ('textures/pavement_1.jpg', .4),
        ('textures/pavement_2.jpg', .4),
        ('textures/pavement_3.jpg', .4),
        ('textures/pavement_4.jpg', .4),
        ('textures/pavement_5.jpg', .4),
        ('textures/pavement_6.jpg', .4),
        ('textures/pavement_7.jpg', .4),
        ('textures/pavement_8.jpg', .4),
        ('textures/pavement_9.jpg', .4),
        ('textures/pavement_10.jpg', .4),
        ('textures/pavement_11.jpg', .4),
        ('textures/pavement_12.jpg', .4),
        ('textures/pavement_13.jpg', .4),
        ('textures/pavement_14.jpg', .4),
        ('textures/pavement_15.jpg', .4),

    ]

    def register_materials(self):
        for index, (fname, size) in enumerate(self.pavements):
            mat_name = 'pavement_%s' % index
            mat_id = self.get_material(mat_name)
            if not mat_id:
                self.register_material(mat_name, M(texture=fname))

    def generate(self, config):
        C = config
        self.register_materials()

        fp_id = self.get_material('pavement_%s' % C.pavement)
        size = self.pavements[C.pavement][-1]
        tx = C.length/size
        ty = C.width/size

        texture_coords=[(tx, 0.0), (tx, ty), (0.0, ty), (0.0, 0.0)]

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
#        self.add_geoms(F)
#        aTrsf=draw.Matrix()
#        aTrsf.rotateX(math.pi)
#        aTrsf.move((0,0,curve_len*2))
#        F1=F.transform(aTrsf)
        block = F.extrude((0, 0, C.height))

        block.set_material(fp_id, 'left', texture_coords)
        block.set_material(fp_id, 'right', texture_coords)
        block.set_material(fp_id, 'front', texture_coords)
        block.set_material(fp_id, 'back', texture_coords)

        x = self.picker.pick((0.1, 1000.0))
        texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)]
        sand_id = self.get_material('sand', M(texture='textures/grass.jpg'))
        block.set_material(sand_id, 'top', texture_coords = texture_coords)

        self.add_geoms(block)

class Block(BaseGenerator):

    CONFIG = (
                'length', (40, 80),
                'width', (20, 40),
                'height', (10, 50),
                'terrace', (0, 4),
                'facade', (0, 9),
             )

    terraces = [
        ('textures/floor_0.jpg', 2.),
        ('textures/floor_1.jpg', 2.),
        ('textures/floor_2.jpg', 2.),
        ('textures/floor_3.jpg', 2.),
        ('textures/floor_4.jpg', 2.),
    ]

    facades = [
        ('textures/building_0.jpg', 4.),
        ('textures/building_2.jpg', 6.),
        ('textures/building_3.jpg', 16.),
        ('textures/building_4.jpg', 6.),
        ('textures/building_5.jpg', 10.),
        ('textures/building_6.jpg', 12.),
        ('textures/building_8.jpg', 18.),
        ('textures/building_9.jpg', 12.),
        ('textures/building_10.jpg', 12.),
        ('textures/building_11.jpg', 12.),
    ]

    def register_materials(self):

        for index, (fname, size) in enumerate(self.terraces):
            mat_name = 'terrace_%s' % index
            mat_id = self.get_material(mat_name)
            if not mat_id:
                self.register_material(mat_name, M(texture=fname))

        for index, (fname, size) in enumerate(self.facades):
            mat_name = 'facade_%s' % index
            mat_id = self.get_material(mat_name)
            if not mat_id:
                self.register_material(mat_name, M(texture=fname))


    def generate(self, config):
        C = config
        self.register_materials()

        try:
            box = draw.makeBox(C.length, C.width, C.height)
        except:
            print 'length of box too small ', C.length, C.width, C.height
            raise
        building_id = self.get_material('facade_%s' % C.facade)
        size = self.facades[C.facade][-1]
        x = C.length/size
        y = C.height/size

        texture_coords=[(x, 0.0), (x, y), (0.0, y), (0.0, 0.0)]
        box.set_material(building_id, 'front', texture_coords)

        texture_coords=[(x, 0.0), (x, y), (0.0, y), (0.0, 0.0)]
        box.set_material(building_id, 'left', texture_coords)

        texture_coords=[(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)]
        box.set_material(building_id, 'right', texture_coords)

        texture_coords=[(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)]
        box.set_material(building_id, 'back', texture_coords)

        size = self.terraces[C.terrace][-1]
        x = C.length/size
        y = C.width/size
        texture_coords=[(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)]

        terrace_id = self.get_material('terrace_%s' % C.terrace)
        box.set_material(terrace_id, 'top', texture_coords)

        self.add_geoms(box)

class Park(BaseGenerator):
    CONFIG = (
                'length', (80, 150),
                'width', (40,80),
                'height', (0.2, 2),
                'right_open', [True, False],
                'left_open', [True, False],
                'park_style', ['line_park', 'middle_tree', 'block_park'],
                'pavement', (0, 9)
             )

    SUB_GENERATORS = {
                        'tree': Tree,
                        'curve_block': CurvedBlock
                     }

    pavements = [
        ('textures/pavement_0.jpg', .4),
        ('textures/pavement_1.jpg', .4),
        ('textures/pavement_2.jpg', .4),
        ('textures/pavement_3.jpg', .4),
        ('textures/pavement_4.jpg', .4),
        ('textures/pavement_5.jpg', .4),
        ('textures/pavement_6.jpg', .4),
        ('textures/pavement_7.jpg', .4),
        ('textures/pavement_8.jpg', .4),
        ('textures/pavement_9.jpg', .4),
        ('textures/pavement_10.jpg', .4),
        ('textures/pavement_11.jpg', .4),
        ('textures/pavement_12.jpg', .4),
        ('textures/pavement_13.jpg', .4),
        ('textures/pavement_14.jpg', .4),
        ('textures/pavement_15.jpg', .4),

    ]

    def register_materials(self):
        for index, (fname, size) in enumerate(self.pavements):
            mat_name = 'pavement_%s' % index
            mat_id = self.get_material(mat_name)
            if not mat_id:
                self.register_material(mat_name, M(texture=fname))

    def generate(self, config):
        C = config
        self.register_materials()

        platform_id = self.get_material('pavement_%s' % C.pavement)
        size = self.pavements[C.pavement][-1]
        tx = C.length/size
        ty = C.width/size
        platform_coords=[(tx, 0.0), (tx, ty), (0.0, ty), (0.0, 0.0)]

        tree_dia = C.length/8.
        tree_height = self.picker.pick(1, 5)
        if C.park_style == 'line_park':

            line = draw.Line((C.length-tree_dia, tree_dia, 0),
                                (tree_dia, tree_dia, 0))
            line = draw.Shape([line.unwrap()])
            park = line.extrude((0, C.width-tree_dia*2, 0))

            park_id = self.get_material('grass',
                                        M(texture='textures/grass.jpg'))
            park.set_material(park_id, texture_coords = platform_coords)

            self.add_geoms(park)

            length = C.length

            width = C.width - 2


            x, y, z = 0.5, 0.5, 0
            while length > tree_dia:
                length = length - (tree_dia + 2)
                x = x + tree_dia + 1
                self.subgen('tree', (x, y, z), tree_dia, tree_height)
    #                self.subgen('tree', (x, C.width-y, z), htree_dia, tree_height)


            x, y, z = 0.5, 0.5, 0
            while width > tree_dia:
                width = width - (tree_dia + 2)
                y = y + tree_dia + 1
                if C.left_open:
                    self.subgen('tree', (x, y, z), tree_dia, tree_height)
                if C.right_open:
                    self.subgen('tree', (C.length-x, y, z), tree_dia, tree_height)
        
        elif C.park_style == 'middle_tree':
            tree_dia = C.length/8.
            line = draw.Line((C.length, 0, 0),
                                (0, 0, 0))
            line = draw.Shape([line.unwrap()])
            park = line.extrude((0, C.width, 0))

            park_id = self.get_material('grass',
                                        M(texture='textures/grass.jpg'))
            park.set_material(park_id, texture_coords = platform_coords)

            self.add_geoms(park)

            self.subgen('tree', (C.length/2., C.width/2., 0), tree_dia, tree_height)

        elif C.park_style == 'block_park':
            block_dia = C.width/10.

            line = draw.Line((C.length-block_dia, block_dia, 0),
                                (block_dia, block_dia, 0))
            line = draw.Shape([line.unwrap()])
            platform = line.extrude((0, C.width-block_dia*2, 0))

            platform.set_material(platform_id, texture_coords = platform_coords)
            self.add_geoms(platform)

            height = self.picker.pick(0.3, 0.8)
            self.subgen('curve_block', (1, 0, 0), C.length/3., block_dia, height)
            self.subgen('curve_block', (C.length-C.length/3.-1, 0, 0), C.length/3., block_dia, height)
            if C.left_open:
                origin = ((1, 1+C.width/10., 0), (math.pi/2, (0, 0, 1)))
                self.subgen('curve_block', origin, C.width/3., block_dia, height)
                origin = ((1, C.width - C.width/3.-1, 0), (math.pi/2, (0, 0, 1)))
                self.subgen('curve_block', origin, C.width/3., block_dia, height)
            if C.right_open:
                origin = ((C.length-1, 1+C.width/10., 0), (math.pi/2, (0, 0, 1)))
                self.subgen('curve_block', origin, C.width/3., block_dia, height)
                origin = ((C.length-1, C.width - C.width/3.-1, 0), (math.pi/2, (0, 0, 1)))
                self.subgen('curve_block', origin, C.width/3., block_dia, height)


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
        self._width = C.total_width/4.
        self._length = C.total_length
        self.center = C.total_width/2. - self._width/2.

        terrace = self.picker.pick((0, len(Block.terraces)-1))
        facade = self.picker.pick((0, len(Block.facades)-1))

        self.subgen('block', (0, self.center, 0),
                    self._length, self._width, C.height,
                    terrace, facade)

        self.blocks = []
        config_blocks = C.blocks[:]
        for i in xrange(C.num_blocks):
            b = self.picker.pick(config_blocks)
            if not b:
                continue
            self.blocks.append(b)
            config_blocks.remove(b)

        self.block_length = self.center
        self.block_width = C.total_length/4.
        self.block_height = C.height

        self.add_blocks(terrace, facade)
        self.add_parks()

    def add_blocks(self, terrace, facade):
        for block in self.blocks:
            location = self.get_block_location(block)
            self.subgen('block', location, self.block_length, self.block_width,
                        self.block_height, terrace, facade)

    def get_block_location(self, block):
        location = None
        s = self

        if block == 'FL':
            location = ((0,s.center,0), (-math.pi/2, (0, 0, 1)))

        elif block == 'FM':
            location = ((s._length/2.-s.block_width/2.,s.center,0),
                        (-math.pi/2, (0, 0, 1)))

        elif block == 'FR':
            location = ((s._length-s.block_width,s.center,0),
                        (-math.pi/2, (0, 0, 1)))

        elif block == 'BR':
            location = ((s._length,s._width+s.center,0), (math.pi/2, (0, 0, 1)))

        elif block == 'BM':
            location = ((s._length/2.+s.block_width-s.block_width/2.,
                        s._width+s.center,0), (math.pi/2, (0, 0, 1)))

        elif block == 'BL':
            location = ((0+s.block_width,s._width+s.center,0),
                        (math.pi/2, (0, 0, 1)))

        return location

    def add_parks(self):
        C = self.config
        s = self

        min_park_space = C.total_length - s.block_width*3
        park_height = 0.05
        
        fp1_origin = (0, 0, park_height)
        fp1_length = C.total_length
        fp1_width = s.center

        fp2_origin = (s.block_width*2 + min_park_space/2., 0, park_height)
        fp2_length = None
        fp2_width = s.center

        bp1_origin = ((C.total_length, C.total_width, park_height),
                      (math.pi, (0, 0, 1)))
        bp1_length = C.total_length
        bp1_width = s.center

        bp2_origin = ((C.total_length-s.block_width*2 - min_park_space/2.,
                      C.total_width, park_height), (math.pi, (0, 0, 1)))
        bp2_length = None
        bp2_width = s.center

        fp2_length = bp2_length = C.total_length - \
                                    (s.block_width*2 + min_park_space/2.)
        

        if 'FL' in s.blocks:
            fp1_origin = (s.block_width, 0, park_height)
            fp1_length -= s.block_width

        if 'FR' in s.blocks:
            fp1_length -= s.block_width
            fp2_length -= s.block_width

        if 'FM' in s.blocks:
            if 'FR' in s.blocks:
                fp1_length = fp1_length - (s.block_width + min_park_space/2.)
            else:
                fp1_length = fp1_length - (s.block_width*2 + min_park_space/2.)

            if fp1_length > s.block_width + min_park_space/2.:
                fp1_length -= s.block_width

        if 'BR' in s.blocks:
            bp1_origin = ((C.total_length - s.block_width, C.total_width,
                           park_height), (math.pi, (0, 0, 1)))
            bp1_length -= s.block_width

        if 'BL' in s.blocks:
            bp1_length -= s.block_width
            bp2_length -= s.block_width

        if 'BM' in s.blocks:
            if 'BL' in s.blocks:
                bp1_length = bp1_length - (s.block_width + min_park_space/2.)
            else:
                bp1_length = bp1_length - (s.block_width*2 + min_park_space/2.)
            
            if bp1_length > s.block_width + min_park_space/2.:
                bp1_length -= s.block_width


        right_open = False
        left_open = False
        if fp1_length == C.total_length:
            right_open = True
        if fp1_origin == (0, 0, park_height):
            left_open = True
        self.subgen('park', fp1_origin, fp1_length, fp1_width, 2, right_open, left_open)

        right_open = False
        if 'FM' in s.blocks:
            if fp2_length > min_park_space/2.:
                right_open = True
            self.subgen('park', fp2_origin, fp2_length, fp2_width, 2, right_open, False)

        right_open = False
        left_open = False
        if bp1_length == C.total_length:
            right_open = True
        if bp1_origin == (0, 0, park_height):
            left_open = True
        self.subgen('park', bp1_origin, bp1_length, bp1_width, 2, right_open, left_open)

        right_open = False
        if 'BM' in s.blocks:
            if bp2_length > min_park_space/2.:
                right_open = True
            self.subgen('park', bp2_origin, bp2_length, bp2_width, 2, right_open, False)

class Pavement(BaseGenerator):

    CONFIG = (
                 'length', (50, 100),
                 'width', (2, 10),
                 'pavement', (0, 14),
             )

    SUB_GENERATORS = {
                     }

    pavements = [
        ('textures/pavement_0.jpg', .4),
        ('textures/pavement_1.jpg', .4),
        ('textures/pavement_2.jpg', .4),
        ('textures/pavement_3.jpg', .4),
        ('textures/pavement_4.jpg', .4),
        ('textures/pavement_5.jpg', .4),
        ('textures/pavement_6.jpg', .4),
        ('textures/pavement_7.jpg', .4),
        ('textures/pavement_8.jpg', .4),
        ('textures/pavement_9.jpg', .4),
        ('textures/pavement_10.jpg', .4),
        ('textures/pavement_11.jpg', .4),
        ('textures/pavement_12.jpg', .4),
        ('textures/pavement_13.jpg', .4),
        ('textures/pavement_14.jpg', .4),
        ('textures/pavement_15.jpg', .4),

    ]

    def register_materials(self):
        for index, (fname, size) in enumerate(self.pavements):
            mat_name = 'pavement_%s' % index
            mat_id = self.get_material(mat_name)
            if not mat_id:
                self.register_material(mat_name, M(texture=fname))

    def generate(self, config):
        C = config
        self.register_materials()

        fp_id = self.get_material('pavement_%s' % C.pavement)
        size = self.pavements[C.pavement][-1]
        tx = C.length/size
        ty = C.width/size

        texture_coords=[(tx, 0.0), (tx, ty), (0.0, ty), (0.0, 0.0)]

        line = draw.Line((C.length, 1, 0), (C.length, 0, 0))
        line = draw.Shape([line.unwrap()])
        ff = line.extrude((-C.length, 0, 0))
        ff.set_material(fp_id, texture_coords=texture_coords)
        self.add_geom(ff)

        line = draw.Line((1, 1, 0), (0, 1, 0))
        line = draw.Shape([line.unwrap()])
        lf = line.extrude((0, C.width-2, 0))
        lf.set_material(fp_id, texture_coords=texture_coords)
        self.add_geom(lf)

        line = draw.Line((C.length, 1, 0), (C.length-1, 1, 0))
        line = draw.Shape([line.unwrap()])
        rf = line.extrude((0, C.width-2, 0))
        rf.set_material(fp_id, texture_coords=texture_coords)
        self.add_geom(rf)

        line = draw.Line((C.length, C.width, 0), (C.length, C.width-1, 0))
        line = draw.Shape([line.unwrap()])
        bf = line.extrude((-C.length, 0, 0))
        bf.set_material(fp_id, texture_coords=texture_coords)
        self.add_geom(bf)

class Base(BaseGenerator):

    CONFIG = (
                 'length', (50, 100),
                 'width', (2, 10),
                 'pavement', (0, 14)
             )

    SUB_GENERATORS = {
                        'pavement': Pavement
                     }

    pavements = [
        ('textures/pavement_0.jpg', .4),
        ('textures/pavement_1.jpg', .4),
        ('textures/pavement_2.jpg', .4),
        ('textures/pavement_3.jpg', .4),
        ('textures/pavement_4.jpg', .4),
        ('textures/pavement_5.jpg', .4),
        ('textures/pavement_6.jpg', .4),
        ('textures/pavement_7.jpg', .4),
        ('textures/pavement_8.jpg', .4),
        ('textures/pavement_9.jpg', .4),
        ('textures/pavement_10.jpg', .4),
        ('textures/pavement_11.jpg', .4),
        ('textures/pavement_12.jpg', .4),
        ('textures/pavement_13.jpg', .4),
        ('textures/pavement_14.jpg', .4),
        ('textures/pavement_15.jpg', .4),

    ]

    def register_materials(self):
        for index, (fname, size) in enumerate(self.pavements):
            mat_name = 'base_%s' % index
            mat_id = self.get_material(mat_name)
            if not mat_id:
                self.register_material(mat_name, M(texture=fname))

    def generate(self, config):
        C = config
        self.register_materials()
        plate = draw.makeBox(C.length, C.width, 0.2)
        pavement_id = self.get_material('base_%s' % C.pavement)
        size = self.pavements[C.pavement][-1]
        x = C.length/size
        y = C.width/size
        plate.set_material(pavement_id, 'front', [(x, 0.0), (x, y), (0.0, y), (0.0, 0.0)])
        plate.set_material(pavement_id, 'left', [(x, 0.0), (x, y), (0.0, y), (0.0, 0.0)])
        plate.set_material(pavement_id, 'right', [(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)])
        plate.set_material(pavement_id, 'back', [(x, y), (0.0, y), (0.0, 0.0), (x, 0.0)])

        x = self.picker.pick((0.1, 1000.0))
        texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)]
        sand_id = self.get_material('sand', M(texture='textures/sand.jpg'))
        plate.set_material(sand_id, 'top', texture_coords)
        self.add_geom(plate)

        self.subgen('pavement', (0, 0, 0.25), C.length, C.width, C.pavement)


class Test(BaseGenerator):
    CONFIG = (
                 'length', (50, 100),
                 'width', (50, 100),
                 'pavement', (0, 14)
             )

    SUB_GENERATORS = {
                        'footpath': Pavement
                     }

    def generate(self, config):
        C = config
        plate = draw.makeBox(C.length, C.width, 0.2)
        sand_id = self.get_material('sand', M(texture='textures/sand.jpg'))
        x = self.picker.pick((0.1, 1000.0))
        texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)]
        plate.set_material(sand_id, texture_coords=texture_coords)
        self.add_geom(plate)

        self.subgen('footpath', (0, 0, 0.25), C.length, C.width, C.pavement)
