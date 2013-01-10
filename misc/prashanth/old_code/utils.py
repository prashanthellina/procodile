
import cStringIO
import block

def generate_block_properties(group, angle):
    element = block.Block(group, angle)
    
    o = cStringIO.StringIO()
    print >> o, '<table border="0">'
    
    print >> o, '<tr>'
    print >> o, '<td>%dg</td>' % element.get_mass()
    print >> o, '</tr>'
    
    print >> o, '<tr>'
    print >> o, '<td>%.2ff</td>' % element.get_friction()
    print >> o, '</tr>'
    
    print >> o, '<tr>'
    print >> o, '<td>%.2fat</td>' % element.get_attenuation()
    print >> o, '</tr>'
    
    print >> o, '<tr>'
    print >> o, '<td>%.2fab</td>' % element.get_energy_absorption()
    print >> o, '</tr>'

    print >> o, '<tr>'
    print >> o, '<td>%dj</td>' % element.get_max_energy()
    print >> o, '</tr>'
    
    print >> o, '</table>'

    return o.getvalue()

def generate_block_table(ostream, block_fn, block_bg_fn):
    o = ostream

    if not block_bg_fn: block_bg_fn = lambda g,a: ''

    print >> o, '<table border="1" width="100%">'
    print >> o, '<tr>'
    print >> o, '<td></td>'
    for g in block.GROUPS:
        print >> o, '<td><b>%s</b></td>' % g
    print >> o, '</tr>'

    for angle in block.ANGLES:
        print >> o, '<tr>'
        print >> o, '<td><b>%s</b></td>' % (angle)
        for group in block.GROUPS:
            print >> o, '<td bgcolor="%s">%s</td>' % (
                    block_bg_fn(group, angle),
                    block_fn(group, angle)
                    )
        print >> o, '</tr>'

    print >> o, '</table>'

def create_bg_fn(property):
    p = property

    def bg_fn(group, angle):
        elements = [block.Block(g,a) for g,a in block.get_block_iterator()]
        elements.sort(cmp=lambda x,y: int(getattr(x,p)()*10000) - int(getattr(y,p)()*10000))
        max = getattr(elements[-1], p)()
        min = getattr(elements[0], p)()

        element = block.Block(group, angle)
        color = float(getattr(element,p)()) / (max - min)
        color = int(color * 128)
        color = 255 - color

        color = '%02x%02x%02x' % (color, color, color)
        return color

    return bg_fn

def create_prop_fn(property):
    p = property

    def prop_fn(group, angle):
        b = block.Block(group, angle)
        return getattr(b, p)()

    return prop_fn

def generate_block_page(ostream):
    o = ostream

    print >> o, '<h2>Periodic Table</h2>'
    generate_block_table(o, generate_block_properties, None)

    props = [
                ('Mass', 'get_mass'),
                ('Friction', 'get_friction'),
                ('Max Energy', 'get_max_energy'),
                ('Attenuation', 'get_attenuation'),
                ('Energy Absorption', 'get_energy_absorption'),
            ]

    for title, property in props:
        print >> o, '<h2>%s</h2>' % title
        p_fn = create_prop_fn(property)
        p_bg_fn = create_bg_fn(property)
        generate_block_table(o, p_fn, p_bg_fn)
    

o = cStringIO.StringIO()
generate_block_page(o)
print o.getvalue()
