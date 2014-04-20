import numpy


data_types = {
    'int8': 'i1',
    'char': 'i1',
    'uint8': 'u1',
    'uchar': 'u1',
    'int16': 'i2',
    'short': 'i2',
    'uint16': 'u2',
    'ushort': 'u2',
    'int32': 'i4',
    'int': 'i4',
    'uint32': 'u4',
    'uint': 'u4',
    'float32': 'f4',
    'float': 'f4',
    'float64': 'f8',
    'double': 'f8'
}

data_type_reverse = {
    'i1': 'int8',
    'u1': 'uint8',
    'i2': 'int16',
    'u2': 'uint16',
    'i4': 'int32',
    'u4': 'uint32',
    'f4': 'float32',
    'f8': 'float64'
}

endianness_map = {
    'ascii': '=',
    'binary_little_endian': '<',
    'binary_big_endian': '>'
}

endianness_reverse = {
    '<': 'binary_little_endian',
    '>': 'binary_big_endian'
}


class PlyHeader(object):

    '''
    PLY file header.

    '''

    def __init__(self, stream):
        lines = []
        self.comments = []
        while True:
            line = stream.readline().strip()
            fields = line.split(None, 1)

            if fields[0] == 'end_header':
                break

            elif fields[0] == 'comment':
                if len(fields) > 1:
                    self.comments.append(fields[1])
                else:
                    self.comments.append('')
            else:
                lines.append(line.split())

        a = 0

        line = lines[a]
        a += 1

        assert line == ['ply']

        line = lines[a]
        a += 1

        assert line[0] == 'format'
        assert line[2] == '1.0'
        assert len(line) == 3
        fmt = line[1]
        assert fmt in endianness_map
        self.endianness = endianness_map[fmt]
        self.format = 't' if fmt == 'ascii' else 'b'

        self.elements = ply_elements(lines[a:], self.endianness)

    def __str__(self):
        lines = ['ply']

        # We didn't keep track of where in the header each comment came
        # from, so the best we can do is just put them all after the
        # initial 'ply'.  There are no current plans to remedy this.
        for c in self.comments:
            lines.append('comment ' + c)

        if self.format == 't':
            lines.append('format ascii')
        else:
            lines.append('format ' +
                         endianness_reverse[self.endianness])
        lines.extend(str(elt) for elt in self.elements)
        lines.append('end_header')
        return '\n'.join(lines)


class PlyData(PlyHeader):

    '''
    PLY file data.

    '''

    def __init__(self, stream):
        PlyHeader.__init__(self, stream)

        self.data = {}

        for elt in self.elements:
            if not elt.count:
                continue

            list_props = elt.list_properties
            if len(list_props):
                # There are list properties, so a simple load is
                # impossible. WARNING: this is going to be slow.

                if self.format == 't':
                    self.data[elt.name] = read_element_general_txt(
                            stream, elt)
                else:
                    self.data[elt.name] = read_element_general_bin(
                            stream, elt)
            else:
                # There are no list properties, so loading the data is
                # much more straightforward.
                if self.format == 't':
                    self.data[elt.name] = numpy.loadtxt(
                        limit_lines(stream, elt.count),
                        elt.dtype)
                else:
                    assert self.format == 'b'
                    self.data[elt.name] = numpy.fromfile(
                        stream, elt.dtype, elt.count)


def read_element_general_txt(stream, elt):
    '''
    Load a PLY element from an ASCII-format PLY file.  The element may
    contain list properties.

    '''
    list_props = elt.list_properties
    data = numpy.empty(elt.count, dtype=elt.dtype)

    for (k, line) in enumerate(limit_lines(stream, elt.count)):
        line = line.strip()
        for prop in elt.dtype:
            if prop[0] in list_props:
                (len_t, val_t) = list_props[prop[0]]
                (len_str, line) = line.split(None, 1)
                n = int(len_str)

                fields = line.split(None, n)
                if len(fields) == n:
                    fields.append('')

                assert len(fields) == n + 1

                data[prop[0]][k] = numpy.loadtxt(fields[:-1],
                                                 val_t, ndmin=1)

                line = fields[-1]
            else:
                (val_str, line) = line.split(None, 1)
                data[prop[0]][k] = numpy.fromstring(val_str,
                                                    prop[1], ' ')

    return data


def read_element_general_bin(stream, elt):
    '''
    Load a PLY element from an binary PLY file.  The element may
    contain list properties.

    '''
    list_props = elt.list_properties
    data = numpy.empty(elt.count, dtype=elt.dtype)

    for k in xrange(elt.count):
        for prop in elt.dtype:
            if prop[0] in list_props:
                (len_t, val_t) = list_props[prop[0]]
                n = numpy.fromfile(stream, len_t, 1)[0]

                data[prop[0]][k] = numpy.fromfile(stream, val_t, n)
            else:
                data[prop[0]][k] = numpy.fromfile(stream, prop[1], 1)[0]

    return data


class PlyElementSpec(object):

    '''
    PLY file element.

    '''

    def __init__(self, name, count, properties):
        self.name = name
        self.count = count

        # Mapping from list-property name to (count_type, value_type).
        self.list_properties = {}

        # Numpy dtype of in-memory representation.  (If there are no
        # list properties, and the PLY format is binary, then this
        # also accurately describes the on-disk representation of the
        # element.)
        self.dtype = []

        for prop in properties:
            if len(prop) == 3:
                assert prop[0] not in self.list_properties
                self.list_properties[prop[0]] = (prop[1], prop[2])
                self.dtype.append((prop[0], object))
            else:
                assert len(prop) == 2
                self.dtype.append(prop)

    def __str__(self):
        lines = ['element %s %d' % (self.name, self.count)]
        for prop in self.dtype:
            if prop[0] in self.list_properties:
                (len_t, val_t) = self.list_properties[prop[0]]
                lines.append('property list %s %s %s' %
                             (data_type_reverse[len_t[1:]],
                              data_type_reverse[val_t[1:]],
                              prop[0]))
            else:
                lines.append('property %s %s' %
                             (data_type_reverse[prop[1][1:]],
                              prop[0]))
        return '\n'.join(lines)

    def __repr__(self):
        return str(self)


def ply_elements(header_lines, endianness):
    '''
    Parse a list of PLY element specifications.

    '''
    elements = []
    while header_lines:
        (elt, header_lines) = one_ply_element(header_lines,
                                              endianness)
        elements.append(elt)

    return elements


def one_ply_element(lines, endianness):
    '''
    Consume one element specification.  The unconsumed input is returned
    along with a PlyElementSpec instance.

    '''
    a = 0
    line = lines[a]

    assert line[0] == 'element'
    assert len(line) == 3
    (name, count) = (line[1], int(line[2]))

    properties = []
    while True:
        a += 1
        if a >= len(lines):
            break

        line = lines[a]
        if lines[a][0] != 'property':
            break

        if line[1] == 'list':
            assert len(line) == 5
            properties.append((line[4],
                               endianness + data_types[line[2]],
                               endianness + data_types[line[3]]))
        else:
            assert len(line) == 3
            properties.append((line[2],
                               endianness + data_types[line[1]]))

    return (PlyElementSpec(name, count, properties), lines[a:])


def limit_lines(stream, n):
    '''
    Generator that generates n lines from the file handle fh.

    '''
    itr = iter(stream)
    for k in xrange(n):
        yield next(itr)
