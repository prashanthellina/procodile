import procodile.draw as draw
from procodile.procedural import BaseGenerator

class Level3(BaseGenerator):

    CONFIG = (
                'length', 10,
                'width', 10,
                'height', 10,
             )

    def generate(self, config):

            C = config
            C.num_levels = None
            box = draw.makeBox(C.length, C.width, C.height)
            self.add_geoms(box)

class Level2(BaseGenerator):

    CONFIG = (
                'length', 10,
                'width', 10,
                'height', 10,
             )

    SUB_GENERATORS = {
                        'level3': Level3
                     }
    def generate(self, config):

            C = config
            C.num_levels = None
            box = draw.makeBox(C.length, C.width, C.height)
            self.add_geoms(box)

            self.subgen('level3', (0,0,20))

class Level1(BaseGenerator):

    CONFIG = (
                'length', 10,
                'width', 10,
                'height', 10,
             )

    SUB_GENERATORS = {
                        'level2': Level2
                     }
    def generate(self, config):

            C = config
            C.num_levels = None
            box = draw.makeBox(C.length, C.width, C.height)
            self.add_geoms(box)

            self.subgen('level2', (0,0,20))

class Level0(BaseGenerator):

    CONFIG = (
                'length', 10,
                'width', 10,
                'height', 10,
             )

    SUB_GENERATORS = {
                        'level1': Level1
                     }
    def generate(self, config):

            C = config
            C.num_levels = None
            box = draw.makeBox(C.length, C.width, C.height)
            self.add_geoms(box)

            self.subgen('level1', (0,0,20))




