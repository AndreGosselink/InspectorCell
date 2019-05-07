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
from pyqtgraph import debug


class GlobalGroup(ChildGroup):

    def __init__(self, *args, globalItems=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.globalItems = globalItems

    def children(self):
        super().children() + self.globalItems


class GlobalView(ViewBox):
    """
    **Bases:** :class:`GraphicsWidget <pyqtgraph.GraphicsWidget>`
    
    Can register and unregister viewboxes. Draws all global items for each
    view registered
    """
    def __init__(self, *args, globalItems=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.childGroup = GlobalGroup(self, globalItems=globalItems)
        self.childGroup.itemsChangedListeners.append(self)

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
        for item in self.childGroup.globalItems:
            item.setTransform(m)
        
        self.sigTransformChanged.emit(self)  ## segfaults here: 1
        self._matrixNeedsUpdate = False
