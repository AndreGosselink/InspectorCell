# -*- coding: utf-8 -*-
"""Datatools gathering informations about data and metadata from all
avaible services, offering unified access to date among different apps
"""

from ._version import __version__

from .processing import TiffImage, OMETiff
from .container import ImageStack, MapGen, ObjGen, ImgObj
