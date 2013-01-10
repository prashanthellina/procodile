#
# compound.py
#
#
import networkx

class Bond:
    def __init__(self, e1, e2, f1, f2):
        self.e1 = e1
        self.e2 = e2
        self.f1 = f1
        self.f2 = f2

class Compound:
    def __init__(self):
        self.structure = networkx.XGraph()
        
    def add_bond(self, b):
        self.structure.add_edge(b.e1, b.e2, b)

    def get_mass(self):
        tm = 0
        for _n in self.structure.nodes():
            tm += _n.get_mass()
        return tm

    def get_color(self):
        pass

    def get_texture(self):
        pass

    def get_attenuation(self):
        pass

    def get_ductility(self):
        pass

    def get_strength(self):
        pass

    def get_friction(self):
        tf = 0
        for e1, e2, b in self.structure.edges():
            tf += b.e1.get_friction() + b.e2.get_friction()

        return tf

    def get_max_energy(self):
        te = 0
        for n in self.structure.nodes():
            te += n.get_max_energy()

        # TODO code for cycles goes here
        return te

    def get_energy_absorption(self):
        tea = 0
        for e1, e2, b in self.structure.edges():
            tea += min(e1.get_energy_absorption(), e2.get_energy_absorption())
        return tea


