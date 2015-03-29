from __future__ import print_function

import py
import pytest

import numpy

from plyfile import PlyData, PlyElement


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
    s1 = prop0.dtype.descr[0][1][1:]

    assert s0 == s1
    s = s0[0]

    if s == 'O':
        for k in range(n):
            assert len(prop0[k]) == len(prop1[k])
            assert (prop0[k] == prop1[k]).all()
    else:
        assert (prop0 == prop1).all()


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


mydir = py.path.local(__file__).dirpath()
tet_ply_ascii = mydir.join('tet.ply').read('rb')


def test_ascii(tet_ply_txt, tmpdir):
    test = tmpdir.join('tet.ply')

    tet_ply_txt.write(str(test))
    assert test.read('rb') == tet_ply_ascii


def test_round_trip(tet_ply_txt, tmpdir):
    ply0 = tet_ply_txt
    test0 = tmpdir.join('test0.ply')

    ply0.write(str(test0))

    ply1 = PlyData.read(str(test0))
    verify(ply0, ply1)

    test1 = tmpdir.join('test1.ply')

    ply1.text = False
    ply1.byte_order = '<'
    ply1.write(str(test1))

    ply2 = PlyData.read(str(test1))
    assert ply2.byte_order == '<'
    verify(ply0, ply2)

    test2 = tmpdir.join('test2.ply')

    ply2.byte_order = '>'
    ply2.write(str(test2))

    ply3 = PlyData.read(str(test2))

    assert ply3.byte_order == '>'
    verify(ply0, ply3)
