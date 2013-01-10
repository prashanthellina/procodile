
from procodile import BaseGenerator, Material
import procodile.draw as draw

class Test(BaseGenerator):

    CONFIG = (
                'density', (.1, 1.5),
             )

    SUB_GENERATORS = {
                     }

    def generate(self, config):

        m = Material(diffuse=(0.0, 0.2, 0.0, 0.0),
                     scale=(.5, .5),
                     scroll=(.4, .2),
                     texture='bark.jpg')

        angle = 0

        for i in range(int(6.28/config.density)):
            angle = config.density * i
            box = draw.Box(1, 1, 10)
            box.rotate(1, 0, 0, angle)
            box.material = m
            self.add_geoms(box)

        #c = draw.Cylinder(meridians=23)
        #c = draw.Cone()
        #c.material = m
        #self.add_geoms(c)
