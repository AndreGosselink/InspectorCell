"""Testing monkey patching of viewbox to implement global scop items 
"""

from pyqtgraph.graphicsItems.ViewBox import ViewBox
from pyqtgraph.graphicsItems.ViewBox.ViewBox import ChildGroup

import weakref
import sys
from copy import deepcopy
import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.python2_3 import sortList, basestring, cmp
from pyqtgraph.Point import Point
from pyqtgraph import functions as fn, getConfigOption, isQObjectAlive
from pyqtgraph.graphicsItems import ItemGroup
from pyqtgraph.graphicsItems.GraphicsWidget import GraphicsWidget
from pyqtgraph import debug, ItemGroup


class GlobalGroup(ItemGroup):
    def paint(self, *args):
        pass
    def addItem(self, item):
        item._paintable = False
        super().addItem(item)

class GlobalView(ViewBox):
    """
    **Bases:** :class:`GraphicsWidget <pyqtgraph.GraphicsWidget>`
    
    Can register and unregister viewboxes. Draws all global items for each
    view registered
    """
    def __init__(self, *args, globalItems=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.globalGroup = globalItems
        self._lastTransform = None

    def updateMatrix(self, changed=None):
        if not self._matrixNeedsUpdate:
            return

        ## Make the childGroup's transform match the requested viewRange.
        bounds = self.rect()
        
        vr = self.viewRect()
        if vr.height() == 0 or vr.width() == 0:
            return
        scale = Point(bounds.width()/vr.width(), bounds.height()/vr.height())
        if not self.state['yInverted']:
            scale = scale * Point(1, -1)
        if self.state['xInverted']:
            scale = scale * Point(-1, 1)
        m = QtGui.QTransform()
        
        ## First center the viewport at 0
        center = bounds.center()
        m.translate(center.x(), center.y())
            
        ## Now scale and translate properly
        m.scale(scale[0], scale[1])
        st = Point(vr.center())
        m.translate(-st[0], -st[1])
        
        self.childGroup.setTransform(m)
        # only here transformation can be achieved
        if not self.globalGroup is None:
            self.globalGroup.setTransform(m)
        
        self.sigTransformChanged.emit(self)  ## segfaults here: 1
        self._matrixNeedsUpdate = False

#     def paint(self, *args, **kwargs):
#         ret = super().paint(*args, **kwargs)
#         if self._lastTransform is None:
#             return ret
#         if not self.globalGroup is None:
#             print('transform')
#             self.globalGroup.setTransform(self._lastTransform)
#             self.globalGroup.transform()
#             for item in self.globalGroup.childItems():
#                 item.paint(*args, force=True)
#         return ret
