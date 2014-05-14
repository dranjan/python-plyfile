import numpy

from plyfile import PlyData, PlyElement


def normalize_property(prop):
    if prop.ndim == 1:
        return prop

    n = len(prop)

    arr = numpy.empty(n, dtype='O')
    for k in xrange(n):
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

    for k in xrange(num_elements):
        assert el0[k].name == el1[k].name

        data0 = el0[k].data
        data1 = el1[k].data

        dtype0 = el0[k].dtype()
        dtype1 = el1[k].dtype()

        num_properties = len(dtype0)
        assert len(dtype1) == num_properties

        for j in xrange(num_properties):
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
        for k in xrange(n):
            assert len(prop0[k]) == len(prop1[k])
            assert (prop0[k] == prop1[k]).all()
    else:
        assert (prop0 == prop1).all()


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


print "Assembling initial PlyData instance..."
ply0 = PlyData([PlyElement.describe(vertex, 'vertex'),
                PlyElement.describe(face, 'face')],
               text=True,
               comments=['single tetrahedron with colored faces.'])

print "Writing test0.ply (ascii)..."
ply0.write('test0.ply')

print "Reading test0.ply..."
ply1 = PlyData.read('test0.ply')

print "(verifying result...)"
verify(ply0, ply1)

print "Writing test1.ply (binary_little_endian)..."
ply1.text = False
ply1.byte_order = '<'
ply1.write('test1.ply')

print "Reading test1.ply..."
ply2 = PlyData.read('test1.ply')

print "(verifying result...)"
assert ply2.byte_order == '<'
verify(ply0, ply2)

print "Writing test2.ply (binary_big_endian)..."
ply2.byte_order = '>'
ply2.write('test2.ply')

print "Reading test2.ply..."
ply3 = PlyData.read('test2.ply')

print "(verifying result...)"
assert ply3.byte_order == '>'
verify(ply0, ply3)

print "All tests passed!"
