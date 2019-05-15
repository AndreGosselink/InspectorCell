# -*- coding: utf-8 -*-

from pathlib import Path
from setuptools import setup, find_packages
import importlib.util


def _import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def get_pack():
    return find_packages('src')

def get_version():
    # _version_path = ''
    # mod = _import_file('_version', _version_path)
    # return mod.__version__
    return '1.0'

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

def get_pkgfiles():
    """Files stored in the package
    """
    ret = {
    'orangecontrib.example': ['tutorials/*.ows'],
    'orangecontrib.example.widgets': ['icons/*'],
    'orangecontrib.cellinspector.widgets': ['icons/*'],
    }
    return ret

def get_requires():
    """minimally needed to run
    """
    ret = [
        'Orange3'
    ]
    return ret

def get_entry():
    ret = {
        # Entry points that marks this package as an orange add-on. If set, addon will
        # be shown in the add-ons manager even if not published on PyPi.
        'orange3.addon': (
            'cellinspector = orangecontrib.cellinspector',
            'example = orangecontrib.example',
        ),
        # # Entry point used to specify packages containing tutorials accessible
        # # from welcome screen. Tutorials are saved Orange Workflows (.ows files).
        # 'orange.widgets.tutorials': (
        #     # Syntax: any_text = path.to.package.containing.tutorials
        #     'exampletutorials = orangecontrib.example.tutorials',
        # ),

        # Entry point used to specify packages containing widgets.
        'orange.widgets': (
            # Syntax: category name = path.to.package.containing.widgets
            # Widget category specification can be seen in
            #    orangecontrib/example/widgets/__init__.py
            'CellInspector = orangecontrib.cellinspector.widgets',
            'Examples = orangecontrib.example.widgets',
        ),

        # # Register widget help
        # "orange.canvas.help": (
        #     'html-index = orangecontrib.example.widgets:WIDGET_HELP_PATH',)
    }
    return ret

def get_keywords():
    ret = (
        'orange3 add-on',
        'microscopy',
        'high-content',
        'image',
        'segmentation',
        'cellmodel',
        'editor',
    )
    return ret


if __name__ == '__main__':
    setup(
        name='cellinspector',
        version='0.0',
        # packages=find_packages('src'),
        packages=get_pack(),
        package_dir={
            '': 'src',
            # 'orangecontrib': 'src/orangecontrib',
            # 'cellinspector': 'src/cellinspector',
        },
        description='Analyse Cells in Orange',

        package_data=get_pkgfiles(),
        include_package_data=True,

        install_requires=get_requires(),

        keywords=get_keywords(),
        namespace_packages=['orangecontrib'],
        entry_points=get_entry(),
        # scripts=get_scripts(),
        # packages=setuptools.find_packages(),
        # package_data={'segtool': ['./res/data/*.csv', './res/data/*.json']},
        # data_files=get_datafiles(),
        # license='Creative Commons Attribution-Noncommercial-Share Alike license',
        # long_description='Analyse Cells in Orange',
    )
