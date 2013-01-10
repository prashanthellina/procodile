'''
The world and all its constituents are built from fundamental building blocks that
we will refer to as 'blocks'. Blocks can combine together in two ways 
    1) Physical (weaker bond, easier to forge and break)
    2) Chemical (stronger bond, harder to forge and break)

When a block takes part in a chemical bond, the properties of the block are no more
considered at an individual level. The 'combination' or the 'compound' will be
attributed the qualities depending on the kind, number and type of connectivity
of constituent blocks.

Each block has some fundamental properties and certain derived ones.

Fundamental properties of blocks
*) Mass (measured in kilograms)
*) Angle (measured in degrees)
*) Friction (0.0 to 1.0)
*) Attenuation (0.0 to 1.0) - Amount of energy loss at boundary
*) Maximum energy (Joules)
*) Energy absorption (0.0 to 1.0)

Geometry of each block:
Every block is an extruded isosceles triangle. The similar sides of the
triangle are of length .02 metres. The height of extrusion is also .02 metres.
The 'angle' of a block is the angle formed by the similar sides of
the triangle.

This each block has 5 surfaces (two triangles, two squares and one rectangle)

All the properties of blocks are functions of angle and group. There are 8 groups.

Each element is named accordingly. <group><angle>. eg: A2 is group = A, angle = 2
E90 is group = E, angle = 90
'''

import doctest

ANGLES = [2, 3, 5, 15, 30, 45, 60, 90]
GROUPS = list('ABCDEFGH')

def get_block_iterator(groups=GROUPS, angles=ANGLES):
    for g in groups:
        for a in angles:
            yield (g, a)

def compute_block_mass(group, angle):
    '''
    Mass of a block increases with angle

    Mass group 1 - G > E > C > A
    Mass group 2 - B > D > F > H

    >>> compute_block_mass('A', 2)
    1
    >>> compute_block_mass('A', 3)
    11
    >>> compute_block_mass('A', 5)
    21
    >>> compute_block_mass('B', 5)
    721
    >>> compute_block_mass('H', 90)
    471
    >>> compute_block_mass('D', 90)
    671

    '''
    MASS_GROUP_1 = list('GECA')
    MASS_GROUP_2 = list('BDFH')

    ANGLE_MASS_STEP = 10
    MG_STEP = 100
    MG1_BASE = 1
    MG2_BASE = 401

    if group in MASS_GROUP_1:
        group_base_mass = MG1_BASE
        index = MASS_GROUP_1.index(group)

    else:
        group_base_mass = MG2_BASE
        index = MASS_GROUP_2.index(group)
        
    index = (len(GROUPS)/2 - 1) - index
    group_mass = group_base_mass + MG_STEP * index

    index = ANGLES.index(angle)
    angle_mass = index * ANGLE_MASS_STEP

    mass = group_mass + angle_mass
    
    return mass

def compute_block_attenuation(group, angle):
    '''
    Attenuation of a block increases with angle

    Attenuation group 1 - H > A > G > B
    Attenuation group 2 - F > C > E > D

    '''
    ATTENUATION_GROUP_1 = list('HAGB')
    ATTENUATION_GROUP_2 = list('FCED')

    ANGLE_ATTENUATION_STEP = 0.05
    AG_STEP = 0.125
    AG1_BASE = 0.0
    AG2_BASE = 0.5

    if group in ATTENUATION_GROUP_1:
        group_base_attenuation = AG1_BASE
        index = ATTENUATION_GROUP_1.index(group)

    else:
        group_base_attenuation = AG2_BASE
        index = ATTENUATION_GROUP_2.index(group)
        
    index = (len(GROUPS)/2 - 1) - index
    group_attenuation = group_base_attenuation + AG_STEP * index

    index = ANGLES.index(angle)
    angle_attenuation = index * ANGLE_ATTENUATION_STEP

    attenuation = group_attenuation + angle_attenuation
    attenuation = attenuation % 1.0
    
    return attenuation

def compute_block_max_energy(group, angle):
    '''
    Energy-max increases with angle and group
    '''
    group_energy = [i**3 * 100 for i in xrange(8)]
    angle_energy = [i**2 * 100 for i in xrange(8)]

    return group_energy[GROUPS.index(group)] + angle_energy[ANGLES.index(angle)]

def compute_block_friction(group, angle):
    '''
    Friction is between 0.0 and 1.0
    Increases along group A > B ... > H
    '''
    FRICTION_GROUP_1 = [2,5,30,60]
    FRICTION_GROUP_2 = [3,15,45,90]

    GROUP_STEP = 0.125
    ANGLE_STEP = 0.025
    FG1_BASE = 0.0
    FG2_BASE = 0.25

    if angle in FRICTION_GROUP_1:
        angle_base_friction = FG1_BASE
        index = FRICTION_GROUP_1.index(angle)

    else:
        angle_base_friction = FG2_BASE
        index = FRICTION_GROUP_2.index(angle)

    angle_friction = angle_base_friction + index * ANGLE_STEP
    group_friction = GROUPS.index(group) * GROUP_STEP

    friction = (angle_friction + group_friction) % 1.0
    return friction

def compute_block_absorption(group, angle):
    '''
    Absorption of a block increases with angle

    Absorption group 1 - H > A > G > B
    Absorption group 2 - F > C > E > D

    '''
    ATTENUATION_GROUP_1 = list('HAGB')
    ATTENUATION_GROUP_2 = list('FCED')

    ANGLE_ATTENUATION_STEP = 0.05
    AG_STEP = 0.125
    AG1_BASE = 0.0
    AG2_BASE = 0.5

    if group in ATTENUATION_GROUP_1:
        group_base_absorption = AG1_BASE
        index = ATTENUATION_GROUP_1.index(group)

    else:
        group_base_absorption = AG2_BASE
        index = ATTENUATION_GROUP_2.index(group)
        
    index = (len(GROUPS)/2 - 1) - index
    group_absorption = group_base_absorption + AG_STEP * index

    index = ANGLES.index(angle)
    angle_absorption = index * ANGLE_ATTENUATION_STEP

    absorption = group_absorption + angle_absorption
    absorption = absorption % 1.0
    absorption = 1.0 - absorption
    
    return absorption

class Block:
    def __init__(self, group, angle):
        assert(group in GROUPS)
        assert(angle in ANGLES)

        self.group = group
        self.angle = angle

    def get_mass(self):
        return compute_block_mass(self.group, self.angle)

    def get_color(self):
        pass

    def get_texture(self):
        pass

    def get_friction(self):
        return compute_block_friction(self.group, self.angle)

    def get_attenuation(self):
        return compute_block_attenuation(self.group, self.angle)

    def get_max_energy(self):
        return compute_block_max_energy(self.group, self.angle)

    def get_energy_absorption(self):
        return compute_block_absorption(self.group, self.angle)

    def __str__(self):
        return '#%s%d' % (self.group, self.angle)

    def __repr__(self):
        return str(self)

def test():
    doctest.testmod()

if __name__ == '__main__':
    test()
