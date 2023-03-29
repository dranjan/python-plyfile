import os
import sys

project = 'plyfile'
copyright = '2014-2023, Darsh Ranjan and plyfile authors'
author = 'Darsh Ranjan'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'numpydoc',
    'myst_parser',
]
source_suffix = ['.rst', '.md']
templates_path = ['_templates']
html_theme = 'sphinx_rtd_theme'
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    'numpy': ('http://docs.scipy.org/doc/numpy/', None),
}
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"
numpydoc_class_members_toctree = False
default_role = 'py:obj'
