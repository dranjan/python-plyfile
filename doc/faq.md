# FAQ

(faq-list-from-2d)=
## How do I initialize a list property from a two-dimensional array?

```Python Console
>>> from plyfile import PlyElement
>>> import numpy
>>>
>>> # Here's a two-dimensional array containing vertex indices.
>>> face_data = numpy.array([[0, 1, 2], [3, 4, 5]], dtype='i4')
>>>
>>> # PlyElement.describe requires a one-dimensional structured array.
>>> ply_faces = numpy.empty(len(face_data),
...                         dtype=[('vertex_indices', 'i4', (3,))])
>>> ply_faces['vertex_indices'] = face_data
>>> face = PlyElement.describe(ply_faces, 'face')
>>>
```

## Can I save a PLY file directly to `sys.stdout`?

Yes, for an ASCII-format PLY file. For binary-format files, it won't
work directly, since `sys.stdout` is a text-mode stream and binary-format
files can only be output to binary streams. (ASCII-format files can be
output to text or binary streams.)

There are a few ways around this.
- Write to a named file instead. On Linux and some other Unix-likes, you
  can access `stdout` via the named file `/dev/stdout`:

    ```Python Console
    >>> plydata.write('/dev/stdout')  # doctest: +SKIP
    ```

- Use `sys.stdout.buffer`:

    ```Python Console
    >>> plydata.write(sys.stdout.buffer)  # doctest: +SKIP
    ```

## Can I read a PLY file from `sys.stdin`?

The answer is exactly analogous to the situation with writing to
`sys.stdout`: it works for ASCII-format PLY files but not binary-format
files. The two workarounds given above also apply: use a named file like
`/dev/stdin`, or use `sys.stdin.buffer`.
