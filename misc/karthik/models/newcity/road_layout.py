#! /usr/bin/python
import math

def make_roads(length, height, road_width, num_roads, min_gap, picker):

    half_width = road_width / 2.

    hroads = [0, height]
    vroads = [0, length]

    num_roads_laid = 0
    num_chances = num_roads + 20

    while num_roads_laid < num_roads and num_chances > 0:
        num_chances -= 1

        roads = hroads if picker.pick() else vroads

        insert_at = picker.pick(0, len(roads) - 2)
        min_offset = roads[insert_at]
        max_offset = roads[insert_at + 1]

        min_offset = min_offset + min_gap
        max_offset = max_offset - min_gap

        if max_offset < min_offset:
            continue

        road_offset = picker.pick(min_offset, max_offset)
        roads.append(road_offset)
        num_roads_laid += 1

        roads.sort()

    if len(hroads) == 2 and len(vroads) == 2:
        return [], [], []

    for roads in (hroads, vroads):
        for index, value in enumerate(roads):
            if index in (0, len(roads)-1):
                value = [value]
            else:
                value = [value - half_width,
                         value + half_width]
            roads[index] = value

    #vroads = [[0], [49,51], [100]]
    #hroads = [[0], [99,101], [200]]
    
    #from pprint import pprint
#    print 'vroads'
#    print(vroads)
#    print 'hroads'
#    print(hroads)

    roads = []
    junctions = []
    spaces = []

    for v in xrange(1, len(vroads)):
        for h in xrange(1, len(hroads)):

            prev_hroad = max(hroads[h-1])
            vroad_length = min(hroads[h])- prev_hroad
            vroad_origin = min(vroads[v]), max(hroads[h-1])

            prev_vroad = max(vroads[v-1])
            hroad_length = min(vroads[v]) - prev_vroad
            hroad_origin = min(vroads[v]), min(hroads[h])

            junc_origin = hroad_origin

            space_origin = max(vroads[v-1]), max(hroads[h-1])
            space_length = hroad_length
            space_width = vroad_length

            spaces.append((space_origin, (space_length, space_width), 0))

            if v != len(vroads) - 1:
                roads.append((vroad_origin, (vroad_length, road_width), 0))
                
            if h != len(hroads) - 1:
                roads.append((hroad_origin, (hroad_length, road_width), math.pi/2))

            if v == len(vroads) - 1 or h == len(hroads) - 1:
                continue

            junctions.append((junc_origin, (road_width, road_width), 0))

    return roads, junctions, spaces

def test():
    from procodile.pick import Picker
    from pprint import pprint

    picker = Picker(0)
    roads, junctions, spaces = make_roads(100, 100, 2, 4, 10, picker)

    from pprint import pprint
    print 'roads'
    pprint(roads)

    print 'junctions'
    pprint(junctions)
    print 'spaces'
    pprint(spaces)

if __name__ == '__main__':
    test()
