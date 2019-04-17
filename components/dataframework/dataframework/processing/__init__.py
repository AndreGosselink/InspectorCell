# -*- coding: utf-8 -*-

"""Tools for interacting with information sources somehow bound to some service,
providing information/data. be it tables/dbs with antibody infoe, filesystem
with images and name encoded metadata or ome tiffs
"""

from .tiff import TiffImage
from .ometiff import OMETiff
from .fsparser import FsParser
from .valuemapper import ValueMapper
from .csv2db import generate_abid_db
