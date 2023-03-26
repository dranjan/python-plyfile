#!/usr/bin/env bash

set -euxo pipefail

export PYTHONPATH=..
sphinx-build . build -b html
