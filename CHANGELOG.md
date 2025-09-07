# Change log

All notable changes to this project will be documented here.

## [Unreleased]
### Changed
- Skip empty header lines to improve interoperability. Thanks to @JTvD
  for the change.

## [1.1.2] - 2025-06-01
### Changed
- Minor metadata updates.

## [1.1.1] - 2025-05-31
### Added
- Official support for Python 3.13.
- Official support for NumPy 2.1 and NumPy 2.2.

### Changed
- Build backend from `pdm-pep517` to `pdm-backend`. Thanks to @bcbnz for
  the fix.

### Fixed
- Integer overflow when reading large files. Thanks to @cdcseacave for
  the fix.

### Removed
- Official support for NumPy < 1.25.

## [1.1] - 2024-08-04
### Added
- Official support for NumPy 2.0.
- Support for write-through memory-mapping. Thanks to @nh2 and
  @chpatrick for the original implementation.

### Fixed
- A small unit test bug.

### Removed
- Official support for Python 3.8.
- Official support for NumPy < 1.21.

## [1.0.3] - 2024-01-06
### Fixed
- Maintainers' documentation for publishing.

## [1.0.2] - 2023-11-13
### Added
- Official support for Python 3.12 and `numpy` 1.26.

## [1.0.1] - 2023-07-23
### Changed
- Minor change to project metadata.

## [1.0] - 2023-07-09
### Added
- PDM user scripts for common development workflow tasks.
- New guides for contributing and maintaining.
- `.readthedocs.yaml` configuration for documentation hosting on
  readthedocs.io.
- Official support for Python 3.11 and `numpy` 1.25.

### Changed
- Major documentation overhaul:
  - documentation moved from `README.md` to `doc/`;
  - Sphinx configuration to render documentation nicely as HTML,
    including API reference via `autodoc`.
- Reordering of code in `plyfile.py`.

### Removed
- `examples/plot.py`, which was a bit out of place.
- Official support for Python 3.7.

## [0.9] - 2023-04-12
### Added
- Support for reading ASCII-format PLY files from text streams.
- Doctest runner in unit test suite.

### Changed
- Docstring formatting style:
  - better PEP-257 compliance;
  - adoption of NumPy docstring style.

### Fixed
- Support for reading Mac-style line endings.

### Removed
- Python2-specific code paths.
- `make2d` function (redundant with `numpy.vstack`).

## [0.8.1] - 2023-03-18
### Changed
- Package metadata management via PDM, rather than `setuptools`.

### Fixed
- Project classifiers array.

## [0.8] - 2023-03-17
### Added
- `known_list_len` optional argument. Thanks to @markbandstra.

### Removed
- Official support for Python<3.7 and `numpy`<1.17.

## [0.7.4] - 2021-05-02
### Fixed
- `DeprecationWarning` fix on `numpy`>=1.19. Thanks to @markbandstra.

## [0.7.3] - 2021-02-06
### Added
- Memory-mapping made optional.
- FAQ section in `README.md`.
- `PlyElement.__len__` and `PlyElement.__contains__`. Thanks to
  @athompson673.

### Changed
- Syntax highlighting in `README.md` improved.

## [0.7.2] - 2020-03-21
### Added
- Long description added to package distribution.

## [0.7.1] - 2019-10-08
### Fixed
- License file included in distribution.

## [0.7] - 2018-12-25
### Added
- Read & write support for file-like objects.

### Fixed
- Documentation improved.

## [0.6] - 2018-07-28
### Changed
- Changed line endings back to Unix-style.

### Fixed
- `make2d` on `numpy`>=1.14.

### Deprecated
- `make2d` function. Please use `numpy.vstack`.

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

[Unreleased]: https://github.com/dranjan/python-plyfile/compare/v1.1.2...HEAD
[1.1]: https://github.com/dranjan/python-plyfile/compare/v1.1.1...v1.1.2
[1.1]: https://github.com/dranjan/python-plyfile/compare/v1.1...v1.1.1
[1.1]: https://github.com/dranjan/python-plyfile/compare/v1.0.3...v1.1
[1.0.3]: https://github.com/dranjan/python-plyfile/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/dranjan/python-plyfile/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/dranjan/python-plyfile/compare/v1.0...v1.0.1
[1.0]: https://github.com/dranjan/python-plyfile/compare/v0.9...v1.0
[0.9]: https://github.com/dranjan/python-plyfile/compare/v0.8.1...v0.9
[0.8.1]: https://github.com/dranjan/python-plyfile/compare/v0.8...v0.8.1
[0.8]: https://github.com/dranjan/python-plyfile/compare/v0.7.4...v0.8
[0.7.4]: https://github.com/dranjan/python-plyfile/compare/v0.7.3...v0.7.4
[0.7.3]: https://github.com/dranjan/python-plyfile/compare/v0.7.2...v0.7.3
[0.7.2]: https://github.com/dranjan/python-plyfile/compare/v0.7.1...v0.7.2
[0.7.1]: https://github.com/dranjan/python-plyfile/compare/v0.7...v0.7.1
[0.7]: https://github.com/dranjan/python-plyfile/compare/v0.6...v0.7
[0.6]: https://github.com/dranjan/python-plyfile/compare/v0.5...v0.6
[0.5]: https://github.com/dranjan/python-plyfile/compare/v0.4...v0.5
[0.4]: https://github.com/dranjan/python-plyfile/compare/v0.3...v0.4
[0.3]: https://github.com/dranjan/python-plyfile/compare/v0.2...v0.3
[0.2]: https://github.com/dranjan/python-plyfile/compare/v0.1...v0.2
