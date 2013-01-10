from procodile.procedural import BaseGenerator
from procodile.loader import get_class
from chair_leg import CylispheLeg
from chair_leg import ChairLeg
from chair_base import ChairBase
from chair_base import RoundBase
from chair_base import FlowerBase
from chair_backrest import ChairBackRest
from chair_backrest import BarBackRest

class Chair(BaseGenerator):

    CONFIG = (
                 'width', (0.3, 1.0),
                 'leg_height', (0.1, 1),
                 'leg_thickness', (0.01, 0.1),
                 'back_rest_height', (0.0, 1.0),
                 'back_rest_thickness', (0.02, 0.1),
                 'base_length', (0.4, 0.7),
                 'base_thickness', (0.02, 0.1),
                 'leg_type', ['square', 'round', 'triangular'],
                 'leg_placement_offset', (.8, 1),
             )

    SUB_GENERATORS = {
                        'leg': ChairLeg,
                        'comp_leg': CylispheLeg,
                        'base': ChairBase,
                        'round_base': RoundBase,
                        'flower_base': FlowerBase,
                        'back_rest': ChairBackRest,
                        'bar_back': BarBackRest
                     }

    def generate(self, config):

        # create legs
        x_translate_by = config.width - config.leg_thickness
        y_translate_by = config.base_length - config.leg_thickness


        self.subgen('comp_leg', (0, 0, 0),
                    config.leg_height, config.leg_thickness)# front-left leg

        self.subgen('comp_leg', (x_translate_by, 0, 0),
                    config.leg_height, config.leg_thickness)# front-right leg

        self.subgen('comp_leg', (0, y_translate_by, 0),
                    config.leg_height, config.leg_thickness)# back-left leg

        self.subgen('comp_leg', (x_translate_by, y_translate_by, 0),
                    config.leg_height, config.leg_thickness)# back-right leg

        # create base
        self.subgen('flower_base', (0, 0, config.leg_height),
                    config.width, config.base_length, config.base_thickness,
                    config.back_rest_thickness)

        # create back rest
        origin = (0, config.base_length - config.back_rest_thickness,
                  config.leg_height + config.base_thickness)
        self.subgen('bar_back', origin,
                             config.width, config.back_rest_thickness,
                             config.back_rest_height)
        
