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


def normalize_type(type_str):
    if type_str not in data_type_reverse:
        raise ValueError("unsupported field type: %s" % type_str)

    return data_types[data_type_reverse[type_str]]


def split_line(line, n):
    fields = line.split(None, n)
    if len(fields) == n:
        fields.append('')

    assert len(fields) == n + 1

    return fields


class PlyData(object):

    '''
    PLY file header and data.

    A PlyData instance is created in one of two ways: by the static
    method PlyData.read (to read a PLY file), or directly from __init__
    given a sequence of elements (which can then be written to a PLY
    file).

    '''

    def __init__(self, elements=[], text=False, byte_order='=',
                 comments=[]):
        '''
        elements: sequence of PlyElement instances.

        text: whether the resulting PLY file will be text (True) or
            binary (False).

        byte_order: '<' for little-endian or '>' for big-endian.  This
            is only relevant if text is False.

        comments: sequence of strings that will be placed in the header
            between the 'ply' and 'format ...' lines.

        '''
        if byte_order == '=' and not text:
            byte_order = native_byte_order

        self.byte_order = byte_order
        self.text = text

        self.comments = comments
        self._elements = list(elements)
        self._element_lookup = dict((elt.name, elt) for elt in
                                    elements)

    @staticmethod
    def _parse_header(stream):
        '''
        Parse a PLY header from a readable file-like stream.

        '''
        lines = []
        comments = []
        while True:
            line = stream.readline().strip()
            fields = split_line(line, 1)

            if fields[0] == 'end_header':
                break

            elif fields[0] == 'comment':
                comments.append('')
            else:
                lines.append(line.split())

        a = 0

        line = lines[a]
        a += 1

        if line != ['ply']:
            raise RuntimeError("expected 'ply'")

        line = lines[a]
        a += 1

        if line[0] != 'format':
            raise RuntimeError("expected 'format'")

        if line[2] != '1.0':
            raise RuntimeError("expected version '1.0'")

        if len(line) != 3:
            raise RuntimeError("too many fields after 'format'")

        fmt = line[1]

        if fmt not in byte_order_map:
            raise RuntimeError("don't understand format %r" % fmt)

        byte_order = byte_order_map[fmt]
        text = fmt == 'ascii'

        return PlyData(PlyElement._parse_multi(lines[a:],
                                               byte_order),
                       text, byte_order, comments)

    @staticmethod
    def read(stream):
        '''
        Read PLY data from a readable file-like object or filename.

        '''
        must_close = False
        try:
            if isinstance(stream, str):
                stream = open(stream, 'rb')
                must_close = True

            data = PlyData._parse_header(stream)

            for elt in data:
                elt._read(stream, data.text)

        finally:
            if must_close:
                stream.close()

        return data

    def write(self, stream):
        '''
        Write PLY data to a writeable file-like object or filename.

        '''
        must_close = False
        try:
            if isinstance(stream, str):
                stream = open(stream, 'wb')
                must_close = True

            print >> stream, self.header

            for elt in self:
                elt._write(stream, self.text)

        finally:
            if must_close:
                stream.close()

    @property
    def header(self):
        '''
        Provide PLY-formatted metadata for the instance.

        '''
        lines = ['ply']

        if self.text:
            lines.append('format ascii 1.0')
        else:
            lines.append('format ' +
                         byte_order_reverse[self.byte_order] +
                         ' 1.0')

        # We didn't keep track of where in the header each comment came
        # from, so the best we can do is just put them all after the
        # 'format' line.  There are no current plans to remedy this.
        for c in self.comments:
            lines.append('comment ' + c)

        lines.extend(elt.header for elt in self.elements)
        lines.append('end_header')
        return '\n'.join(lines)

    @property
    def elements(self):
        return self._elements

    def __str__(self):
        return self.header

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    def __contains__(self, name):
        return name in self._element_lookup

    def __getitem__(self, name):
        return self._element_lookup[name]


