# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import versioneer

def get_pack():
    return find_packages('src')

def get_datafiles():
    # _config_path = None
    # mod = _import_file('_config', _config_path)
    # dir_name = mod.__marker_db_dir
    # return [(dir_name, ['./res/data/abids.csv', './res/data/abids.json'])]
    return []


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
        # Entry points that marks this package as an orange add-on. If set, addon will
        # be shown in the add-ons manager even if not published on PyPi.
        'orange3.addon': (
            'inspectorcell = orangecontrib.inspectorcell',
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
            'InspectorCell = orangecontrib.inspectorcell.widgets',
        ),

        # # Register widget help
        # "orange.canvas.help": (
        #     'html-index = orangecontrib.example.widgets:WIDGET_HELP_PATH',)

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
        # packages=find_packages('src'),
        packages=find_packages('src'),
        package_dir={
            # '': 'src',
            'orangecontrib': 'src/orangecontrib',
            # might be a nameclash
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
        # scripts=get_scripts(),
        # packages=setuptools.find_packages(),
        # package_data={'segtool': ['./res/data/*.csv', './res/data/*.json']},
        # data_files=get_datafiles(),
        # license='Creative Commons Attribution-Noncommercial-Share Alike license',
        # long_description='Analyse Cells in Orange',
    )

if __name__ == '__main__':
    main()
