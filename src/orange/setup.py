import sys
from setuptools import setup, find_packages

NAME = "CellProfiling"

VERSION = "0.0.3"

DESCRIPTION = "Add-on containing cell profiling widgets"

PACKAGES = find_packages()
PACKAGE_DATA = {}

INSTALL_REQUIRES = [
    'Orange3',
]

ENTRY_POINTS = {
    'orange3.addon': (
        'cellprofiling = orangecontrib.cellprofiling'
    ),
    'orange.widgets': (
        'CellProfiling = orangecontrib.cellprofiling.widgets'
    ),
}

NAMESPACE_PACKAGES = ["orangecontrib"]

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