from itertools import islice

import numpy
import sys


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
    'b1': 'uint8',
    'u1': 'uint8',
    'i2': 'int16',
    'u2': 'uint16',
    'i4': 'int32',
    'u4': 'uint32',
    'f4': 'float32',
    'f8': 'float64'
}

byte_order_map = {
    'ascii': '=',
    'binary_little_endian': '<',
    'binary_big_endian': '>'
}

byte_order_reverse = {
    '<': 'binary_little_endian',
    '>': 'binary_big_endian'
}


native_byte_order = '<' if sys.byteorder == 'little' else '>'


class PlyHeader(object):

    '''
    PLY file header.

    '''

    def __init__(self, text=False, byte_order='=', elements=[],
                 comments=[]):

        if byte_order == '=' and not text:
            byte_order = native_byte_order

        self.byte_order = byte_order
        self.text = text

        self.comments = comments
        self.elements = elements

    @staticmethod
    def read(stream):
        lines = []
        comments = []
        while True:
            line = stream.readline().strip()
            fields = line.split(None, 1)

            if fields[0] == 'end_header':
                break

            elif fields[0] == 'comment':
                if len(fields) > 1:
                    comments.append(fields[1])
                else:
                    comments.append('')
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

        assert fmt in byte_order_map
        byte_order = byte_order_map[fmt]
        text = fmt == 'ascii'

        return PlyHeader(text, byte_order,
                         ply_elements(lines[a:], byte_order),
                         comments)

    def __str__(self):
        lines = ['ply']

        # We didn't keep track of where in the header each comment came
        # from, so the best we can do is just put them all after the
        # initial 'ply'.  There are no current plans to remedy this.
        for c in self.comments:
            lines.append('comment ' + c)

        if self.text:
            lines.append('format ascii 1.0')
        else:
            lines.append('format ' +
                         byte_order_reverse[self.byte_order] +
                         ' 1.0')
        lines.extend(str(elt) for elt in self.elements)
        lines.append('end_header')
        return '\n'.join(lines)


class PlyElement(object):

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

    @staticmethod
    def describe(arr, name, byte_order='=', list_types={}):
        '''
        Construct a PlyElement from an array's metadata.

        A byte order other than native can be specified if desired.

        list_types can be given as a mapping from list property names to
        tuples (len_type, val_type), where each element of the tuple is
        a supported numpy typestring (like 'u1', 'f4', etc.).  For any
        list property not given as a key in list_types (or if list_types
        is omitted), the mapping value will be treated as ('u1', 'u4').
        The byte order should *not* be specified in the type string.

        '''
        if byte_order == '=':
            byte_order = native_byte_order

        if not isinstance(arr, numpy.ndarray):
            raise TypeError("only numpy arrays are supported")

        if len(arr.shape) != 1:
            raise ValueError("only one-dimensional arrays are "
                             "supported")

        count = len(arr)

        properties = []
        descr = arr.dtype.descr

        for t in descr:
            if len(t) != 2:
                raise ValueError("only scalar fields are supported")

            if not t[0]:
                raise ValueError("field with empty name")

            if t[1][1] == 'O':
                # object: this must be a list property.

                lt = tuple(byte_order + s
                           for s in list_types.get(t[0], ('u1', 'u4')))

                prop = (t[0],) + lt
            elif t[1][1:] in data_type_reverse:
                type_str = data_types[data_type_reverse[t[1][1:]]]
                prop = (t[0], byte_order + type_str)
            else:
                raise ValueError("unsupported field type: %s" % t[1])

            properties.append(prop)

        return PlyElement(name, count, properties)

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


def read_ply(stream):
    '''
    Read a PLY file.  The argument `stream' should be a file name or an
    open file object.  The return value is (header, data) where header
    is a PlyHeader instance and data is a dict mapping element names to
    numpy structured arrays.

    '''
    must_close = False
    try:
        if isinstance(stream, str):
            stream = open(stream, 'rb')
            must_close = True

        header = PlyHeader.read(stream)

        data = {}

        for elt in header.elements:
            if not elt.count:
                continue

            if len(elt.list_properties):
                # There are list properties, so a simple load is
                # impossible. WARNING: this is going to be slow.

                if header.text:
                    data[elt.name] = read_element_txt(stream, elt)
                else:
                    data[elt.name] = read_element_bin(stream, elt)
            else:
                # There are no list properties, so loading the data is
                # much more straightforward.
                if header.text:
                    data[elt.name] = numpy.loadtxt(
                        islice(iter(stream.readline, ''), elt.count),
                        elt.dtype)
                else:
                    data[elt.name] = numpy.fromfile(
                        stream, elt.dtype, elt.count)
    finally:
        if must_close:
            stream.close()

    return (header, data)


