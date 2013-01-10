from procodile.procedural import BaseGenerator
import procodile.draw as draw

class PrimitiveGen(BaseGenerator):
    '''
    Demonstrates the creation of base shapes
    '''

    CONFIG = (
                'box', [True, False],
                'sphere', [True, False],
                'cylinder', [True, False],
                'plane', [True, False],
                'polygon', [True, False],
             )

    def generate(self, config):
        # x is on horizontal,  y is on depthwards, z is on upwards
        '''
        z    y
        |   *
        |  *
        | *
        - - - x

        all units are in metres
        '''

        # in short
        '''
        pnt is where the object has to be created
        dir is in which directiong it has to be created

        draw.makeBox(length, width, height, pnt=(0,0,0), dir=(0,0,1))
        draw.makeSphere(radius, pnt=(0,0,0), dir=(0,0,1), angle1=0.5*PI, angle2=0.5*PI, angle3=2*PI)
        draw.makeCylinder(radius, height, pnt=(0,0,0), dir=(0,0,1), angle=2*PI)
        draw.makePlane(length,width, pnt=(0,0,0), dir=(0,0,1))
        draw.makePolygon([]) -- Make a polygon of a list of points
        '''

        C = config

        if C.box:
            box = draw.makeBox(1, 1, 1)
            self.add_geom(box) # adding box to the scene

            pnt = (2, 2, 2)
            o_box = draw.makeBox(1, 1, 1, pnt)
            self.add_geom(o_box) # adding another box at different point in scene

        if C.sphere:
            sphere = draw.makeSphere(2)
            self.add_geom(sphere)

            pnt = (2, 2, 2)
            o_sphere = draw.makeSphere(2, pnt)
            self.add_geom(o_sphere)

        if C.cylinder:
            cylinder = draw.makeCylinder(1, 1)
            self.add_geom(cylinder)

            pnt = (2, 2, 2)
            o_cylinder = draw.makeCylinder(1, 1, pnt)
            self.add_geom(o_cylinder)

        if C.plane:
            plane = draw.makePlane(1, 1)
            self.add_geom(plane)

            pnt = (2, 2, 2)
            o_plane = draw.makePlane(1, 1, pnt)
            self.add_geom(o_plane)

        if C.polygon:
            polygon = draw.makePolygon([(0, 0, 0),
                                        (1, 0, 0),
                                        (1, 0, 1),
                                        (0, 0, 1),
                                        (0, 0, 0)]) # this returns a wire connecting points

            face = draw.Face(polygon) # filling up the wire with mass, u can also do other things with the wire

            self.add_geom(face)




        

        











