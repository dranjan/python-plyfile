# Change log

All notable changes to this project will be documented here.

## [Unreleased]
### Changed
- Changed line endings back to Unix-style.

## [0.5] - 2017-02-27
### Added
- Project metadata suitable for PyPI.
- More unit tests.
- Official support for NumPy 1.10 and 1.11.
- Automatic unit test coverage reporting through test runner.
- CHANGELOG.md.
- Comment validation and preservation of leading spaces.  Thanks to
  @Zac-HD for the bug report.
- Better validation of element and property names.

### Changed
- Made "private" variables explicitly so.
- Used memory mapping for "simple" PLY elements.  Thanks to @Zac-HD for
  the original pull request.
- (Under the hood) Rewrote header parser.

### Removed
- Official support for Python 2.6.

### Fixed
- Fixed reading and writing through unicode filenames.
- Fixed documentation bugs.  Thanks to @jeremyherbert.

## [0.4] - 2015-04-05
### Added
- `PlyParseError` for parsing errors.
- Explicit (limited) mutability of PLY metadata.
- Better validation when modifying PLY metadata.
- More unit tests.

### Removed
- Ability to change element and property names by mutation, which was
  never handled correctly anyway.

## [0.3] - 2015-03-28
### Added
- `__getitem__` and `__setitem__` for `PlyElement`.
- Support for `obj_info` comments.
- `make2d` utility function.

### Changed
- Ported test setup to `py.test` and `tox`.
- Changed output property names to those in original specification.

## [0.2] - 2014-11-09
### Added
- GPLv3 license.
- Documentation.
- Example plotting script.
- Python 3 compatibility.  Thanks to @svenpilz for most of the bug fixes.

### Fixed
- Changed line endings to be compliant with specification.
- Improved validation of property and element names.

## 0.1 - 2014-05-17
### Added
- plyfile.py: PLY format I/O.
- Rudimentary test setup.
- Basic installation script.

[Unreleased]: https://github.com/dranjan/python-plyfile/compare/v0.5...HEAD
[0.5]: https://github.com/dranjan/python-plyfile/compare/v0.4...v0.5
[0.4]: https://github.com/dranjan/python-plyfile/compare/v0.3...v0.4
[0.3]: https://github.com/dranjan/python-plyfile/compare/v0.2...v0.3
[0.2]: https://github.com/dranjan/python-plyfile/compare/v0.1...v0.2
