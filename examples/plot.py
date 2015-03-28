'''
Example script illustrating plotting of PLY data using Mayavi.  Mayavi
is not a dependency of plyfile, but you will need to install it in order
to run this script.  Failing to do so will immediately result in
ImportError.

'''

from argparse import ArgumentParser

import numpy
from mayavi import mlab

from plyfile import PlyData


def main():
    parser = ArgumentParser()
    parser.add_argument('ply_filename')

    args = parser.parse_args()

    plot(PlyData.read(args.ply_filename))
    mlab.show()


def plot(ply):
    '''
    Plot vertices and triangles from a PlyData instance. Assumptions:
        `ply' has a 'vertex' element with 'x', 'y', and 'z'
            properties;

        `ply' has a 'face' element with an integral list property
            'vertex_indices', all of whose elements have length 3.

    '''
    vertex = ply['vertex']

    (x, y, z) = (vertex[t] for t in ('x', 'y', 'z'))

    mlab.points3d(x, y, z, color=(1, 1, 1), mode='point')

    if 'face' in ply:
        tri_idx = ply['face']['vertex_indices']
        idx_dtype = tri_idx[0].dtype

        triangles = numpy.fromiter(tri_idx, [('data', idx_dtype, (3,))],
                                   count=len(tri_idx))['data']

        mlab.triangular_mesh(x, y, z, triangles,
                             color=(1, 0, 0.4), opacity=0.5)


main()
