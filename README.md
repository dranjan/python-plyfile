Welcome to the `plyfile` Python module, which provides a simple facility
for reading and writing ASCII and binary PLY files.

The PLY format is documented
[elsewhere](http://www.cs.virginia.edu/~gfx/Courses/2001/Advanced.spring.01/plylib/Ply.txt).

# Installation

The installation/test shell script `test-all.sh` documents the procedure
for installing `plyfile` and its dependencies in a virtualenv
environment on a Unix-like system.  One option is simply to run the test
script and keep using the virtualenv it creates, or to read the script
and adapt it to your needs.  (You will need `virtualenv` and `pip` to
run `test-all.sh`.)  Or just keep reading:

## Dependency: NumPy

The only dependency is the ubiquitous `numpy`, but you'll need a fairly
recent version.  Version 1.8 is known to be sufficient.  While this is
listed as a dependency in `setup.py`, the automatic installation doesn't
seem to work well, so you may need to install it manually.  But this is
quite easy:

    pip install numpy

(Or just use your package manager's NumPy if it isn't too old.)

## Installing plyfile

    python setup.py install

(Or just copy `plyfile.py` into your project.)

# Usage

The test script `test.py` documents the basic usage.  A more fleshed-out
description is also given here.

The following code examples refer to the file `tet.ply`, which can be
found in the `test` directory.

    >>> from plyfile import PlyData, PlyElement

Both deserialization and serialization of PLY file data is done through
`PlyData` and `PlyElement` instances.

## Reading a PLY file

    >>> plydata = PlyData.read('tet.ply')

or

    >>> plydata = PlyData.read(open('tet.ply'))

The static method `PlyData.read` returns a `PlyData` instance, which is
`plyfile`'s representation of the data in a PLY file.  A `PlyData`
instance has an attribute `elements`, which is a list of `PlyElement`
instances, each of which has a `data` attribute which is a `numpy`
structured array containing the numerical data.  PLY file elements map
onto `numpy` structured arrays in a pretty obvious way.  For a list
property in an element, the corresponding `numpy` field type
is `object`, with the members being `numpy` arrays (see the
`vertex_indices` example below).

Concretely:

    >>> plydata.elements[0].name
    'vertex'
    >>> plydata.elements[0].data[0]
    (0.0, 0.0, 0.0)
    >>> plydata.elements[0].data['x']
    array([ 0.,  0.,  1.,  1.], dtype=float32)
    >>> plydata['face'].data['vertex_indices'][0]
    array([0, 1, 2], dtype=int32)

For convenience, elements can be looked up by name:

    >>> plydata['vertex'].data['x']
    array([ 0.,  0.,  1.,  1.], dtype=float32)

`PlyElement` instances also contain metadata:

    >>> plydata.elements[0].properties
    [PlyProperty('x', 'float32'), PlyProperty('y', 'float32'),
     PlyProperty('z', 'float32')]
    >>> plydata.elements[0].count
    4

`PlyProperty` and `PlyListProperty` instances are used internally as a
convenient intermediate representation of PLY element properties that
can easily be serialized to a PLY header (using `str`) or converted to
`numpy`-compatible type descriptions (via the `dtype` method).

In theory, the `properties` attribute of a `PlyElement` instance could
be manipulated before serializing the data to perform some types of
coercions, but this isn't well tested or documented.

## Creating a PLY file

The first step is to get your data into `numpy` structured arrays.  Note
that there are some restrictions: generally speaking, if you know the
types of properties a PLY file element can contain, you can easily
deduce the restrictions.  For example, PLY files don't contain 64-bit
integer or complex data, so these aren't allowed.

For convenience, non-scalar fields **are** allowed; they will be
serialized as list properties.  For example, when constructing a "face"
element, if all the faces are triangles (a common occurrence), it's okay
to have a  "vertex_indices" field of type `'i4'` and shape `(3,)`
instead of type `object` and shape `()`.  However, if the serialized PLY
file is read back in using `plyfile`, the "vertex_indices" property will
be represented as an `object`-typed field, each of whose values is an
array of type `'i4'` and length 3.  The reason is simply that the PLY
format provides no way to find out that each "vertex_indices" field has
length 3 without actually reading all the data, so `plyfile` has to
assume that this is a variable-length property.

For example, if we wanted to create the "vertex" and "face" PLY elements
of the `tet.ply` data directly as `numpy` arrays for the purpose of
serialization, we could do (as in `test/test.py`):

    >>> vertex = numpy.array([(0, 0, 0),
    ...                       (0, 1, 1),
    ...                       (1, 0, 1),
    ...                       (1, 1, 0)],
    ...                      dtype=[('x', 'f4'), ('y', 'f4'),
    ...                             ('z', 'f4')])
    >>> face = numpy.array([([0, 1, 2], 255, 255, 255),
    ...                     ([0, 2, 3], 255,   0,   0),
    ...                     ([0, 1, 3],   0, 255,   0),
    ...                     ([1, 2, 3],   0,   0, 255)],
    ...                    dtype=[('vertex_indices', 'i4', (3,)),
    ...                           ('red', 'u1'), ('green', 'u1'),
    ...                           ('blue', 'u1')])

Once you have suitably structured array, the static method
`PlyElement.describe` can then be used to create the necessary
`PlyElement` instances:

    >>> el = PlyElement.describe('some_name', some_array)

or

    >>> el = PlyElement.describe('some_name', some_array,
    ...                          comments=['comment1',
    ...                                    'comment2'])

Note that there's no need to create `PlyProperty` instances explicitly.
This is all done behind the scenes by examining `some_array.dtype.descr`.
One slight hiccup here is that variable-length fields in a `numpy` array
(i.e., our representation of PLY list properties)
must have a type of `object`, so the types of the list length and values
in the serialized PLY file can't be obtained from the array's `dtype`
attribute alone.  For simplicity and predictability, the length
defaults to 8-bit unsigned integer, and the value defaults to 32-bit
signed integer, which covers the majority of use cases.  Exceptions must
be stated explicitly:

    >>> el = PlyElement.describe('some_name', some_array,
    ...                          val_dtypes={'some_property': 'f8'},
    ...                          len_dtypes={'some_property': 'u4'})

Now you can instantiate `PlyData` and serialize:

    >>> PlyData([el]).write('some_binary.ply')
    >>> PlyData([el], text=True).write('some_ascii.ply')
    >>> PlyData([el],
    ...         byte_order='>').write('some_big_endian_binary.ply')

In the last example, the byte order of the output was forced to
big-endian, independently of the machine's native byte order.

Comments can be added:

    >>> PlyData([el], comments=['header comment']).write('some.ply')

# Design philosophy and rationale

At the time that I wrote this, I didn't know of any simple and
self-contained Python PLY file module using `numpy` as its data
representation medium.  Considering the increasing prevalance of Python
as a tool for scientific programming with NumPy as the _lingua franca_
for numerical data, such a module seemed desirable; hence, `plyfile` was
born.

## Familiarity

I opted to use existing Python and NumPy constructs whenever they
matched the data.  Thus, the `elements` attribute of a `PlyData`
instance is simply a `list` of `PlyElement` instances, and the `data`
attribute of a `PlyElement` instance is a `numpy` array, and a list
property field of a PLY element datum is referred to in the `data`
attribute by a type of `object` with the value being another `numpy`
array, etc.  In the last case, this is certainly not the most-efficient
in-memory representation of the data, since it contains a lot of
indirection.  However, it is arguably the most obvious and natural
unless NumPy adds explicit support for "ragged" arrays in its type
system.  The design goal was to represent data in a form familiar to
users of `numpy`.

## Simplicity

When the two were at odds, I decided to favor simplicity over power or
user-friendliness.  Thus, list property types in `PlyElement.describe`
always default to the same, rather than, say, being obtained by looking
at an array element.  (Which element?  What if the array has length
zero?  Whatever default we could choose in that case could lead to
subtle edge-case bugs if the user isn't vigilant.)  Also, all input and
output is done in "one shot": all the arrays must be created up front
rather than being processed in a streaming fashion.  (That said, I have
nothing against streamability, and I considered it at one point.  I
decided against it for now in order to have a consistent and
maintainable interface at least for the first usable version.)

## Interpretation issues

There doesn't seem to be a single complete and consistent description of
the PLY format.  Even the "authoritative" 
[Ply.txt](http://www.cs.virginia.edu/~gfx/Courses/2001/Advanced.spring.01/plylib/Ply.txt)
by Greg Turk is incomplete and inconsistent.  For example,
where can comments appear in the header?  At least one popular reader of
PLY files chokes on comments before the "format" line.  `plyfile`
accepts comments anywhere in the header in input but only places them in
a few limited places in output, namely immediately after "format" and
"element" lines.  It appears that in all the "official" examples, all
comments immediately follow the "format" line, but the language of the
specification neither places any such restrictions nor explicitly allows
comments to be placed anywhere else.

Another ambiguity is names: what strings are allowed as PLY element and
property names?  `plyfile` accepts as input any name that doesn't
contain spaces, but this is surely too generous.  This may not be such
a big deal, though: although names are theoretically arbitrary, in
practice, the majority of PLY element and property names probably come
from a small finite set ("face", "x", "nx", "green", etc.).

A more serious problem is that the PLY format specification appears to
be inconsistent regarding the syntax of property definitions.  In
some examples, it uses the syntax

    property {type} {name}

and in others,

    property {name} {type}

`plyfile` only supports the former, which appears to be standard _de
facto_.

# Deficiencies

## Validation

Although some validation is done, malformed data may silently give
strange results instead of raising errors.  It would be better if
`plyfile` completely validated that input satisfied the PLY
specification (modulo the ambiguities mentioned above).  Also, `plyfile`
can silently write invalid PLY files for some badly formed input, for
example, if element or property names contain spaces or newlines.  This
is really a bug.

## Error messages

Error messages aren't necessarily as helpful as they could be, although
we do make an attempt at describing the nature of errors encountered.
In many cases, exceptions raised from `numpy` routines will simply
propagate through `plyfile`, and the user will have the task of hunting
down the real errors.  This is arguably a bug.

# Credits

Author: Darsh Ranjan

# License

This software is released under the terms of the GNU General Public
License, version 3.  See the file `COPYING` for details.
