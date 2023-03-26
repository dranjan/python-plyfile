# Design philosophy and rationale

The design philosophy of `plyfile` can be summed up as follows.
- Be familiar to users of `numpy` and reuse existing idioms and concepts
  when possible.
- Favor simplicity over power or user-friendliness.
- Support all valid PLY files.

## Familiarity

For the most part, PLY concepts map nicely to Python and specifically to
`numpy`, and leveraging that has strongly influenced the design of this
package.  The `elements` attribute of a `PlyData` instance is simply a
`list` of `PlyElement` instances, and the `data` attribute of a
`PlyElement` instance is a `numpy` array, and a list property field of a
PLY element datum is referred to in the `data` attribute by a type of
`object` with the value being another `numpy` array, etc.

## Simplicity

When applicable, we favor simplicity over power or user-friendliness.
Thus, list property types in `PlyElement.describe` always default to the
same, rather than, say, being obtained by looking at an array element.
(Which element?  What if the array has length zero?  Whatever default we
could choose in that case could lead to subtle edge-case bugs if the
user isn't vigilant.)  Also, all input and output is done in "one shot":
all the arrays must be created up front rather than being processed in a
streaming fashion.

## Generality and interpretation issues

We aim to support all valid PLY files. However, exactly what constitutes
a "valid" file isn't obvious, since there doesn't seem to be a single
complete and consistent description of the PLY format.  Even the
"authoritative"
[Ply.txt](https://web.archive.org/web/20161221115231/http://www.cs.virginia.edu/~gfx/Courses/2001/Advanced.spring.01/plylib/Ply.txt)
by Greg Turk has some issues.

### Comment placement

Where can comments appear in the header?  It appears that in all the
"official" examples, all comments immediately follow the "format" line,
but the language of the document neither places any such restrictions
nor explicitly allows comments to be placed anywhere else.  Thus, it
isn't clear whether comments can appear anywhere in the header or must
immediately follow the "format" line.  At least one popular reader of
PLY files chokes on comments before the "format" line.  `plyfile`
accepts comments anywhere in the header in input but only places them in
a few limited places in output, namely immediately after "format" and
"element" lines.

### Element and property names

Another ambiguity is names: what strings are allowed as PLY element and
property names?  `plyfile` accepts as input any name that doesn't
contain spaces, but this is surely too generous.  This may not be such
a big deal, though: although names are theoretically arbitrary, in
practice, the majority of PLY element and property names probably come
from a small finite set ("face", "x", "nx", "green", etc.).

### Property syntax

A more serious problem is that the PLY format specification appears to
be inconsistent regarding the syntax of property definitions.  In
some examples, it uses the syntax

    property {type} {name}

and in others,

    property {name} {type}

`plyfile` only supports the former, which appears to be standard _de
facto_.

### Header line endings

The specification explicitly states that lines in the header must
end with carriage returns, but this rule doesn't seem to be followed by
anyone, including the C-language PLY implementation by Greg Turk, the
author of the format.  Here, we stick to common practice and output
Unix-style line endings (with no carriage returns) but accept any line
ending style in input files.
