# Usage

Both deserialization and serialization of PLY file data is done through
`PlyData` and `PlyElement` instances.

```Python Console
>>> import numpy
>>> from plyfile import PlyData, PlyElement
>>>
```

For the code examples that follow, assume the file `tet.ply` contains
the following text:

    ply
    format ascii 1.0
    comment single tetrahedron with colored faces
    element vertex 4
    comment tetrahedron vertices
    property float x
    property float y
    property float z
    element face 4
    property list uchar int vertex_indices
    property uchar red
    property uchar green
    property uchar blue
    end_header
    0 0 0
    0 1 1
    1 0 1
    1 1 0
    3 0 1 2 255 255 255
    3 0 2 3 255 0 0
    3 0 1 3 0 255 0
    3 1 2 3 0 0 255

(This file is available under the `examples` directory.)

## Reading a PLY file

```Python Console
>>> plydata = PlyData.read('tet.ply')
>>>
```

or

```Python Console
>>> with open('tet.ply', 'rb') as f:
...     plydata = PlyData.read(f)
>>>
```

The static method `PlyData.read` returns a `PlyData` instance, which is
`plyfile`'s representation of the data in a PLY file.  A `PlyData`
instance has an attribute `elements`, which is a list of `PlyElement`
instances, each of which has a `data` attribute which is a `numpy`
structured array containing the numerical data.  PLY file elements map
onto `numpy` structured arrays in a pretty obvious way.  For a list
property in an element, by default, the corresponding `numpy` field type
is `object`, with the members being `numpy` arrays (see the
`vertex_indices` example below).[^list_property_note]