def write_ply(stream, data, text=False, byte_order='=', list_types={},
              comments=[]):
    '''
    Write a sequence of numpy arrays to file name or open file `stream'.

    `data' can be a list of form [(element_name, array)] or dict mapping
    the element_name to the array (in which case the order of the
    elements in the resulting file is unpredictable).

    if `list_types' is given, it must be a mapping from element names to
    mappings of list property names to tuples (len_type, val_type),
    which will default to ('u1', 'u4') if omitted.   Each type should be
    specified as a numpy type string (like 'u1', 'f4', etc.)  (Note:
    this is all irrelevant if the PLY format is text.)

    '''
    must_close = False
    try:
        if isinstance(stream, str):
            stream = open(stream, 'wb')
            must_close = True

        if isinstance(data, dict):
            data = data.items()

        elements = [PlyElement.describe(arr, name, byte_order,
                                        list_types.get(name, {}))
                    for (name, arr) in data]

        header = PlyHeader(text, byte_order, elements, comments)

        print >> stream, header

        for (elt, (_, arr)) in zip(elements, data):
            if len(elt.list_properties):
                # There are list properties, so serialization is
                # slightly complicated.
                if text:
                    write_element_txt(stream, elt, arr)
                else:
                    write_element_bin(stream, elt, arr)
            else:
                # no list properties, so serialization is
                # straightforward.
                if text:
                    numpy.savetxt(stream, arr, '%g')
                else:
                    arr = arr.astype(elt.dtype, copy=False)
                    arr.tofile(stream)

    finally:
        if must_close:
            stream.close()


def read_element_txt(stream, elt):
    '''
    Load a PLY element from an ASCII-format PLY file.  The element may
    contain list properties.

    '''
    list_props = elt.list_properties
    data = numpy.empty(elt.count, dtype=elt.dtype)

    for (k, line) in enumerate(islice(iter(stream.readline, ''),
                                      elt.count)):
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


def write_element_txt(stream, elt, data):
    '''
    Save a PLY element to an ASCII-format PLY file.  The element may
    contain list properties.

    '''
    list_props = elt.list_properties

    for rec in data:
        fields = []
        for t in elt.dtype:
            if t[0] in list_props:
                fields.append(len(rec[t[0]]))
                fields.extend(rec[t[0]])
            else:
                fields.append(rec[t[0]])

        numpy.savetxt(stream, [fields], '%g')


def read_element_bin(stream, elt):
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


def write_element_bin(stream, elt, data):
    '''
    Save a PLY element to a binary PLY file.  The element may contain
    list properties.

    '''
    list_props = elt.list_properties

    for rec in data:
        for t in elt.dtype:
            if t[0] in list_props:
                (len_type, val_type) = list_props[t[0]]
                list_len = numpy.array(len(rec[t[0]]), dtype=len_type)
                list_vals = rec[t[0]].astype(val_type, copy=False)

                list_len.tofile(stream)
                list_vals.tofile(stream)
            else:
                rec[t[0]].astype(t[1], copy=False).tofile(stream)


def ply_elements(header_lines, byte_order):
    '''
    Parse a list of PLY element specifications.

    '''
    elements = []
    while header_lines:
        (elt, header_lines) = one_ply_element(header_lines,
                                              byte_order)
        elements.append(elt)

    return elements


def one_ply_element(lines, byte_order):
    '''
    Consume one element specification.  The unconsumed input is returned
    along with a PlyElement instance.

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
                               byte_order + data_types[line[2]],
                               byte_order + data_types[line[3]]))
        else:
            assert len(line) == 3
            properties.append((line[2],
                               byte_order + data_types[line[1]]))

    return (PlyElement(name, count, properties), lines[a:])
