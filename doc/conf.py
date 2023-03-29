import os
import sys

project = 'plyfile'
copyright = '2023, Darsh Ranjan'
author = 'Darsh Ranjan'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'numpydoc',
    'myst_parser',
    'sphinxcontrib.fulltoc',
]
source_suffix = ['.rst', '.md']
templates_path = ['_templates']
html_theme = 'cloud'
html_theme_options = {
    'stickysidebar': True,
    'highlighttoc': True,
}
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    'numpy': ('http://docs.scipy.org/doc/numpy/', None),
}
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"
numpydoc_class_members_toctree = False
default_role = 'py:obj'
