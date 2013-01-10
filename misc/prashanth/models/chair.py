
from procodile.procedural import BaseGenerator
import procodile.draw as draw

class Chair(BaseGenerator):

    CONFIG = (
                 'width', (0.3, 1.0),
                 'leg_height', (0.1, 1),
                 'leg_thickness', (0.01, 0.1),
                 'back_rest_height', (0.0, 1.0),
                 'back_rest_thickness', (0.02, 0.1),
                 'base_length', (0.2, 4),
                 'base_thickness', (0.02, 0.1),
                 'leg_type', ['square', 'round', 'triangular'],
                 'leg_placement_offset', (.8, 1),
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):
    
        # create four legs
        legs = []

        for i in xrange(4):
            leg = draw.makeBox(config.leg_thickness,
                               config.leg_thickness,
                               config.leg_height)
            legs.append(leg)

        x_translate_by = config.width - config.leg_thickness
        y_translate_by = config.base_length - config.leg_thickness

        legs[1].translate((x_translate_by, 0, 0)) # front-right leg
        legs[2].translate((0, y_translate_by, 0)) # back-left leg
        legs[3].translate((x_translate_by, y_translate_by, 0)) # back-right leg

        self.add_geoms(legs)

        # create base
        base = draw.makeBox(config.width, config.base_length, config.base_thickness)
        base.translate((0, 0, config.leg_height))
        self.add_geoms(base)

        # create back rest
        back_rest = draw.makeBox(config.width,
                                 config.back_rest_thickness,
                                 config.back_rest_height)
        back_rest.translate((0,
                             config.base_length - config.back_rest_thickness,
                             config.leg_height + config.base_thickness))
        self.add_geoms(back_rest)

