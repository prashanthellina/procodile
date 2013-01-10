#! /usr/bin/python

__author__="karthik"
__date__ ="$Sep 14, 2009 1:14:01 PM$"

import math

from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw
import procodile.geometry as geometry
from celllayout import Layout
from road_layout import make_roads
from road import SimpleRoad as road
from builiding.building import Generator as building

class Sector(BaseGenerator):

    CONFIG = (
                 'length', (1000, 5000),
                 'width', (1000, 5000),
                 'num_roads', (2, 4),
                 'road_width', (5, 20),
                 'min_gap_btw_roads', (50, 100),
                 'level',[1,2,3,4]
             )

    SUB_GENERATORS = {
                        'cellayout': Layout,
                        'building': building,
                        'road': road
                     }

    def generate(self, config):
        C = config
        if C.level == 7:
            road_width = 6
            sky_origin, layouts = self.skyapt_plan(C.length, C.width,
                                                   road_width, 'sky')
            
        elif C.level == 7:
            road_width = 8          
            apt, layouts = self.skyapt_plan(C.length, C.width,
                                            road_width, 'apt')
                
        else:
            road_width = 10
            

            if C.level == 1:
                plot_gap = 4
                height_width_ratio = 8.
                road_width = 5
                build_height = self.picker.pick((100,300))
                plot_width = build_height/height_width_ratio
                if plot_width < 10:
                    plot_width = 10
                plot_length = (plot_width,plot_width*3)
                height_range = (100,300)

            elif C.level == 2:
                plot_gap = 10
                height_width_ratio = 8.
                road_width = 8
                build_height = self.picker.pick((50,70))
                plot_width = build_height/height_width_ratio
                if plot_width < 10:
                    plot_width = 10
                plot_length = (plot_width,plot_width*3)
                height_range = (40, 100)

            elif C.level == 3:
                plot_gap = 10
                height_width_ratio = 4.
                road_width = 8
                build_height = self.picker.pick((3,15))
                plot_width = build_height/height_width_ratio
                if plot_width < 10:
                    plot_width = 10
                plot_length = (plot_width,plot_width*3)
                height_range = (3,15)

            else:
                plot_gap = 12
                height_width_ratio = 2.
                road_width = 8
                build_height = self.picker.pick((3,15))
                plot_width = build_height/height_width_ratio
                if plot_width < 15:
                    plot_width = 15
                plot_length = (plot_width,plot_width*4)
                height_range = (3,15)

            roads, junctions, spaces = make_roads(C.length, C.width,
                                            road_width, self.picker.pick((3,5)),
                                            C.min_gap_btw_roads, self.picker)

            for origin, (slength, swidth), rotation in spaces:
                x,y = origin
                origin = ((x, y, 0), (rotation, (0, 0, 1)))

                self.subgen('cellayout', origin, C.level, slength,
                            swidth, [plot_length], plot_width, road_width,
                            [height_range], plot_gap)

            for road in roads:
                origin, (road_length, road_width), rotation = road
                x,y = origin
                origin = ((x, y, 0), (rotation, (0, 0, 1)))

                self.subgen('road', origin,
                        road_length, road_width)

    def skyapt_plan(self, sector_length, sector_width, road_gap, plan):

        chooser = lambda min, max: self.picker.pick((min,max))

        if plan == 'sky':
            height_width_ratio = 8.
            build_height = self.picker.pick((100,300))
            build_width = build_height/height_width_ratio
            build_length = self.picker.pick((build_width, build_width*2))
        else:
            build_length = self.picker.pick((50,70))
            build_width = self.picker.pick((50,70))
            build_height = chooser(1,2)

        build_length = int(round(build_length))
        build_width = int(round(build_width))
        x = sector_length - build_length
        y = sector_width - build_width
        x = int(round(x))
        y = int(round(y))

        if x <= 5 or y <= 5:
            return None, None
        
        x = chooser(5, x)
        y = chooser(5, y)

        build_origin = (x, y, 0)
        sky_apt = None
        if plan == 'sky':
            self.subgen('building', build_origin, build_length, build_width, height=build_height)
            sky_apt = build_origin
        else:

            a,b,c = build_origin
            base = draw.makePolygon([build_origin,(a+build_length,b,0),
                                    (a+build_length,b+build_width,0),
                                    (a,b+build_width,0),build_origin])
            sky_apt = base.extrude((0,0,3))
            self.add_geom(sky_apt)

        build_start = (x, y)
        build_end = (x+build_length, y+build_width)
        build_rect = geometry.AxisAligned2DRectangle(build_start, build_end)
        sector_rect = geometry.AxisAligned2DRectangle((0,0), (sector_length, sector_width))
        common, layouts = geometry.split_overlapping_rectangles(sector_rect, build_rect)
        for layout in layouts:
            (x1, y1), (x2, y2) = layout.point1, layout.point2
            layout_length = abs(x2 - x1) - road_gap
            layout_width = abs(y2 - y1) - road_gap
            dummy, sub_layouts = self.skyapt_plan(layout_length,
                                                  layout_width, road_gap, plan)
            if not sub_layouts:
                origin = (layout.min_x(), layout.min_y(), 0)
                if plan == 'sky':
                    plot_gap = 5
                    height_width_ratio = 8.
                    building_range = self.picker.random()
                    if building_range <= 0.4:
                        building_height = self.picker.pick((15,75))
                        height_range = (15,75)
                    else:
                        building_height = self.picker.pick((3,15))
                        height_range = (3,15)
                    plot_width = building_height/height_width_ratio
                    if plot_width < 5:
                        plot_width = 5
                    plot_length = (plot_width,plot_width*2)
                else:
                    plot_gap = 8
                    height_width_ratio = 6.
                    building_height = self.picker.pick((3,50))
                    height_range = (3,50)
                    plot_width = building_height/height_width_ratio
                    if plot_width < 5:
                        plot_width = 5
                    plot_length = (plot_width,plot_width*3)
                self.subgen('celllayout', origin, layout_length,
                            layout_width, [plot_length], plot_width, road_gap,
                            [height_range], plot_gap)

        return sky_apt, layouts