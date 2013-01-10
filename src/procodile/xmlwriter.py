'''
A simple abstraction to help produce XML data.
'''

import sys
import cStringIO as StringIO

class XMLNode(object):
    '''
    >>> rootnode = XMLNode('toplevel')
    >>> books = rootnode.books
    >>> books.book.attrs = {'name': 'Prashanth', 'id': 2323232}
    >>> books.book.name = 'Karthik'
    >>> books.book.mook.dook = 10
    >>> b = XMLNode('book')
    >>> b.isbn = '878JHKJ45GDS'
    >>> books.book = b
    >>> b = books.book
    >>> b.text = 'bingo'
    >>> b.attrs = (('x', 10),)

    >>> rootnode.serialize(sys.stdout)
    <toplevel>
        <books>
            <book id="2323232" name="Prashanth"/>
            <book>
                <name>Karthik</name>
            </book>
            <book>
                <mook>
                    <dook>10</dook>
                </mook>
            </book>
            <book>
                <isbn>878JHKJ45GDS</isbn>
            </book>
            <book x="10">bingo</book>
        </books>
    </toplevel>
    '''

    def __init__(self, tag):
        self._tag = tag
        self._sub_nodes = []
        self._attrs = ()
        self._text = ''

    def __getattr__(self, name):
        new_node = XMLNode(name)
        self._sub_nodes.append((name, new_node))
        return new_node

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        
        else:
            if name == 'attrs':
                if isinstance(value, dict):
                    value = value.items()
                    value.sort()

                self._attrs = value

            else:
                if isinstance(value, XMLNode):
                    self._sub_nodes.append((name, value))

                elif name == 'text':
                    self._text = value

                else:
                    getattr(self, name)._text = value

    def serialize(self, stream, indent=0):
        '''
        @type stream: file like object
        @param stream: stream to which xml
            should be serialized

        @type indent: int
        @param indent: indentation level
        '''

        o = stream

        attributes = ''
        if self._attrs:
            a = []
            for k, v in self._attrs:
                a.append('%s="%s"' % (k, v))
            attributes = ' %s' % (' '.join(a))
        
        whitespace = ' ' * indent

        close = '/'
        if self._sub_nodes or self._text:
            close = ''

        newline = '\n'
        if self._text and not self._sub_nodes:
            newline = ''

        o.write('%s<%s%s%s>%s' % (whitespace, self._tag, \
                attributes, close, newline))

        if self._sub_nodes or self._text:

            if self._text:
                o.write('%s' % (self._text))
                whitespace = ''

            for tag, node in self._sub_nodes:
                node.serialize(o, indent+4)

            o.write('%s</%s>\n' % (whitespace, self._tag))
