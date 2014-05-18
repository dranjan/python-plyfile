#!/usr/bin/env bash

set -e
set -o pipefail

mydir=$(dirname $(readlink -f $0))
pushd "$mydir" > /dev/null

echo "Creating virtualenv..."
virtualenv plyfile-venv

source plyfile-venv/bin/activate

# Apparently setuptools' automatic dependency handling is broken?
echo "installing numpy..."
pip install numpy

echo "installing plyfile..."
python setup.py install

echo "running test..."
pushd test > /dev/null
python test.py
popd > /dev/null

deactivate
popd > /dev/null

echo
echo "All OK!"
echo "plyfile and numpy are installed in a virtualenv environment:"
echo "   $(readlink -f plyfile-venv)"
echo "which you can safely delete or keep using."
