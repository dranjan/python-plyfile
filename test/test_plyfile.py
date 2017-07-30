from __future__ import print_function

import sys

from io import BytesIO

import pytest

import numpy

from plyfile import (PlyData, PlyElement, make2d,
                     PlyHeaderParseError, PlyElementParseError,
                     PlyProperty)


try:
    _range = xrange
except NameError:
    _range = range


class Raises(object):

    '''
    Utility: use as a context manager for code that is expected to raise
    an exception.

    '''
    def __init__(self, *exc_types):
        self._exc_types = set(exc_types)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        assert exc_type in self._exc_types
        self.exc_type = exc_type
        self.exc_val = exc_val
        self.traceback = traceback
        return True

    def __str__(self):
        return str(self.exc_val)


def normalize_property(prop):
    if prop.ndim == 1:
        return prop

    n = len(prop)

    arr = numpy.empty(n, dtype='O')
    for k in _range(n):
        arr[k] = prop[k]

    return arr


def verify(ply0, ply1):
    '''
    Verify that two PlyData instances describe the same data.

    '''
    el0 = ply0.elements
    el1 = ply1.elements

    num_elements = len(el0)
    assert len(el1) == num_elements

    for k in _range(num_elements):
        assert el0[k].name == el1[k].name

        data0 = el0[k].data
        data1 = el1[k].data

        dtype0 = el0[k].dtype().descr
        dtype1 = el1[k].dtype().descr

        num_properties = len(dtype0)
        assert len(dtype1) == num_properties

        for j in _range(num_properties):
            prop_name = dtype0[j][0]
            assert dtype1[j][0] == prop_name

            prop0 = normalize_property(data0[prop_name])
            prop1 = normalize_property(data1[prop_name])

            verify_1d(prop0, prop1)

        verify_comments(el0[k].comments, el1[k].comments)

    verify_comments(ply0.comments, ply1.comments)
    verify_comments(ply0.obj_info, ply1.obj_info)


def verify_1d(prop0, prop1):
    '''
    Verify that two 1-dimensional arrays (possibly of type object)
    describe the same data.

    '''
    n = len(prop0)
    assert len(prop1) == n

    s0 = prop0.dtype.descr[0][1][1:]
    s1 = prop1.dtype.descr[0][1][1:]

    assert s0 == s1
    s = s0[0]

    if s == 'O':
        for k in _range(n):
            assert len(prop0[k]) == len(prop1[k])
            assert (prop0[k] == prop1[k]).all()
    else:
        assert (prop0 == prop1).all()


def verify_comments(comments0, comments1):
    '''
    Verify that comment lists are identical.

    '''
    assert len(comments0) == len(comments1)
    for (comment0, comment1) in zip(comments0, comments1):
        assert comment0 == comment1


def write_read(ply, tmpdir, name='test.ply'):
    '''
    Utility: serialize/deserialize a PlyData instance through a
    temporary file.

     '''
    filename = tmpdir.join(name)
    ply.write(str(filename))
    return PlyData.read(str(filename))


def read_str(string, tmpdir, name='test.ply'):
    '''
    Utility: create a PlyData instance from a string.

    '''
    filename = tmpdir.join(name)
    with filename.open('wb') as f:
        f.write(string)
    return PlyData.read(str(filename))


