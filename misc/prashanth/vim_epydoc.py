'''
Vim python module for modifying old style argument documentation
into epydoc style
'''
import vim
import re

PATTERNS = (
           ('all', '( +)@([^ ]+) *\(([^\)]*)\) *-{0,2} *(.*)'),
           ('no desc', '( +)@([^ ]+) *\(([^\)]*)\) *'),
           ('no type', '( +)@([^ ]+) *-{1,2} *(.*)'),
           ('no desc-type', '( +)@([^ ]+) *'),
           ('', '.*')
            )

SEP = ':_._._._:'

def parse(data):
    for name, pattern in PATTERNS:
        m = re.findall(pattern, data)
        if m: return name, m

def adjust():
    line_no, col = vim.current.window.cursor
    line_no -= 1
    data = vim.current.buffer[line_no]
    print data

    name, m = parse(data)
    if not name: return
    m = m[0]

    if name == 'all':
        spaces, var, _type, desc = m
        type_line = '%(spaces)s@type %(var)s: %(_type)s' % locals()
        var_line = '%(spaces)s@param %(var)s: %(desc)s' % locals()
        line = '%s%s%s' % (type_line, SEP, var_line)

    elif name == 'no desc':
        spaces, var, _type = m
        type_line = '%(spaces)s@type %(var)s: %(_type)s' % locals()
        line = type_line

    elif name == 'no type':
        spaces, var, desc = m
        line = '%(spaces)s@param %(var)s: %(desc)s' % locals()

    elif name == 'no desc-type':
        spaces, var = m
        desc = ''
        line = '%(spaces)s@param %(var)s: %(desc)s' % locals()

    vim.current.buffer[line_no] = line
