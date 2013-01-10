from procodile.procedural import BaseGenerator, Material as M
import procodile.draw as draw

class Tree(BaseGenerator):

    CONFIG = (
                'diameter', (0.05, 0.5),
                'height', (0.5, 5),
             )
   
    def generate(self, config):

        C = config
        grass_id = self.get_material('grass', M(texture='textures\\grass.jpg'))
        bark_id = self.get_material('bark', M(texture='textures\\bark.jpg'))

        trunk = draw.makeBox(C.diameter,C.diameter,C.height)
        trunk.set_material(bark_id)
        self.add_geom(trunk)

        length = C.diameter * 10
        pnt = (-length/2, -length/2, C.height)
        top = draw.makeBox(length, length, length, pnt)
        x = self.picker.pick((1.0))
        top.set_material(grass_id, texture_coords=[(0.0, 0.0), (x, 0.0), (x, x), (0.0, x)])
        self.add_geom(top)