[^list_property_note]: Also see the
[section on `known_list_len`](#known_list_len).

Concretely:

```Python Console
>>> plydata.elements[0].name
'vertex'
>>> plydata.elements[0].data[0].tolist()
(0.0, 0.0, 0.0)
>>> plydata.elements[0].data['x']
array([0., 0., 1., 1.], dtype=float32)
>>> plydata['face'].data['vertex_indices'][0]
array([0, 1, 2], dtype=int32)
>>>
```

For convenience, elements and properties can be looked up by name:

```Python Console
>>> plydata['vertex']['x']
array([0., 0., 1., 1.], dtype=float32)
>>>
```

and elements can be indexed directly without explicitly going through
the `data` attribute:

```Python Console
>>> plydata['vertex'][0].tolist()
(0.0, 0.0, 0.0)
>>>
```

The above expression is equivalent to `plydata['vertex'].data[0]`.

`PlyElement` instances also contain metadata:

```Python Console
>>> plydata.elements[0].properties
(PlyProperty('x', 'float'), PlyProperty('y', 'float'), PlyProperty('z', 'float'))
>>> plydata.elements[0].count
4
>>>
```

`PlyProperty` and `PlyListProperty` instances are used internally as a
convenient intermediate representation of PLY element properties that
can easily be serialized to a PLY header (using `str`) or converted to
`numpy`-compatible type descriptions (via the `dtype` method).  It's not
extremely common to manipulate them directly, but if needed, the
property metadata of an element can be accessed as a tuple via the
`properties` attribute (as illustrated above) or looked up by name:

```Python Console
>>> plydata.elements[0].ply_property('x')
PlyProperty('x', 'float')
>>>
```

Many (but not necessarily all) types of malformed input files will raise
`PlyParseError` when `PlyData.read` is called.  The string value of the
`PlyParseError` instance (as well as attributes `element`, `row`, and
`prop`) provides additional context for the error if applicable.

### Faster reading via memory mapping

To accelerate parsing of binary data, `plyfile` can make use of
`numpy`'s memory mapping facilities. The decision to memory map or not
is made on a per-element basis. To make this determination, there are
two cases to consider.

#### Case 1: elements with no list properties

If an element in a binary PLY file has no list properties, then it will
be memory-mapped by default, subject to the capabilities of the
underlying file object.
- Memory mapping can be disabled or fine-tuned using the `mmap` argument
  of `PlyData.read`.
- To confirm whether a given element has been memory-mapped or not,
  check the type of `element.data`.

This is all illustrated below:

```Python Console
>>> plydata.text = False
>>> plydata.byte_order = '<'
>>> plydata.write('tet_binary.ply')
>>>
>>> # Memory-mapping is enabled by default.
>>> plydata = PlyData.read('tet_binary.ply')
>>> isinstance(plydata['vertex'].data, numpy.memmap)
True
>>> # Any falsy value disables memory-mapping here.
>>> plydata = PlyData.read('tet_binary.ply', mmap=False)
>>> isinstance(plydata['vertex'].data, numpy.memmap)
False
>>> # Strings can also be given to fine-tune memory-mapping.
>>> # For example, with 'r+', changes can be written back to the file.
>>> # In this case, the file must be explicitly opened with read-write
>>> # access.
>>> with open('tet_binary.ply', 'r+b') as f:
...     plydata = PlyData.read(f, mmap='r+')
>>> isinstance(plydata['vertex'].data, numpy.memmap)
True
>>> plydata['vertex']['x'] = 100
>>> plydata['vertex'].data.flush()
>>> plydata = PlyData.read('tet_binary.ply')
>>> all(plydata['vertex']['x'] == 100)
True
>>>
```

(known_list_len)=
#### Case 2: elements with list properties

In the general case, elements with list properties cannot be
memory-mapped as `numpy` arrays, except in one important case: when
all list properties have fixed and known lengths. In that case, the
`known_list_len` argument can be given to `PlyData.read`:

```Python Console
>>> plydata = PlyData.read('tet_binary.ply',
...                        known_list_len={'face': {'vertex_indices': 3}})
>>> isinstance(plydata['face'].data, numpy.memmap)
True
>>>
```

The implementation will validate the data: if any instance of the list
property has a length other than the value specified, then
`PlyParseError` will be raised.

Note that in order to enable memory mapping for a given element,
*all* list properties in the element must have their lengths in the
`known_list_len` dictionary. If any list property does not have its
length given in `known_list_len`, then memory mapping will not be
attempted, and no error will be raised.

## Creating a PLY file

The first step is to get your data into `numpy` structured arrays.  Note
that there are some restrictions: generally speaking, if you know the
types of properties a PLY file element can contain, you can easily
deduce the restrictions.  For example, PLY files don't contain 64-bit
integer or complex data, so these aren't allowed.

For convenience, non-scalar fields **are** allowed, and they will be
serialized as list properties.  For example, when constructing a "face"
element, if all the faces are triangles (a common occurrence), it's okay
to have a  "vertex_indices" field of type `'i4'` and shape `(3,)`
instead of type `object` and shape `()`.  However, if the serialized PLY
file is read back in using `plyfile`, the "vertex_indices" property will
be represented as an `object`-typed field, each of whose values is an
array of type `'i4'` and length 3. The reason is simply that the PLY
format provides no way to find out that each "vertex_indices" field has
length 3 without actually reading all the data, so `plyfile` has to
assume that this is a variable-length property.  However, see the
[FAQ](#faq-list-from-2d) for an easy way to recover a two-dimensional
array from a list property, and also see the [notes above](#known_list_len)
about the `known_list_len` parameter to speed up the reading of files with
lists of fixed, known length.

For example, if we wanted to create the "vertex" and "face" PLY elements
of the `tet.ply` data directly as `numpy` arrays for the purpose of
serialization, we could do this:

```Python Console
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
>>>
```

Once you have suitably structured array, the static method
`PlyElement.describe` can then be used to create the necessary
`PlyElement` instances:

```Python Console
>>> el = PlyElement.describe(vertex, 'vertex')
>>>
```

or

```Python Console
>>> el = PlyElement.describe(vertex, 'vertex',
...                          comments=['comment1',
...                                    'comment2'])
>>>
```

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

```Python Console
>>> el = PlyElement.describe(face, 'face',
...                          val_types={'vertex_indices': 'u2'},
...                          len_types={'vertex_indices': 'u4'})
>>>
```

Now you can instantiate `PlyData` and serialize:

```Python Console
>>> PlyData([el]).write('some_binary.ply')
>>> PlyData([el], text=True).write('some_ascii.ply')
>>>
>>> # Force the byte order of the output to big-endian, independently of
>>> # the machine's native byte order
>>> PlyData([el],
...         byte_order='>').write('some_big_endian_binary.ply')
>>>
>>> # Use a file object. Binary mode is used here, which will cause
>>> # Unix-style line endings to be written on all systems.
>>> with open('some_ascii.ply', mode='wb') as f:
...     PlyData([el], text=True).write(f)
>>>
```

## Miscellaneous

### Comments

Header comments are supported:

```Python Console
>>> ply = PlyData([el], comments=['header comment'])
>>> ply.comments
['header comment']
>>>
```

`obj_info` comments are supported as well:

```Python Console
>>> ply = PlyData([el], obj_info=['obj_info1', 'obj_info2'])
>>> ply.obj_info
['obj_info1', 'obj_info2']
>>>
```

When written, they will be placed after regular comments after the
"format" line.

Comments can have leading whitespace, but trailing whitespace may be
stripped and should not be relied upon.  Comments may not contain
embedded newlines.

### Getting a two-dimensional array from a list property

The PLY format provides no way to assert that all the data for a given
list property is of the same length, yet this is a relatively common
occurrence.  For example, all the "vertex_indices" data on a "face"
element will have length three for a triangular mesh.  In such cases,
it's usually much more convenient to have the data in a two-dimensional
array, as opposed to a one-dimensional array of type `object`.  Here's a
pretty easy way to obtain a two dimensional array:

```Python Console
>>> plydata = PlyData.read('tet.ply')
>>> tri_data = plydata['face'].data['vertex_indices']
>>> triangles = numpy.vstack(tri_data)
>>>
```

(If the row lengths of all list properties are known in advance, the
[`known_list_len` parameter](#known_list_len) can also be used.)

### Instance mutability

A plausible code pattern is to read a PLY file into a `PlyData`
instance, perform some operations on it, possibly modifying data and
metadata in place, and write the result to a new file.  This pattern is
partially supported. The following in-place mutations are possible:

- Modifying numerical array data only.
- Assigning directly to a `PlyData` instance's `elements`.
- Switching format by changing the `text` and `byte_order` attributes of
  a `PlyData` instance.   This will switch between `ascii`,
  `binary_little_endian`, and `binary_big_endian` PLY formats.
- Modifying a `PlyData` instance's `comments` and `obj_info`, and
  modifying a `PlyElement` instance's `comments`.
- Assigning to an element's `data`.  Note that the property metadata in
  `properties` is not touched by this, so for every property in the
  `properties` list of the `PlyElement` instance, the `data` array must
  have a field with the same name (but possibly different type, and
  possibly in different order).  The array can have additional fields as
  well, but they won't be output when writing the element to a PLY file.
  The properties in the output file will appear as they are in the
  `properties` list.  If an array field has a different type than the
  corresponding `PlyProperty` instance, then it will be cast when
  writing.
- Assigning directly to an element's `properties`.  Note that the
  `data` array is not touched, and the previous note regarding the
  relationship between `properties` and `data` still applies: the field
  names of `data` must be a superset of the property names in
  `properties`, but they can be in a different order and specify
  different types.
- Changing a `PlyProperty` or `PlyListProperty` instance's `val_dtype`
  or a `PlyListProperty` instance's `len_dtype`, which will perform
  casting when writing.

Modifying the `name` of a `PlyElement`, `PlyProperty`, or
`PlyListProperty` instance is not supported and will raise an error.  To
rename a property of a `PlyElement` instance, you can remove the
property from `properties`, rename the field in `data`, and re-add the
property to `properties` with the new name by creating a new
`PlyProperty` or `PlyListProperty` instance:

```Python Console
>>> from plyfile import PlyProperty, PlyListProperty
>>> face = plydata['face']
>>> face.properties = ()
>>> face.data.dtype.names = ['idx', 'r', 'g', 'b']
>>> face.properties = (PlyListProperty('idx', 'uchar', 'int'),
...                    PlyProperty('r', 'uchar'),
...                    PlyProperty('g', 'uchar'),
...                    PlyProperty('b', 'uchar'))
>>>
```

Note that it is always safe to create a new `PlyElement` or `PlyData`
instance instead of modifying one in place, and this is the recommended
style:

```Python Console
>>> # Recommended:
>>> plydata = PlyData([plydata['face'], plydata['vertex']],
...                   text=False, byte_order='<')
>>>
>>> # Also supported:
>>> plydata.elements = [plydata['face'], plydata['vertex']]
>>> plydata.text = False
>>> plydata.byte_order = '<'
>>> plydata.comments = []
>>> plydata.obj_info = []
>>>
```

Objects created by this library don't claim ownership of the other
objects they refer to, which has implications for both styles (creating
new instances and modifying in place).  For example, a single
`PlyElement` instance can be contained by multiple `PlyData` instances,
but modifying that instance will then affect all of those containing
`PlyData` instances.

### Text-mode streams

Input and output on text-mode streams is supported for ASCII-format
PLY files, but not binary-format PLY files. Input and output on
binary streams is supported for all valid PLY files. Note that
`sys.stdout` and `sys.stdin` are text streams, so they can only be
used directly for ASCII-format PLY files.
