from __future__ import print_function

import py
import pytest

import numpy

from plyfile import PlyData, PlyElement, make2d


try:
    range = xrange
except:
    pass


def normalize_property(prop):
    if prop.ndim == 1:
        return prop

    n = len(prop)

    arr = numpy.empty(n, dtype='O')
    for k in range(n):
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

    for k in range(num_elements):
        assert el0[k].name == el1[k].name

        data0 = el0[k].data
        data1 = el1[k].data

        dtype0 = el0[k].dtype()
        dtype1 = el1[k].dtype()

        num_properties = len(dtype0)
        assert len(dtype1) == num_properties

        for j in range(num_properties):
            prop_name = dtype0[j][0]
            assert dtype1[j][0] == prop_name

            prop0 = normalize_property(data0[prop_name])
            prop1 = normalize_property(data1[prop_name])

            verify_1d(prop0, prop1)


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
        for k in range(n):
            assert len(prop0[k]) == len(prop1[k])
            assert (prop0[k] == prop1[k]).all()
    else:
        assert (prop0 == prop1).all()


def write_read(ply, tmpdir, name='test.ply'):
    '''
    Utility: serialize/deserialize a PlyData instance through a
    temporary file.

    '''
    filename = tmpdir.join(name)
    ply.write(str(filename))
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


@pytest.fixture
def tet_ply_txt():
    return tet_ply(True, '=')


tet_ply_ascii = '''\
ply\r\n\
format ascii 1.0\r\n\
comment single tetrahedron with colored faces\r\n\
element vertex 4\r\n\
comment tetrahedron vertices\r\n\
property float x\r\n\
property float y\r\n\
property float z\r\n\
element face 4\r\n\
property list uchar int vertex_indices\r\n\
property uchar red\r\n\
property uchar green\r\n\
property uchar blue\r\n\
end_header\r\n\
0 0 0\r\n\
0 1 1\r\n\
1 0 1\r\n\
1 1 0\r\n\
3 0 1 2 255 255 255\r\n\
3 0 2 3 255 0 0\r\n\
3 0 1 3 0 255 0\r\n\
3 1 2 3 0 0 255\r\n\
'''.encode('ascii')

np_types = ['i1', 'u1', 'i2', 'u2', 'i4', 'u4', 'f4', 'f8']


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


def tet_read_stream(tmpdir, tet_ply_txt):
    ply0 = tet_ply_txt
    test_file = tmpdir.join('test.ply')

    tet_ply_txt.write(str(test_file))

    with test_file.open('rb') as f:
        ply1 = PlyData.read(f)

    verify(ply0, ply1)


def test_ascii(tet_ply_txt, tmpdir):
    test_file = tmpdir.join('test.ply')

    tet_ply_txt.write(str(test_file))
    assert test_file.read('rb') == tet_ply_ascii


@pytest.mark.parametrize('text,byte_order',
                         [(True, '='), (False, '<'), (False, '>')])
def test_write_read(tet_ply_txt, tmpdir, text, byte_order):
    ply0 = PlyData(tet_ply_txt.elements, text, byte_order, tet_ply_txt.comments)
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
    assert ply0_str.startswith('ply\r\nformat ascii 1.0\r\n'
                               'obj_info test obj_info\r\n')

    ply1 = PlyData.read(str(test_file))
    assert len(ply1.obj_info) == 1
    assert ply1.obj_info[0] == 'test obj_info'


def test_make2d():
    a = numpy.empty(2, dtype=object)
    a[:] = [numpy.array([0, 1, 2]), numpy.array([3, 4, 5])]

    b = make2d(a)
    assert b.shape == (2, 3)
    assert (b == [[0, 1, 2], [3, 4, 5]]).all()
