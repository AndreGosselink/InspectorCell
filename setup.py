# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

import versioneer

def get_packages():
    try:
        return find_packages('src')
    except NameError:
        import itertools as it
        import os
        packages = ['inspectorcell', 'orangecontrib']
        pathes = [os.path.join('src', pkg) for pkg in packages]
        inits = [list(pth.glob('*/__init__.py')) for pth in pathes]
        for init in it.chain.from_iterable(inits):
            init = init.parent
            subpack = '.'.join(init.parts)
            if subpack not in packages:
                packages.append(subpack)
        return packages

def get_scripts():
    entity_scripts = ['./src/scripts/entitytool.sh',
                      './src/scripts/entitytool.bat',
                      './src/scripts/entitytool.py'
            ]
    return entity_scripts

def get_pkgfiles():
    """Files stored in the package
    """
    ret = {
        'orangecontrib.inspectorcell.widgets': ['icons/*'],
    }
    return ret


def get_requires():
    """minimally needed to run
    """
    base = [
        'pathlib',
        'sortedcontainers',
        'numpy',
        'Orange3',
        'opencv-python',
        'AnyQt',
        'PyQt5',
        'dataclasses',
        'Orange3-ImageAnalytics',
    ]
    return base

def get_extra_requires():
    """some extras, mostly dev related
    """
    extras = {
        'dev': ['versioneer', 'wheel', 'CProfileV', 'pytest', 'pytest-qt'],
        'util': ['pandas', 'openpyxl', 'shapely'],
        'doc': ['sphinx', 'sphinx-automodapi'],
    }
    return extras

def get_entry():
    ret = {
        'orange3.addon': (
            'inspectorcell = orangecontrib.inspectorcell',
        ),

        'orange.widgets': (
            'InspectorCell = orangecontrib.inspectorcell.widgets',
        ),

        'console_scripts': [
            'entitycli=inspectorcell.util.entitycli:main',
        ],
    }
    return ret


def get_keywords():
    ret = (
        'orange3 add-on',
        'microscopy',
        'high-content',
        'image',
        'segmentation',
        'tissue',
        'cell',
        'editor',
    )
    return ret


def main():
    setup(
        name='inspectorcell',
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        packages=find_packages('src'),
        package_dir={
            'orangecontrib': 'src/orangecontrib',
            'inspectorcell': 'src/inspectorcell',
        },
        description='Analyse Cells in Orange',

        package_data=get_pkgfiles(),
        include_package_data=True,

        python_requires='>=3',

        install_requires=get_requires(),
        extras_require=get_extra_requires(),

        keywords=get_keywords(),
        namespace_packages=['orangecontrib'],
        entry_points=get_entry(),
        license='Apache Licence Version 2.0',
    )

if __name__ == '__main__':
    main()
