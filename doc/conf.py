import os
import sys

sys.path.insert(0, os.path.abspath('.'))

project = 'plyfile'
copyright = '2023, Darsh Ranjan'
author = 'Darsh Ranjan'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'numpydoc']
templates_path = ['_templates']
exclude_patterns = ['build', 'test', '.tox']
html_theme = 'cloud'
html_theme_options = {
    'stickysidebar': True,
    'highlighttoc': True,
}
#import solar_theme
#html_theme_path = [solar_theme.theme_path]
html_static_path = ['build/static']
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    'numpy': ('http://docs.scipy.org/doc/numpy/', None),
}
autodoc_class_signature = "separated"
