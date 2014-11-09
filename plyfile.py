#   Copyright 2014 Darsh Ranjan
#
#   This file is part of python-plyfile.
#
#   python-plyfile is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   python-plyfile is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with termcolors.  If not, see <http://www.gnu.org/licenses/>.

from itertools import islice as _islice

import numpy as _np
from sys import byteorder as _byteorder


try:
    range = xrange
except:
    pass


_data_types = {
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

_data_type_reverse = {
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

_byte_order_map = {
    'ascii': '=',
    'binary_little_endian': '<',
    'binary_big_endian': '>'
}

_byte_order_reverse = {
    '<': 'binary_little_endian',
    '>': 'binary_big_endian'
}


_native_byte_order = {'little': '<', 'big': '>'}[_byteorder]


def _lookup_type(type_str):
    if type_str not in _data_type_reverse:
        raise ValueError("unsupported field type: %s" % type_str)

    return _data_type_reverse[type_str]


def _split_line(line, n):
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
            byte_order = _native_byte_order

        self.byte_order = byte_order
        self.text = text

        self.comments = list(comments)
        self.elements = list(elements)
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
            line = stream.readline().decode('ascii').strip()
            fields = _split_line(line, 1)

            if fields[0] == 'end_header':
                break

            elif fields[0] == 'comment':
                lines.append(fields)
            else:
                lines.append(line.split())

        a = 0
        if lines[a] != ['ply']:
            raise RuntimeError("expected 'ply'")

        a += 1
        while lines[a][0] == 'comment':
            comments.append(lines[a][1])
            a += 1

        if lines[a][0] != 'format':
            raise RuntimeError("expected 'format'")

        if lines[a][2] != '1.0':
            raise RuntimeError("expected version '1.0'")

        if len(lines[a]) != 3:
            raise RuntimeError("too many fields after 'format'")

        fmt = lines[a][1]

        if fmt not in _byte_order_map:
            raise RuntimeError("don't understand format %r" % fmt)

        byte_order = _byte_order_map[fmt]
        text = fmt == 'ascii'

        a += 1
        while lines[a][0] == 'comment':
            comments.append(lines[a][1])
            a += 1

        return PlyData(PlyElement._parse_multi(lines[a:]),
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
                elt._read(stream, data.text, data.byte_order)

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

            stream.write(self.header.encode('ascii'))
            stream.write(b'\r\n')

            for elt in self:
                elt._write(stream, self.text, self.byte_order)

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
                         _byte_order_reverse[self.byte_order] +
                         ' 1.0')

        # Some information is lost here, since all comments are placed
        # between the 'format' line and the first element.
        for c in self.comments:
            lines.append('comment ' + c)

        lines.extend(elt.header for elt in self.elements)
        lines.append('end_header')
        return '\r\n'.join(lines)

    def __iter__(self):
        return iter(self.elements)

    def __len__(self):
        return len(self.elements)

    def __contains__(self, name):
        return name in self._element_lookup

    def __getitem__(self, name):
        return self._element_lookup[name]

    def __str__(self):
        return self.header

    def __repr__(self):
        return ('PlyData(%r, text=%r, byte_order=%r, comments=%r)' %
                (self.elements, self.text, self.byte_order,
                 self.comments))


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

    def __init__(self, name, properties, count, comments=[]):
        '''
        This is not part of the public interface.  The preferred methods
        of obtaining PlyElement instances are PlyData.read (to read from
        a file) and PlyElement.describe (to construct from a numpy
        array).

        '''
        self.name = name
        self.count = count

        self.properties = properties
        self.comments = list(comments)

        self._have_list = any(isinstance(p, PlyListProperty)
                              for p in self.properties)

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        if any(c.isspace() for c in name):
            msg = "element name %r contains spaces" % name
            raise RuntimeError(msg)

        self._name = name

    name = property(_get_name, _set_name)

    def dtype(self, byte_order='='):
        '''
        Return the numpy dtype of the in-memory representation of the
        data.  (If there are no list properties, and the PLY format is
        binary, then this also accurately describes the on-disk
        representation of the element.)

        '''
        return [(prop.name, prop.dtype(byte_order))
                for prop in self.properties]

    @staticmethod
    def _parse_multi(header_lines):
        '''
        Parse a list of PLY element definitions.

        '''
        elements = []
        while header_lines:
            (elt, header_lines) = PlyElement._parse_one(header_lines)
            elements.append(elt)

        return elements

    @staticmethod
    def _parse_one(lines):
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

        comments = []
        properties = []
        while True:
            a += 1
            if a >= len(lines):
                break

            if lines[a][0] == 'comment':
                comments.append(lines[a][1])
            elif lines[a][0] == 'property':
                properties.append(PlyProperty._parse_one(lines[a]))
            else:
                break

        return (PlyElement(name, properties, count, comments),
                lines[a:])

    @staticmethod
    def describe(data, name, len_types={}, val_types={},
                 comments=[]):
        '''
        Construct a PlyElement from an array's metadata.

        len_types and val_types can be given as mappings from list
        property names to type strings (like 'u1', 'f4', etc.). These
        can be used to define the length and value types of list
        properties.  List property lengths always default to type 'u1'
        (8-bit unsigned integer), and value types default to 'i4'
        (32-bit integer).

        '''
        if not isinstance(data, _np.ndarray):
            raise TypeError("only numpy arrays are supported")

        if len(data.shape) != 1:
            raise ValueError("only one-dimensional arrays are "
                             "supported")

        count = len(data)

        properties = []
        descr = data.dtype.descr

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

                len_str = _data_type_reverse[len_types.get(t[0], 'u1')]
                if t[1][1] == 'O':
                    val_type = val_types.get(t[0], 'i4')
                    val_str = _lookup_type(val_type)
                else:
                    val_str = _lookup_type(t[1][1:])

                prop = PlyListProperty(t[0], len_str, val_str)
            else:
                val_str = _lookup_type(t[1][1:])
                prop = PlyProperty(t[0], val_str)

            properties.append(prop)

        elt = PlyElement(name, properties, count, comments)
        elt.data = data

        return elt

    def _read(self, stream, text, byte_order):
        '''
        Read the actual data from a PLY file.

        '''
        if self._have_list:
            # There are list properties, so a simple load is
            # impossible.
            if text:
                self._read_txt(stream)
            else:
                self._read_bin(stream, byte_order)
        else:
            # There are no list properties, so loading the data is
            # much more straightforward.
            if text:
                self.data = _np.loadtxt(
                    _islice(iter(stream.readline, ''), self.count),
                    self.dtype())
            else:
                self.data = _np.fromfile(
                    stream, self.dtype(byte_order), self.count)

    def _write(self, stream, text, byte_order):
        '''
        Write the data to a PLY file.

        '''
        if self._have_list:
            # There are list properties, so serialization is
            # slightly complicated.
            if text:
                self._write_txt(stream)
            else:
                self._write_bin(stream, byte_order)
        else:
            # no list properties, so serialization is
            # straightforward.
            if text:
                _np.savetxt(stream, self.data, '%.18g', newline='\r\n')
            else:
                data = self.data.astype(self.dtype(byte_order),
                                        copy=False)
                data.tofile(stream)

    def _read_txt(self, stream):
        '''
        Load a PLY element from an ASCII-format PLY file.  The element
        may contain list properties.

        '''
        self.data = _np.empty(self.count,
                              dtype=self.dtype())

        for (k, line) in enumerate(_islice(iter(stream.readline, ''),
                                           self.count)):
            fields = iter(line.strip().split())
            for prop in self.properties:
                self.data[prop.name][k] = prop._from_fields(fields)

    def _write_txt(self, stream):
        '''
        Save a PLY element to an ASCII-format PLY file.  The element may
        contain list properties.

        '''
        for rec in self.data:
            fields = []
            for prop in self.properties:
                fields.extend(prop._to_fields(rec[prop.name]))

            _np.savetxt(stream, [fields], '%.18g', newline='\r\n')

    def _read_bin(self, stream, byte_order):
        '''
        Load a PLY element from a binary PLY file.  The element may
        contain list properties.

        '''
        self.data = _np.empty(self.count,
                              dtype=self.dtype(byte_order))

        for k in range(self.count):
            for prop in self.properties:
                self.data[prop.name][k] = prop._read_bin(stream,
                                                         byte_order)

    def _write_bin(self, stream, byte_order):
        '''
        Save a PLY element to a binary PLY file.  The element may
        contain list properties.

        '''
        for rec in self.data:
            for prop in self.properties:
                prop._write_bin(rec[prop.name], stream, byte_order)

    @property
    def header(self):
        '''
        Format this element's metadata as it would appear in a PLY
        header.

        '''
        lines = ['element %s %d' % (self.name, self.count)]

        # Some information is lost here, since all comments are placed
        # between the 'element' line and the first property definition.
        for c in self.comments:
            lines.append('comment ' + c)

        lines.extend(list(map(str, self.properties)))

        return '\r\n'.join(lines)

    def __str__(self):
        return self.header

    def __repr__(self):
        return ('PlyElement(%r, %r, count=%d, comments=%r)' %
                (self.name, self.properties, self.count,
                 self.comments))


class PlyProperty(object):

    '''
    PLY property description.  This class is pure metadata; the data
    itself is contained in PlyElement instances.

    '''

    def __init__(self, name, val_dtype):
        self.name = name
        self.val_dtype = _data_types[val_dtype]

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        name = str(name)

        if any(c.isspace() for c in name):
            msg = "Error: property name %r contains spaces" % name
            raise RuntimeError(msg)

        self._name = name

    name = property(_get_name, _set_name)

    @staticmethod
    def _parse_one(line):
        assert line[0] == 'property'

        if line[1] == 'list':
            if len(line) > 5:
                raise RuntimeError("too many fields after "
                                   "'property list'")
            if len(line) < 5:
                raise RuntimeError("too few fields after "
                                   "'property list'")

            return PlyListProperty(line[4], line[2], line[3])

        else:
            if len(line) > 3:
                raise RuntimeError("too many fields after "
                                   "'property'")
            if len(line) < 3:
                raise RuntimeError("too few fields after "
                                   "'property'")

            return PlyProperty(line[2], line[1])

    def dtype(self, byte_order='='):
        '''
        Return the numpy dtype description for this property (as a tuple
        of strings).

        '''
        return byte_order + self.val_dtype

    def _from_fields(self, fields):
        '''
        Parse one item from generator.

        '''
        return _np.fromstring(next(fields), self.dtype(), sep=' ')

    def _to_fields(self, data):
        '''
        Return generator over one item.

        '''
        yield data

    def _read_bin(self, stream, byte_order):
        '''
        Read data from a binary stream.

        '''
        return _np.fromfile(stream, self.dtype(byte_order), 1)[0]

    def _write_bin(self, data, stream, byte_order):
        '''
        Write data to a binary stream.

        '''
        data.astype(self.dtype(byte_order)).tofile(stream)

    def __str__(self):
        val_str = _data_type_reverse[self.val_dtype]
        return 'property %s %s' % (val_str, self.name)

    def __repr__(self):
        return 'PlyProperty(%r, %r)' % (self.name,
                                        _lookup_type(self.val_dtype))


class PlyListProperty(PlyProperty):

    '''
    PLY list property description.

    '''

    def __init__(self, name, len_dtype, val_dtype):
        PlyProperty.__init__(self, name, val_dtype)

        self.len_dtype = _data_types[len_dtype]

    def dtype(self, byte_order='='):
        '''
        List properties always have a numpy dtype of "object".

        '''
        return '|O'

    def list_dtype(self, byte_order='='):
        '''
        Return the pair (len_dtype, val_dtype) (both numpy-friendly
        strings).

        '''
        return (byte_order + self.len_dtype,
                byte_order + self.val_dtype)

    def _from_fields(self, fields):
        '''
        Parse textual data from a generator.

        '''
        (len_t, val_t) = self.list_dtype()

        n = int(next(fields))

        return _np.loadtxt(list(_islice(fields, n)), val_t, ndmin=1)

    def _to_fields(self, data):
        '''
        Return generator over the (numerical) PLY representation of the
        list data (length followed by actual data).

        '''
        yield data.size
        for x in data.ravel():
            yield x

    def _read_bin(self, stream, byte_order):
        '''
        Read data from a binary stream.

        '''
        (len_t, val_t) = self.list_dtype(byte_order)

        n = _np.fromfile(stream, len_t, 1)[0]

        return _np.fromfile(stream, val_t, n)

    def _write_bin(self, data, stream, byte_order):
        '''
        Write data to a binary stream.

        '''
        (len_t, val_t) = self.list_dtype(byte_order)

        _np.array(data.size, dtype=len_t).tofile(stream)
        data.astype(val_t, copy=False).tofile(stream)

    def __str__(self):
        len_str = _data_type_reverse[self.len_dtype]
        val_str = _data_type_reverse[self.val_dtype]
        return 'property list %s %s %s' % (len_str, val_str, self.name)

    def __repr__(self):
        return ('PlyListProperty(%r, %r, %r)' %
                (self.name,
                 _lookup_type(self.len_dtype),
                 _lookup_type(self.val_dtype)))
