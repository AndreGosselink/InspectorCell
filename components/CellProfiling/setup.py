import sys
from setuptools import setup, find_packages

NAME = "CellProfiling"

VERSION = "0.0.2"

DESCRIPTION = "Add-on containing cell profiling widgets"

from setuptools import setup

PACKAGES = ["Widgets"]

PACKAGE_DATA = {
    'Widgets': ['icons/*'],
}

INSTALL_REQUIRES = [
    'Orange3',
]

ENTRY_POINTS = {

    # Entry point used to specify packages containing widgets.
    'orange.widgets': (
        # Syntax: category name = path.to.package.containing.widgets
        # Widget category specification can be seen in
        #    orangecontrib/example/widgets/__init__.py
        'CellProfiling = Widgets',
    )
}

if __name__ == '__main__':
    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        packages=PACKAGES,
        package_data=PACKAGE_DATA,
        install_requires=INSTALL_REQUIRES,
        entry_points=ENTRY_POINTS,
        include_package_data=True,
        zip_safe=False,
    )