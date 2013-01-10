from procodile.procedural import BaseGenerator
import procodile.draw as draw

class ChairLeg(BaseGenerator):
    CONFIG = (
                 'leg_height', (0.1, 1),
                 'leg_thickness', (0.01, 0.1),
                 'type',['square', 'cylinder', 'triangular']
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):
        if config.type == 'square':
            leg = draw.makeBox(config.leg_thickness,
                               config.leg_thickness,
                               config.leg_height)

        elif config.type == 'cylinder':
            origin = (config.leg_thickness/2,config.leg_thickness/2,0)
            leg = draw.makeCylinder(config.leg_thickness/2,
                                    config.leg_height, origin)

        elif config.type == 'triangular':
            leg = draw.makePolygon([(config.leg_thickness,0,0),(0,config.leg_thickness,0),(0,0,0)])
            leg = leg.extrude((0,0,config.leg_height))

        self.add_geoms(leg)

class ChairBase(BaseGenerator):
    CONFIG = (
                 'width', (0.3, 1.0),
                 'base_length', (0.2, 4),
                 'base_thickness', (0.02, 0.1)
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):

        base = draw.makeBox(config.width, config.base_length, config.base_thickness)
        self.add_geoms(base)

class ChairBackRest(BaseGenerator):
    CONFIG = (
                 'width', (0.3, 1.0),
                 'back_rest_thickness', (0.02, 0.1),
                 'back_rest_height', (0.0, 1.0)
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):

        back_rest = draw.makeBox(config.width,
                                 config.back_rest_thickness,
                                 config.back_rest_height)

        self.add_geoms(back_rest)

class Chair(BaseGenerator):

    CONFIG = (
                 'width', (0.3, 1.0),
                 'leg_height', (0.1, 1),
                 'leg_thickness', (0.01, 0.1),
                 'back_rest_height', (0.0, 1.0),
                 'back_rest_thickness', (0.02, 0.1),
                 'base_length', (0.4, 0.7),
                 'base_thickness', (0.02, 0.1),
                 'leg_type', ['square', 'cylinder', 'triangular'],
             )

    SUB_GENERATORS = (
                        'leg', ChairLeg,
                        'base', ChairBase,
                        'back_rest', ChairBackRest,
                     )

    def generate(self, config):

        # create legs
        x_translate_by = config.width - config.leg_thickness
        y_translate_by = config.base_length - config.leg_thickness


        self.subgen('leg', (0, 0, 0),
                    config.leg_height, config.leg_thickness,
                    config.leg_type)# front-left leg

        self.subgen('leg', (x_translate_by, 0, 0),
                    config.leg_height, config.leg_thickness,
                    config.leg_type)# front-right leg

        self.subgen('leg', (0, y_translate_by, 0),
                    config.leg_height, config.leg_thickness,
                    config.leg_type)# back-left leg

        self.subgen('leg', (x_translate_by, y_translate_by, 0),
                    config.leg_height, config.leg_thickness,
                    config.leg_type)# back-right leg

        # create base
        self.subgen('base', (0, 0, config.leg_height),
                    config.width, config.base_length, config.base_thickness)

        # create back rest
        origin = (0, config.base_length - config.back_rest_thickness,
                  config.leg_height + config.base_thickness)
                  
        self.subgen('back_rest', origin, config.width,
                    config.back_rest_thickness, config.back_rest_height)