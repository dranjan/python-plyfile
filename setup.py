import os

from setuptools import setup

mydir = os.path.dirname(__file__)
if mydir:
    os.chdir(mydir)

setup(name = 'plyfile',
      version = '0.2',
      install_requires = ['numpy>=1.8'],
      description = 'PLY file reader/writer',
      py_modules = ['plyfile'])
