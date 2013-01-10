# RECIPE 1.0
from procodile.recipe import RecipeConfig

D = 'A Flower Chair Recipe'

G = (
    ('chair', '../models/chair', 'chair.Chair', None),
    ('simpleleg', '../models/chair', 'chair_leg.ChairLeg', None),
    ('comp_leg', '../models/chair', 'chair_leg.CylispheLeg', None),
    ('bar_back', '../models/chair', 'chair_backrest.BarBackRest', None),
    ('base', '../models/chair', 'chair_base.ChairBase', None),
    ('flower_base', '../models/chair', 'chair_base.FlowerBase', None)
    )

M = (
    ('chair', '/chair'),
    )

O = (
    ('chair', ('seed', '5555')),
    )

data = {'description': D, 'generators': G, 'matches': M, 'onmatches': O}
recipe = RecipeConfig(__file__, data)
Generator = recipe.make_generator()
