from procodile.procedural import BaseGenerator
import procodile.draw as draw

class MyGenerator(BaseGenerator):
    CONFIG = ('length', (1, 100),
              'width', (0.5, 50.0),
              'height', [10, 20, 30, 40])

    def generate(self, config):
        box = draw.makeBox(config.length, config.width, config.height)
        self.add_geom(box)