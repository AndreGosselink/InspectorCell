"""
InspectorCell
=============
Provides
  1. Isolated datamodel and widged for use in GUI Apps
  2. Polygon based segmentation of image objects
  3. Clear display of large multiplexed image stacks
  4. Utility scripts for integration in existing workflows

Available subpackages
---------------------
:mod:`viewer`
    Widgeds and Graphic objects for GUI apps
:mod:`entities`
    A central interface for safe data generation and manipulation
:mod:`graphics`
    Primitives and graphical elements used by the viewer
:mod:`graphics`
    Primitives and graphical elements used by the viewer
:mod:`util`
    Utility functions not in the core featureset (e.g. image loading)

Utilities
---------
entitytools
    Script to simplify acces to generated data and feature extraction
"""

from .control import Controller
from .viewer import ViewContext
from .entities import EntityManager

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
