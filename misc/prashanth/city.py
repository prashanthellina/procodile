import svgfig
import random
from geometry import *
from pprint import pprint
import time

class SectorConfig:
    min_roads = 1
    max_roads = 50
    road_gap = 5

class CityConfig:
    min_main_roads = 1
    max_main_roads = 20
    main_road_gap = 8

    area = AxisAligned2DRectangle((0, 0), (500, 500))

    sector_config = SectorConfig

class City:
    def __init__(self, area, sectors):
        self.area = area
        self.sectors = sectors

class Sector:
    def __init__(self, area, sub_sectors):
        self.area = area
        self.sub_sectors = sub_sectors

def break_rectangle(rect, num_cuts, min_gap, R):
    xvalues = [rect.min_x(), rect.max_x()]
    yvalues = [rect.min_y(), rect.max_y()]

    for i in xrange(num_cuts):
        
        values = xvalues if R.randint(0, 1) else yvalues

        location = R.randint(0, len(values) - 2)
        min_val = values[location] + min_gap
        max_val = values[location + 1] - min_gap
        if min_val >= max_val: continue
        values.append(R.randint(min_val, max_val))

        values.sort()

    xvalues = list(set(xvalues))
    xvalues.sort()
    yvalues = list(set(yvalues))
    yvalues.sort()

    splits = []
    for x in xrange(len(xvalues) - 1):
        for y in xrange(len(yvalues) - 1):
            x1, y1 = xvalues[x], yvalues[y]
            x2, y2 = xvalues[x + 1], yvalues[y + 1]
            r = AxisAligned2DRectangle((x1, y1), (x2, y2))
            splits.append(r)
  
    return splits

def sector_factory(seed, area, config):
    R = random.Random(seed)

    num_roads = R.randint(config.min_roads, config.max_roads)
    sub_sector_areas = break_rectangle(area, num_roads, config.road_gap, R)

    return Sector(area, sub_sector_areas)

def city_factory(seed, view_area, config):
    R = random.Random(seed)

    area = config.area
    num_roads = R.randint(config.min_main_roads, config.max_main_roads)

    sector_areas = break_rectangle(area, num_roads, config.main_road_gap, R)

    sectors = []
    for index, sector_area in enumerate(sector_areas):
        sector_seed = seed * index
        if sector_area.has_overlap(view_area):
            sector = sector_factory(sector_seed, sector_area, config.sector_config)
        else:
            sector = Sector(sector_area, [])
        sectors.append(sector)

    return City(area, sectors)

def main():
    dg = DiagramGenerator()

    view_area = AxisAligned2DRectangle((250, 250), (500, 500))
    #view_area = AxisAligned2DRectangle((400, 0), (500, 20))
    view_area = AxisAligned2DRectangle((0, 0), (500, 500))

#    for i in xrange(500):
    if 1:
        city = city_factory(15, view_area, CityConfig)

        renderables = []
        for sector in city.sectors:
            apply_attributes(sector.area, stroke='#555555', fill='', stroke_width=4)
            renderables.append(sector.area)
            for ssector in sector.sub_sectors:
                apply_attributes(ssector, stroke='#999999', fill='', stroke_width=2)
                renderables.append(ssector)

        dg.generate(renderables, width=800, height=800, viewbox='0 0 811 811')

        #print i
        #time.sleep(.01)


if __name__ == '__main__':
    main()
