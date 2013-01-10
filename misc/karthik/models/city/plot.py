#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 10, 2009 1:11:52 PM$"

from procodile.procedural import BaseGenerator
from builiding.building import Generator as building
from builiding.building import LBuildings
from tree.normal import Tree
import procodile.draw as draw
from procodile.procedural import BaseGenerator, Material as M

class RuralPlot(BaseGenerator):

    CONFIG = (
                 'length', (1000, 5000),
                 'width', (1000, 5000),
                 'build_height_range', None,
             )

    SUB_GENERATORS = {
                        'building': LBuildings,
                        'tree': Tree
                     }

    def generate(self, config):
        C = config
        plate = draw.makeBox(C.length, C.width, 0.2)
        sand_id = self.get_material('sand', M(texture='sand.jpg'))
        x = self.picker.pick((0.1, 1000.0))
        texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)]
        plate.set_material(sand_id, texture_coords=texture_coords)
        self.add_geom(plate)
        building_height = self.picker.pick(C.build_height_range)
        print 'calling building **'
        self.subgen('building', (0,0,0.2), C.length, C.width,
                    height=building_height)

class Plot(BaseGenerator):

    CONFIG = (
                 'length', (1000, 5000),
                 'width', (1000, 5000),                 
                 'plot_length_range', (25, 40),
                 'build_height_range', None,
                 'plot_gap', (2,4)
             )

    SUB_GENERATORS = {
                        'building': building,
                        'tree': Tree
                     }

    def generate(self, config):

        C = config
        plate = draw.makeBox(C.length, C.width, 0.2)
        sand_id = self.get_material('sand', M(texture='sand.jpg'))
        x = self.picker.pick((0.1, 1000.0))
        texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)]
        plate.set_material(sand_id, texture_coords=texture_coords)
        self.add_geom(plate)

        plots = make_plots(self.picker, C.length, C.plot_length_range, C.plot_gap)

        if not plots:
            return
        for origin, length in plots:
            if length <= 5 and C.width <= 5:
                print 'returning empty plot'
                return

            building_height = self.picker.pick(C.build_height_range)
            print 'plot got ', C.build_height_range, building_height
            width = C.width
            if length > 5:
                length = self.picker.pick((length/2, length))
            if C.width > 5:
                width = self.picker.pick((width/2, width))
            self.subgen('building', origin, length, width, height=building_height)
            gap = C.width - width
            if gap > 2:
                x,y,z = origin
                x= x+gap/2
                y = y+width+1
                self.subgen('tree', (x,y,z))

#def make_plots(picker, length, plot_length_range, plot_gap):
#    plots = []
#    consumed = 0
#    while 1:
#        build_len = picker.pick(plot_length_range)
#        if length < build_len:
#            print 'returning frm plot', length, build_len
#            return
#        pre_consumed = consumed
#        consumed = pre_consumed + build_len + plot_gap
#        if consumed > length:
#            plots.append(((pre_consumed+plot_gap,0,0),length-pre_consumed))
#            break
#        plots.append(((pre_consumed+plot_gap,0,0),build_len))
#    return plots

def make_plots(picker, length, plot_length_range, plot_gap):
    plots = []

    while length > 0:
        build_len = picker.pick(plot_length_range)
        l = build_len + plot_gap
        
        if l > length:
            length += plot_gap
            break

        plots.append(build_len)
        length -= l

    num_gaps = len(plots) - 1
    if length > 0 and num_gaps > 0:
        gap_increment = length / float(num_gaps)
        plot_gap += gap_increment

    offset = 0
    for index, plot in enumerate(plots):
        plots[index] = ((offset, 0, 0), plot)
        offset = offset + plot + plot_gap

    return plots