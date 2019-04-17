# -*- coding: utf-8 -*-
from pathlib import Path
from distutils.core import setup

def get_version():
    _version_path = Path('./dataframework/_version.py')
    with _version_path.open('r') as ver_file:
        ver_line = ver_file.readlines()[-1]
        ver_line = ver_line.strip()
        __version__ = ver_line.split('=')[-1]
        __version__ = __version__.strip()
        __version__ = __version__.strip('"')
        __version__ = __version__.strip("'")
    return __version__

setup(
    name='DataFramework',
    version=get_version(),
    # packages=['dataframework',], misses the submodules
    packages=setuptools.find_packages(),
    # license='Creative Commons Attribution-Noncommercial-Share Alike license',
    long_description='Tools and utils + marker infromation to access' +\
                     'MICS data in a uniform, consisten fashion',
    include_package_data=True,
    install_requires=[
        'numpy',
        'opencv-python',
        'tinydb',
        'pandas',
        'lxml',
      ],
)
