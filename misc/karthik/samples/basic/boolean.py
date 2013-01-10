from procodile.procedural import BaseGenerator
import procodile.draw as draw

class BooleanGen(BaseGenerator):
    CONFIG = (
                'cut', [True, False],
                'common', [True, False],
                'fuse', [True, False],
             )

    def generate(self, config):
        C = config

        cylinder = draw.makeCylinder(3, 10, (0,0,0), (1,0,0))
        sphere = draw.makeSphere(5, (5,0,0))

        if C.cut:
            diff = cylinder.cut(sphere)
            self.add_geom(diff)

        if C.common:
            common = cylinder.common(sphere)
            self.add_geom(common)

        if C.fuse:
            fuse = cylinder.fuse(sphere)
            self.add_geom(fuse)

        
