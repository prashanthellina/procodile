import random

import networkx

import block
import compound

def main():
    d = int(raw_input())
    n = int(raw_input())
    g = networkx.random_regular_graph(d, n)

    node_properties = {}
    for _n in g:
        angle = random.choice(block.ANGLES)
        group = random.choice(block.GROUPS)
        node_properties[_n] = block.Block(group, angle)

    cm = compound.Compound()

    for a, b in g.edges_iter():
        bond = compound.Bond(node_properties[a], node_properties[b], 1, 1)
        cm.add_bond(bond)

    print cm.get_mass()
    print cm.get_max_energy()
    print cm.get_energy_absorption()
    print cm.get_friction()

if __name__ == '__main__':
    main()