def tet_ply(text, byte_order):
    vertex = numpy.array([(0, 0, 0),
                          (0, 1, 1),
                          (1, 0, 1),
                          (1, 1, 0)],
                         dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4')])

    face = numpy.array([([0, 1, 2], 255, 255, 255),
                        ([0, 2, 3], 255,   0,   0),
                        ([0, 1, 3],   0, 255,   0),
                        ([1, 2, 3],   0,   0, 255)],
                       dtype=[('vertex_indices', 'i4', (3,)),
                              ('red', 'u1'), ('green', 'u1'),
                              ('blue', 'u1')])

    return PlyData(
        [
            PlyElement.describe(
                vertex, 'vertex',
                comments=['tetrahedron vertices']
            ),
            PlyElement.describe(face, 'face')
        ],
        text=text, byte_order=byte_order,
        comments=['single tetrahedron with colored faces']
    )


@pytest.fixture(scope='function')
def tet_ply_txt():
    return tet_ply(True, '=')


tet_ply_ascii = '''\
ply\n\
format ascii 1.0\n\
comment single tetrahedron with colored faces\n\
element vertex 4\n\
comment tetrahedron vertices\n\
property float x\n\
property float y\n\
property float z\n\
element face 4\n\
property list uchar int vertex_indices\n\
property uchar red\n\
property uchar green\n\
property uchar blue\n\
end_header\n\
0 0 0\n\
0 1 1\n\
1 0 1\n\
1 1 0\n\
3 0 1 2 255 255 255\n\
3 0 2 3 255 0 0\n\
3 0 1 3 0 255 0\n\
3 1 2 3 0 0 255\n\
'''.encode('ascii')

np_types = ['i1', 'u1', 'i2', 'u2', 'i4', 'u4', 'f4', 'f8']


def test_str(tet_ply_txt):
    # Nothing to assert; just make sure the call succeeds
    str(tet_ply_txt)


def test_repr(tet_ply_txt):
    # Nothing to assert; just make sure the call succeeds
    repr(tet_ply_txt)


@pytest.mark.parametrize('np_type', np_types)
def test_property_type(tmpdir, np_type):
    dtype = [('x', np_type), ('y', np_type), ('z', np_type)]
    a = numpy.array([(1, 2, 3), (4, 5, 6)], dtype=dtype)

    ply0 = PlyData([PlyElement.describe(a, 'test')])

    assert ply0.elements[0].name == 'test'
    assert ply0.elements[0].properties[0].name == 'x'
    assert ply0.elements[0].properties[0].val_dtype == np_type
    assert ply0.elements[0].properties[1].name == 'y'
    assert ply0.elements[0].properties[1].val_dtype == np_type
    assert ply0.elements[0].properties[2].name == 'z'
    assert ply0.elements[0].properties[2].val_dtype == np_type

    ply1 = write_read(ply0, tmpdir)

    assert ply1.elements[0].name == 'test'
    assert ply1.elements[0].data.dtype == dtype
    verify(ply0, ply1)


@pytest.mark.parametrize('np_type', np_types)
def test_list_property_type(tmpdir, np_type):
    a = numpy.array([([0],), ([1, 2, 3],)], dtype=[('x', object)])

    ply0 = PlyData([PlyElement.describe(a, 'test',
                                        val_types={'x': np_type})])

    assert ply0.elements[0].name == 'test'
    assert ply0.elements[0].properties[0].name == 'x'
    assert ply0.elements[0].properties[0].val_dtype == np_type

    ply1 = write_read(ply0, tmpdir)

    assert ply1.elements[0].name == 'test'
    assert ply1.elements[0].data[0]['x'].dtype == numpy.dtype(np_type)
    verify(ply0, ply1)


@pytest.mark.parametrize('len_type',
                         ['i1', 'u1', 'i2', 'u2', 'i4', 'u4'])
def test_list_property_len_type(tmpdir, len_type):
    a = numpy.array([([0],), ([1, 2, 3],)], dtype=[('x', object)])

    ply0 = PlyData([PlyElement.describe(a, 'test',
                                        len_types={'x': len_type})])

    assert ply0.elements[0].name == 'test'
    assert ply0.elements[0].properties[0].name == 'x'
    assert ply0.elements[0].properties[0].val_dtype == 'i4'
    assert ply0.elements[0].properties[0].len_dtype == len_type

    ply1 = write_read(ply0, tmpdir)

    assert ply1.elements[0].name == 'test'
    assert ply1.elements[0].data[0]['x'].dtype == numpy.dtype('i4')
    verify(ply0, ply1)


def test_write_stream(tmpdir, tet_ply_txt):
    ply0 = tet_ply_txt
    test_file = tmpdir.join('test.ply')

    with test_file.open('wb') as f:
        tet_ply_txt.write(f)

    ply1 = PlyData.read(str(test_file))
    verify(ply0, ply1)


def test_read_stream(tmpdir, tet_ply_txt):
    ply0 = tet_ply_txt
    test_file = tmpdir.join('test.ply')

    tet_ply_txt.write(str(test_file))

    with test_file.open('rb') as f:
        ply1 = PlyData.read(f)

    verify(ply0, ply1)


def test_write_read_str_filename(tmpdir, tet_ply_txt):
    ply0 = tet_ply_txt
    test_file = tmpdir.join('test.ply')
    filename = str(test_file)

    tet_ply_txt.write(filename)
    ply1 = PlyData.read(filename)

    verify(ply0, ply1)


def test_memmap(tmpdir, tet_ply_txt):
    vertex = tet_ply_txt['vertex']
    face0 = PlyElement.describe(tet_ply_txt['face'].data, 'face0')
    face1 = PlyElement.describe(tet_ply_txt['face'].data, 'face1')

    # Since the memory mapping requires some manual offset calculation,
    # check that it's done correctly when there are elements before
    # and after the one that can be memory-mapped.
    ply0 = PlyData([face0, vertex, face1])
    ply1 = write_read(ply0, tmpdir)

    verify(ply0, ply1)


def test_copy_on_write(tmpdir, tet_ply_txt):
    ply0 = tet_ply_txt
    filename = str(tmpdir.join('test.ply'))
    ply0.write(filename)
    ply1 = PlyData.read(filename)
    ply1['vertex']['x'] += 1
    ply2 = PlyData.read(filename)

    verify(ply0, ply2)


# In Python 3, `unicode' is not a separate type from `str' (and the
# `unicode' builtin does not exist).  Thus, this test is unnecessary
# (and indeed would not pass).
@pytest.mark.skipif(sys.version_info >= (3,),
                    reason="only relevant on Python 2")
def test_write_read_unicode_filename(tmpdir, tet_ply_txt):
    ply0 = tet_ply_txt
    test_file = tmpdir.join('test.ply')
    filename = unicode(str(test_file))

    tet_ply_txt.write(filename)
    ply1 = PlyData.read(filename)

    verify(ply0, ply1)


def test_write_invalid_filename(tet_ply_txt):
    with Raises(RuntimeError) as e:
        tet_ply_txt.write(None)

    assert str(e) == "expected open file or filename"


def test_ascii(tet_ply_txt, tmpdir):
    test_file = tmpdir.join('test.ply')

    tet_ply_txt.write(str(test_file))
    assert test_file.read('rb') == tet_ply_ascii


@pytest.mark.parametrize('text,byte_order',
                         [(True, '='), (False, '<'), (False, '>')])
def test_write_read(tet_ply_txt, tmpdir, text, byte_order):
    ply0 = PlyData(tet_ply_txt.elements, text, byte_order,
                   tet_ply_txt.comments)
    ply1 = write_read(ply0, tmpdir)
    verify(ply0, ply1)


def test_switch_format(tet_ply_txt, tmpdir):
    ply0 = tet_ply_txt
    ply1 = write_read(ply0, tmpdir, 'test0.ply')
    verify(ply0, ply1)
    ply1.text = False
    ply1.byte_order = '<'
    ply2 = write_read(ply1, tmpdir, 'test1.ply')
    assert ply2.byte_order == '<'
    verify(ply0, ply2)
    ply2.byte_order = '>'
    ply3 = write_read(ply2, tmpdir, 'test2.ply')
    assert ply3.byte_order == '>'
    verify(ply0, ply3)


def test_invalid_byte_order(tet_ply_txt):
    with Raises(ValueError):
        tet_ply_txt.byte_order = 'xx'


def test_element_lookup(tet_ply_txt):
    assert tet_ply_txt['vertex'].name == 'vertex'
    assert tet_ply_txt['face'].name == 'face'


def test_property_lookup(tet_ply_txt):
    vertex = tet_ply_txt['vertex'].data
    assert (tet_ply_txt.elements[0]['x'] == vertex['x']).all()
    assert (tet_ply_txt.elements[0]['y'] == vertex['y']).all()
    assert (tet_ply_txt.elements[0]['z'] == vertex['z']).all()

    face = tet_ply_txt['face'].data
    assert (tet_ply_txt.elements[1]['vertex_indices'] ==
            face['vertex_indices']).all()
    assert (tet_ply_txt.elements[1]['red'] == face['red']).all()
    assert (tet_ply_txt.elements[1]['green'] == face['green']).all()
    assert (tet_ply_txt.elements[1]['blue'] == face['blue']).all()


def test_obj_info(tmpdir):
    ply0 = PlyData([], text=True, obj_info=['test obj_info'])
    test_file = tmpdir.join('test.ply')
    ply0.write(str(test_file))

    ply0_str = test_file.read('rb').decode('ascii')
    assert ply0_str.startswith('ply\nformat ascii 1.0\n'
                               'obj_info test obj_info\n')

    ply1 = PlyData.read(str(test_file))
    assert len(ply1.obj_info) == 1
    assert ply1.obj_info[0] == 'test obj_info'


def test_comment_spaces(tmpdir):
    ply0 = PlyData([], text=True, comments=['  test comment'])
    test_file = tmpdir.join('test.ply')
    ply0.write(str(test_file))

    ply0_str = test_file.read('rb').decode('ascii')
    assert ply0_str.startswith('ply\nformat ascii 1.0\n'
                               'comment   test comment\n')

    ply1 = PlyData.read(str(test_file))
    assert len(ply1.comments) == 1
    assert ply1.comments[0] == '  test comment'


def test_assign_comments(tet_ply_txt):
    ply0 = tet_ply_txt

    ply0.comments = ['comment1', 'comment2']
    ply0.obj_info = ['obj_info1', 'obj_info2']
    verify_comments(ply0.comments, ['comment1', 'comment2'])
    verify_comments(ply0.obj_info, ['obj_info1', 'obj_info2'])

    ply0['face'].comments = ['comment1']
    verify_comments(ply0['face'].comments, ['comment1'])


def test_assign_comments_newline(tet_ply_txt):
    ply0 = tet_ply_txt

    with Raises(ValueError):
        ply0.comments = ['comment1\ncomment2']

    with Raises(ValueError):
        ply0.obj_info = ['comment1\ncomment2']

    with Raises(ValueError):
        ply0['face'].comments = ['comment1\ncomment2']


def test_assign_comments_non_ascii(tet_ply_txt):
    ply0 = tet_ply_txt

    with Raises(ValueError):
        ply0.comments = ['\xb0']

    with Raises(ValueError):
        ply0.obj_info = ['\xb0']

    with Raises(ValueError):
        ply0['face'].comments = ['\xb0']


def test_make2d():
    a = numpy.empty(2, dtype=object)
    a[:] = [numpy.array([0, 1, 2]), numpy.array([3, 4, 5])]

    b = make2d(a)
    assert b.shape == (2, 3)
    assert (b == [[0, 1, 2], [3, 4, 5]]).all()


def test_reorder_elements(tet_ply_txt, tmpdir):
    ply0 = tet_ply_txt
    (vertex, face) = ply0.elements
    ply0.elements = [face, vertex]

    ply1 = write_read(ply0, tmpdir)

    assert ply1.elements[0].name == 'face'
    assert ply1.elements[1].name == 'vertex'


def test_assign_elements_duplicate(tet_ply_txt):
    with Raises(ValueError) as e:
        tet_ply_txt.elements = [tet_ply_txt['vertex'],
                                tet_ply_txt['vertex']]
    assert str(e) == "two elements with same name"


def test_reorder_properties(tet_ply_txt, tmpdir):
    ply0 = tet_ply_txt
    vertex = ply0.elements[0]
    (x, y, z) = vertex.properties
    vertex.properties = [y, z, x]

    ply1 = write_read(ply0, tmpdir)

    assert ply1.elements[0].properties[0].name == 'y'
    assert ply1.elements[0].properties[1].name == 'z'
    assert ply1.elements[0].properties[2].name == 'x'

    verify_1d(ply0['vertex']['x'], ply1['vertex']['x'])
    verify_1d(ply0['vertex']['y'], ply1['vertex']['y'])
    verify_1d(ply0['vertex']['z'], ply1['vertex']['z'])


@pytest.mark.parametrize('text,byte_order',
                         [(True, '='), (False, '<'), (False, '>')])
def test_remove_property(tet_ply_txt, tmpdir, text, byte_order):
    ply0 = tet_ply_txt
    face = ply0.elements[1]
    (vertex_indices, r, g, b) = face.properties
    face.properties = [vertex_indices]

    ply0.text = text
    ply0.byte_order = byte_order

    ply1 = write_read(ply0, tmpdir)

    assert ply1.text == text
    assert ply1.byte_order == byte_order

    assert len(ply1.elements[1].properties) == 1
    assert ply1.elements[1].properties[0].name == 'vertex_indices'

    verify_1d(normalize_property(ply1['face']['vertex_indices']),
              normalize_property(face['vertex_indices']))


def test_assign_properties_error(tet_ply_txt):
    vertex = tet_ply_txt['vertex']
    with Raises(ValueError) as e:
        vertex.properties = (vertex.properties +
                             (PlyProperty('xx', 'i4'),))
    assert str(e) == "dangling property 'xx'"


def test_assign_properties_duplicate(tet_ply_txt):
    vertex = tet_ply_txt['vertex']
    with Raises(ValueError) as e:
        vertex.properties = (vertex.ply_property('x'),
                             vertex.ply_property('x'))
    assert str(e) == "two properties with same name"


@pytest.mark.parametrize('text,byte_order',
                         [(True, '='), (False, '<'), (False, '>')])
def test_cast_property(tet_ply_txt, tmpdir, text, byte_order):
    ply0 = tet_ply_txt
    (vertex, face) = ply0.elements
    vertex.properties[0].val_dtype = 'f8'
    vertex.properties[2].val_dtype = 'u1'

    assert face.properties[0].len_dtype == 'u1'
    face.properties[0].len_dtype = 'i4'

    ply0.text = text
    ply0.byte_order = byte_order

    ply1 = write_read(ply0, tmpdir)

    assert ply1.text == text
    assert ply1.byte_order == byte_order

    assert ply1['vertex']['x'].dtype.descr[0][1][1:] == 'f8'
    assert ply1['vertex']['y'].dtype.descr[0][1][1:] == 'f4'
    assert ply1['vertex']['z'].dtype.descr[0][1][1:] == 'u1'

    assert(ply1['vertex']['x'] == vertex['x']).all()
    assert(ply1['vertex']['y'] == vertex['y']).all()
    assert(ply1['vertex']['z'] == vertex['z']).all()

    assert ply1['face'].properties[0].len_dtype == 'i4'

    verify_1d(normalize_property(ply1['face']['vertex_indices']),
              normalize_property(face['vertex_indices']))


def test_cast_val_error(tet_ply_txt):
    with Raises(ValueError) as e:
        tet_ply_txt['vertex'].properties[0].val_dtype = 'xx'
    assert str(e).startswith("field type 'xx' not in")


def test_cast_len_error(tet_ply_txt):
    with Raises(ValueError) as e:
        tet_ply_txt['face'].properties[0].len_dtype = 'xx'
    assert str(e).startswith("field type 'xx' not in")


def ply_abc(fmt, n, data):
    string = (b"ply\nformat " + fmt.encode() + b" 1.0\nelement test " +
              str(n).encode() + b"\n"
              b"property uchar a\nproperty uchar b\n property uchar c\n"
              b"end_header\n")
    if fmt == 'ascii':
        return string + data + b'\n'
    else:
        return string + data


def ply_list_a(fmt, n, data):
    string = (b"ply\nformat " + fmt.encode() + b" 1.0\nelement test " +
              str(n).encode() + b"\n"
              b"property list uchar int a\n"
              b"end_header\n")
    if fmt == 'ascii':
        return string + data + b'\n'
    else:
        return string + data


invalid_cases = [
    (ply_abc('ascii', 1, b'1 2 3.3'),
     "row 0: property 'c': malformed input"),

    (ply_list_a('ascii', 1, b''),
     "row 0: property 'a': early end-of-line"),

    (ply_list_a('ascii', 1, b'3 2 3'),
     "row 0: property 'a': early end-of-line"),

    (ply_abc('ascii', 1, b'1 2 3 4'),
     "row 0: expected end-of-line"),

    (ply_abc('ascii', 1, b'1'),
     "row 0: property 'b': early end-of-line"),

    (ply_abc('ascii', 2, b'1 2 3'),
     "row 1: early end-of-file"),

    (ply_abc('binary_little_endian', 1, b'\x01\x02'),
     "row 0: early end-of-file"),

    (ply_list_a('binary_little_endian', 1, b''),
     "row 0: property 'a': early end-of-file"),

    (ply_list_a('binary_little_endian', 1,
                b'\x03\x01\x00\x00\x00\x02\x00\x00\x00'),
     "row 0: property 'a': early end-of-file"),

    (ply_list_a('binary_little_endian', 1, b'\x01\x02'),
     "row 0: property 'a': early end-of-file"),

    (ply_abc('binary_little_endian', 2, b'\x01\x02\x03'),
     "row 1: early end-of-file")
]


@pytest.mark.parametrize('s,error_string', invalid_cases,
                         ids=list(map(str, _range(len(invalid_cases)))))
def test_invalid(tmpdir, s, error_string):
    with Raises(PlyElementParseError) as e:
        read_str(s, tmpdir)
    assert str(e) == "element 'test': " + error_string


def test_assign_elements(tet_ply_txt):
    test = PlyElement.describe(numpy.zeros(1, dtype=[('a', 'i4')]),
                               'test')
    tet_ply_txt.elements = [test]
    assert len(tet_ply_txt.elements) == 1
    assert len(tet_ply_txt) == 1
    assert 'vertex' not in tet_ply_txt
    assert 'face' not in tet_ply_txt
    assert 'test' in tet_ply_txt

    for (k, elt) in enumerate(tet_ply_txt):
        assert elt.name == 'test'
        assert k == 0


def test_assign_data(tet_ply_txt):
    face = tet_ply_txt['face']
    face.data = face.data[:1]

    assert face.count == 1


def test_assign_data_error(tet_ply_txt):
    vertex = tet_ply_txt['vertex']

    with Raises(ValueError) as e:
        vertex.data = vertex[['x', 'z']]
    assert str(e) == "dangling property 'y'"


def test_invalid_element_names():
    with Raises(ValueError):
        PlyElement.describe(numpy.zeros(1, dtype=[('a', 'i4')]),
                            '\xb0')

    with Raises(ValueError):
        PlyElement.describe(numpy.zeros(1, dtype=[('a', 'i4')]),
                            'test test')


def test_invalid_property_names():
    with Raises(ValueError):
        PlyElement.describe(numpy.zeros(1, dtype=[('\xb0', 'i4')]),
                            'test')

    with Raises(ValueError):
        PlyElement.describe(numpy.zeros(1, dtype=[('a b', 'i4')]),
                            'test')

invalid_header_cases = [
    (b'plyy\n', 1),
    (b'ply xxx\n', 1),
    (b'ply\n\n', 2),
    (b'ply\nformat\n', 2),
    (b'ply\nelement vertex 0\n', 2),
    (b'ply\nformat asciii 1.0\n', 2),
    (b'ply\nformat ascii 2.0\n', 2),
    (b'ply\nformat ascii 1.0\n', 3),
    (b'ply\nformat ascii 1.0\nelement vertex\n', 3),
    (b'ply\nformat ascii 1.0\nelement vertex x\n', 3),
    (b'ply\nformat ascii 1.0\nelement vertex 0\n'
     b'property float\n', 4),
    (b'ply\nformat ascii 1.0\nelement vertex 0\n'
     b'property list float\n', 4),
    (b'ply\nformat ascii 1.0\nelement vertex 0\n'
     b'property floatt x\n', 4),
    (b'ply\nformat ascii 1.0\nelement vertex 0\n'
     b'property float x y\n', 4),
    (b'ply\nformat ascii 1.0\nelement vertex 0\n'
     b'property list ucharr int extra\n', 4),
    (b'ply\nformat ascii 1.0\nelement vertex 0\n'
     b'property float x\nend_header xxx\n', 5)
]


@pytest.mark.parametrize(
    's,line', invalid_header_cases,
    ids=list(map(str, _range(len(invalid_header_cases))))
)
def test_header_parse_error(s, line):
    with Raises(PlyHeaderParseError) as e:
        PlyData.read(BytesIO(s))
    assert e.exc_val.line == line


invalid_arrays = [
    numpy.zeros((2,2)),
    numpy.array([(0, (0, 0))],
                dtype=[('x', 'f4'), ('y', [('y0', 'f4'), ('y1', 'f4')])]),
    numpy.array([(0, (0, 0))],
                dtype=[('x', 'f4'), ('y', 'O', (2,))])
]


@pytest.mark.parametrize(
    'a', invalid_arrays,
    ids=list(map(str, _range(len(invalid_arrays))))
)
def test_invalid_array(a):
    with Raises(ValueError):
        PlyElement.describe(a, 'test')


def test_invalid_array_type():
    with Raises(TypeError):
        PlyElement.describe([0, 1, 2], 'test')


def test_header_parse_error_repr():
    e = PlyHeaderParseError('text', 11)
    assert repr(e) == 'PlyHeaderParseError(\'text\', line=11)'


def test_element_parse_error_repr():
    prop = PlyProperty('x', 'f4')
    elt = PlyElement('test', [prop], 0)
    e = PlyElementParseError('text', elt, 0, prop)
    assert repr(e)
