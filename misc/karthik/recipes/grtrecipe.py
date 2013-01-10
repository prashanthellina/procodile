# RECIPE 1.0
from procodile.recipe import RecipeConfig

D = 'A Flower Chair Recipe'

G = (
    ('chair', '../recipes', 'chair1.Generator', None),
    )

M = (
    ('chair', '/chair'),
    )

O = (
    ('chair', ('seed', '2222')),
    )

data = {'description': D, 'generators': G, 'matches': M, 'onmatches': O}
recipe = RecipeConfig(__file__, data)
Generator = recipe.make_generator()