class PlyElement(object):

    '''
    PLY file element.

    A client of this library doesn't normally need to instantiate this
    directly, so the following is only for the sake of documenting the
    internals.

    Creating a PlyElement instance is generally done in one of two ways:
    as a byproduct of PlyData.read (when reading a PLY file) and by
    PlyElement.describe (before writing a PLY file).

    '''

    def __init__(self, name, properties, count):
        '''
        This is not part of the public interface.  The preferred methods
        of obtaining PlyElement instances are PlyData.read (to read from
        a file) and PlyElement.describe (to construct from a numpy
        array).

        '''
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
                self.list_properties[prop[0]] = (prop[1], prop[2])
                self.dtype.append((prop[0], object))
            else:
                assert len(prop) == 2
                self.dtype.append(prop)

    @staticmethod
    def _parse_multi(header_lines, byte_order):
        '''
        Parse a list of PLY element definitions.

        '''
        elements = []
        while header_lines:
            (elt, header_lines) = PlyElement._parse_one(header_lines,
                                                        byte_order)
            elements.append(elt)

        return elements

    @staticmethod
    def _parse_one(lines, byte_order):
        '''
        Consume one element definition.  The unconsumed input is
        returned along with a PlyElement instance.

        '''
        a = 0
        line = lines[a]

        if line[0] != 'element':
            raise RuntimeError("expected 'element'")
        if len(line) > 3:
            raise RuntimeError("too many fields after 'element'")
        if len(line) < 3:
            raise RuntimeError("too few fields after 'element'")

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
                if len(line) > 5:
                    raise RuntimeError("too many fields after "
                                       "'property list'")
                if len(line) < 5:
                    raise RuntimeError("too few fields after "
                                       "'property list'")

                properties.append((line[4],
                                   byte_order + data_types[line[2]],
                                   byte_order + data_types[line[3]]))
            else:
                if len(line) > 3:
                    raise RuntimeError("too many fields after "
                                       "'property'")
                if len(line) < 3:
                    raise RuntimeError("too few fields after "
                                       "'property'")

                properties.append((line[2],
                                   byte_order + data_types[line[1]]))

        return (PlyElement(name, properties, count), lines[a:])

    @staticmethod
    def describe(arr, name, byte_order='=', len_types={}, val_types={}):
        '''
        Construct a PlyElement from an array's metadata.

        A byte order other than native can be specified if desired.

        len_types and val_types can be given as a mapping from list
        property names to type strings (like 'u1', 'f4', etc.). These
        can be used to define the length and value types of list
        properties.  List property lengths always default to type 'u1'
        (8-bit unsigned integer), and value types are obtained from the
        array if possible and default to 'u4' (32-bit unsigned integer)
        if the array is empty.

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
            if not isinstance(t[1], str):
                raise ValueError("nested records not supported")

            if not t[0]:
                raise ValueError("field with empty name")

            if len(t) != 2 or t[1][1] == 'O':
                # non-scalar field, which corresponds to a list
                # property in PLY.

                if t[1][1] == 'O':
                    if len(t) != 2:
                        raise ValueError("non-scalar object fields not "
                                         "supported")

                len_type = byte_order + len_types.get(t[0], 'u1')
                if t[1][1] == 'O':
                    if count > 0 and t[0] not in val_types:
                        field_descr = arr[t[0]][0].dtype.descr
                        if len(field_descr) > 1:
                            raise ValueError("object fields must be "
                                             "flat")
                        val_str = normalize_type(field_descr[0][1][1:])
                    else:
                        val_str = val_types.get(t[0], 'u4')
                else:
                    val_str = normalize_type(t[1][1:])

                prop = (t[0], len_type, byte_order + val_str)
            else:
                type_str = normalize_type(t[1][1:])
                prop = (t[0], byte_order + type_str)

            properties.append(prop)

        elt = PlyElement(name, properties, count)
        elt.data = arr

        return elt

    def _read(self, stream, text=False):
        '''
        Read the actual data from a PLY file.

        '''
        if len(self.list_properties):
            # There are list properties, so a simple load is
            # impossible.
            if text:
                self._read_txt(stream)
            else:
                self._read_bin(stream)
        else:
            # There are no list properties, so loading the data is
            # much more straightforward.
            if text:
                self.data = numpy.loadtxt(
                    islice(iter(stream.readline, ''), self.count),
                    self.dtype)
            else:
                self.data = numpy.fromfile(
                    stream, self.dtype, self.count)

    def _write(self, stream, text=False):
        '''
        Write the data to a PLY file.

        '''
        if len(self.list_properties):
            # There are list properties, so serialization is
            # slightly complicated.
            if text:
                self._write_txt(stream)
            else:
                self._write_bin(stream)
        else:
            # no list properties, so serialization is
            # straightforward.
            if text:
                numpy.savetxt(stream, self.data, '%.18g')
            else:
                self.data.astype(self.dtype, copy=False).tofile(stream)

    def _read_txt(self, stream):
        '''
        Load a PLY element from an ASCII-format PLY file.  The element may
        contain list properties.

        '''
        list_props = self.list_properties
        self.data = numpy.empty(self.count, dtype=self.dtype)

        for (k, line) in enumerate(islice(iter(stream.readline, ''),
                                          self.count)):
            line = line.strip()
            for prop in self.dtype:
                if prop[0] in list_props:
                    (len_t, val_t) = list_props[prop[0]]
                    (len_str, line) = split_line(line, 1)
                    n = int(len_str)

                    fields = split_line(line, n)
                    if len(fields) == n:
                        fields.append('')

                    assert len(fields) == n + 1

                    self.data[prop[0]][k] = numpy.loadtxt(
                            fields[:-1], val_t, ndmin=1)

                    line = fields[-1]
                else:
                    (val_str, line) = split_line(line, 1)
                    self.data[prop[0]][k] = numpy.fromstring(
                            val_str, prop[1], sep=' ')

    def _write_txt(self, stream):
        '''
        Save a PLY element to an ASCII-format PLY file.  The element may
        contain list properties.

        '''
        list_props = self.list_properties

        for rec in self.data:
            fields = []
            for t in self.dtype:
                if t[0] in list_props:
                    fields.append(rec[t[0]].size)
                    fields.extend(rec[t[0]].ravel())
                else:
                    fields.append(rec[t[0]])

            numpy.savetxt(stream, [fields], '%.18g')

    def _read_bin(self, stream):
        '''
        Load a PLY element from an binary PLY file.  The element may
        contain list properties.

        '''
        list_props = self.list_properties
        self.data = numpy.empty(self.count, dtype=self.dtype)

        for k in xrange(self.count):
            for prop in self.dtype:
                if prop[0] in list_props:
                    (len_t, val_t) = list_props[prop[0]]
                    n = numpy.fromfile(stream, len_t, 1)[0]

                    self.data[prop[0]][k] = numpy.fromfile(
                            stream, val_t, n)
                else:
                    self.data[prop[0]][k] = numpy.fromfile(
                            stream, prop[1], 1)[0]

    def _write_bin(self, stream):
        '''
        Save a PLY element to a binary PLY file.  The element may
        contain list properties.

        '''
        list_props = self.list_properties

        for rec in self.data:
            for t in self.dtype:
                if t[0] in list_props:
                    (len_type, val_type) = list_props[t[0]]
                    list_len = numpy.array(rec[t[0]].size,
                                           dtype=len_type)
                    list_vals = rec[t[0]].astype(val_type, copy=False)

                    list_len.tofile(stream)
                    list_vals.tofile(stream)
                else:
                    rec[t[0]].astype(t[1]).tofile(stream)

    @property
    def header(self):
        '''
        Format this element's metadata as it would appear in a PLY
        header.

        '''
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

    def __str__(self):
        return self.header

    def __repr__(self):
        return str(self)
