#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 10, 2009 9:56:26 AM$"

from procodile.procedural import BaseGenerator
import procodile.draw as draw
from plot import Plot
import math

class Layout(BaseGenerator):

    CONFIG = (
                 'length', (1000, 5000),
                 'width', (1000, 5000),
                 'road_width', (5, 10),
                 'building_height', None,
                 'plot_width', (20, 40),
                 'height_width_ratio',(6,10),
                 'level',[1,2,3,4]
             )

    SUB_GENERATORS = {
                        'plot': Plot,
                        'layout':None
                     }

    def generate(self, config):
        C = config

        if C.length < 1 or C.width < 1:
            print 'returning empty layout'
            return

#        height_width_ratio = self.picker.pick((6,10))
#        building_height = self.picker.pick((10,250))
#        plot_min_width = building_height/height_width_ratio
#        if C.plot_width > plot_min_width:
#            plot_width = self.picker.pick((plot_min_width, C.plot_width))
#        else:
#            plot_width = plot_min_width

        print 'level is ', C.level
        if C.level == 1:
            height_width_ratio = 8.
            if not C.building_height:
                building_range = self.picker.random()
                if building_range <= 0.2:
                    building_height = self.picker.pick((100,300))
                elif building_range <= 0.4:
                    building_height = self.picker.pick((15,75))
                else:
                    building_height = self.picker.pick((3,15))

            else:
                building_height = C.building_height
               
            plot_width = building_height/height_width_ratio
            road_width = 6
            print 'heit, width ', building_height, plot_width

        if C.level == 2:
            height_width_ratio = 6.
            building_height = self.picker.pick((3, 50))
            plot_width = building_height/height_width_ratio
            road_width = 8

        if C.level == 3:
            height_width_ratio = 4.
            building_height = self.picker.pick((3,15))
            plot_width = building_height/height_width_ratio
            road_width = 10

        if C.level == 4:
            height_width_ratio = 2.
            building_height = self.picker.pick((3,15))
            plot_width = building_height/height_width_ratio
            road_width = 12


        layouts = self.make_layouts(C.length, C.width, plot_width, road_width)

        for (origin, (llength, lwidth)) in layouts:
            self.subgen('layout', origin, llength, lwidth, road_width, building_height, level = C.level)

        if not layouts:
            location = ((C.length,0,0), (math.pi / 2, (0, 0, 1))) if C.length < C.width else (0,0,0)
            l,w = (C.width, C.length) if C.length < C.width else (C.length, C.width)
            self.subgen('plot', location, l,w, building_height, level = C.level)


    def make_layouts(self, length, width, plot_width, road_width):
        if self.id == 1304:
            print 'layout len, wid and min plot wid ', length, width, plot_width
        if length < width:
            if length > plot_width  and length/2 > plot_width+road_width:
                l,w = [length/2-road_width/2,width]
                space1 = ((0,0,0), (l,w))
                space2 = ((l+road_width, 0,0), (l,w))

                if self.id == 1304:
                    print space1, space2
                return [space1, space2]
        else:
            if width > plot_width and width/2 > plot_width+road_width:
                l,w = [length, width/2-road_width/2]
                space1 = ((0,0,0), (l,w))
                space2 = ((0,w+road_width, 0), (l,w))

                if self.id == 1304:
                    print space1, space2
                return [space1, space2]
        return []

Layout.SUB_GENERATORS['layout']=Layout
