# -*- coding: utf-8 -*-

from pathlib import Path
from distutils.core import setup
import setuptools
import importlib.util


def _import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def get_version():
    _version_path = ''
    mod = _import_file('_version', _version_path)
    return mod.__version__

def get_datafiles():
    # _config_path = None
    # mod = _import_file('_config', _config_path)
    # dir_name = mod.__marker_db_dir
    # return [(dir_name, ['./res/data/abids.csv', './res/data/abids.json'])]
    return []

def get_scripts():
    # script_dir = Path('./res/scripts/')
    # return [str(p) for p in script_dir.glob('*.bat')]
    return []

def get_requires():
    """minimally needed to run
    """
    ret = [
        'Orange3'
    ]
    return ret

def get_entry():
    ret = {
        # Entry point used to specify packages containing widgets.
        'orange.widgets': (
            # Syntax: category name = path.to.package.containing.widgets
            # Widget category specification can be seen in
            #    orangecontrib/example/widgets/__init__.py
            'CellProfiling = Widgets',
        )
    }
    return ret


if __name__ == '__main__':
    setup(
        name='cellinspector',
        version=get_version(),
        packages=[''],
        package_dir={'cellinspector': 'src'},
        description='Analyse Cells in Orange',
        include_package_data=False,
        install_requires=get_requires(),
        # scripts=get_scripts(),
        # packages=setuptools.find_packages(),
        # package_data={'segtool': ['./res/data/*.csv', './res/data/*.json']},
        # data_files=get_datafiles(),
        # license='Creative Commons Attribution-Noncommercial-Share Alike license',
        # long_description='Analyse Cells in Orange',
    )
