# Installation

## Dependencies

- python3 >= 3.7
- numpy >= 1.17

(`plyfile` may or may not work on older versions.)

### Optional dependencies

- tox (for test suite)
- pytest (for test suite)

## Installing plyfile

Quick way:

    pip3 install plyfile

Or clone the repository and run from the project root:

    pip3 install .

Or just copy `plyfile.py` into your GPL-compatible project.

## Running test suite

Preferred (more comprehensive; requires tox):

    tox -v --skip-missing-interpreters

Alternate (requires pytest):

    pytest test -v
