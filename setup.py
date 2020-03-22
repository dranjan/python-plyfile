import os

from setuptools import setup

mydir = os.path.dirname(__file__)
if mydir:
    os.chdir(mydir)

with open("README.md", "r") as f:
    long_description = f.read()

version = '0.7.2'
base_url = 'https://github.com/dranjan/python-plyfile'

setup(name='plyfile',
      author='Darsh Ranjan',
      author_email='dranjan@berkeley.edu',
      version=version,
      install_requires=['numpy>=1.8'],
      description='PLY file reader/writer',
      long_description_content_type="text/markdown",
      long_description=long_description,
      url=base_url,
      download_url=('%s/archive/v%s.tar.gz' % (base_url, version)),
      classifiers=[
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Operating System :: OS Independent',
          'Development Status :: 4 - Beta',
          'Topic :: Scientific/Engineering'
      ],
      data_files=[('', ['COPYING'])],
      py_modules=['plyfile'],
      keywords=['ply', 'numpy'])
