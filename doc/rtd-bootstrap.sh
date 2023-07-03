#!/usr/bin/env bash
#
# This script is used specifically in the Read the Docs build to
# bootstrap the environment needed to generate the documentation (see
# .readthedocs.yaml at the top level). A normal user should not need to
# run this script except literally to test the logic below.

set -euxo pipefail

mkdir -p build/
curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/2.7.4/install-pdm.py > build/install-pdm.py
mkdir -p build/root/
python build/install-pdm.py --path build/root -v 2.7.4
build/root/bin/pdm install -dG doc
