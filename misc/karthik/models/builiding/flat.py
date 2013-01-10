'''
Building Flat model and generator.

G{importgraph}
'''

from procodile.procedural import BaseGenerator
import procodile.geometry as geometry
import procodile.draw as draw

class Generator(BaseGenerator):

    CONFIG = (
                    'length', (10, 100),
                    'width', (10, 100),
                    'height', (3, 5),
                    'inner_wall_thickness', (.1, .3),
                    'outer_wall_thickness', (.2, .4),
                    'corridor_length', (6, 8),
                    'corridor_width', (6, 8),
                    'door_width', 1,
                    'door_height', 2,
                    'main_door_width',(1,2),
                    'main_door_height', (2,3),
                    'main_door_wall', None,
                    'main_door_position', None
              )

    SUB_GENERATORS = {                        
                     }
    def generate(self, config):
        
        C = config
        flat_rect = ((0, 0), (C.length, C.width))
        flat_rect = geometry.AxisAligned2DRectangle(*flat_rect)
        center = C.length/2, C.width/2
        print flat_rect
        ps = self.get_surrounding((0,0,0,C.length,C.width,0))
        geoms = ps.get_geoms(tag='door')
        door = geoms[0]
        bb = door.BoundBox
        print bb
        (x1,y1,z1,x2,y2,z2) = (round(bb.XMin),round(bb.YMin),round(bb.ZMin),
                               round(bb.XMax),round(bb.YMax),round(bb.ZMax))

        door_width = x2 - x1
        door_center = x1 + door_width/2
        len_center = C.length/2
        wid_center = C.width/2
        door_gap = 2

#       main_door_wall is 'left'
        if x1 == 0 or x2 == 0:
            print 'left'
            if door_center > wid_center:
                hall_edge = (0,y1-door_gap)
                other_edge = (C.length/2, C.width)
            else :
                hall_edge = (0,y1+door_gap)
                other_edge = (C.length/2, 0)
            hall_edge = (0,y1-door_gap) if door_center > wid_center else (0,y1+door_gap)

#       main_door_wall is 'right'
        elif x1 == C.length or x2 == C.length:
            print 'right'
            if door_center > wid_center:
                hall_edge = (C.length,y1-door_gap)
                other_edge = (C.length/2, C.width)
            else :
                hall_edge = (C.length,y1+door_gap)
                other_edge = (C.length/2, 0)
#       main_door_wall is 'down'
        elif y1 == 0 or y2 == 0:
            print 'down'
            if door_center > len_center:
                hall_edge = (x1-door_gap,0)
                other_edge = (C.length, C.width/2)
            else :
                hall_edge = (x2+door_gap,0)
                other_edge = (0, C.width/2)
#       main_door_wall is 'up'
        elif y1 == C.width or y2 == C.width:
            print 'up'
            if door_center > len_center:
                hall_edge = (x1-door_gap,C.width)
                other_edge = (C.length, C.width/2)
            else :
                hall_edge = (x2+door_gap,C.width)
                other_edge = (0, C.width/2)
            
        hall_rect = geometry.AxisAligned2DRectangle(hall_edge, other_edge)
        common, rooms = geometry.split_overlapping_rectangles(flat_rect, hall_rect)
        
        fused = None
        
        for room in rooms:
            
            (x1, y1), (x2, y2) = room.point1, room.point2
            li = [(x1, y1), (x2, y2)]
            li.sort()
            (x1, y1), (x2, y2) = li[0], li[1]
            room_length = abs(x2 - x1)
            room_width = abs(y2 - y1)
           
            thickness = C.inner_wall_thickness
            p = draw.makePlane(room_length, room_width)
            p1 = draw.makePlane(room_length-thickness*2,
                                room_width-thickness*2,
                                (thickness,thickness,0))

            p = p.cut(p1)
            p = p.Faces[0]
            
            p = draw._wrap_value(p)
            p = p.extrude((0, 0, C.height))

            p.translate((x1, y2, 0))
            if fused:
                fused = fused.fuse(p)
            else:
                fused = p

        self.add_geom(fused)
