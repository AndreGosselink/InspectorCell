import PyQt5.QtCore as QtCore
import PyQt5.QtCore as qc
import PyQt5.QtGui as QtGui
import pyqtgraph as pg
import pyqtgraph.functions as fn
from pyqtgraph import Point

import numpy as np


class CrossHair(pg.GraphicsObject):

    def __init__(self, pos=None, pen=None, width=20, height=20):
        """
        just a crosshair
        """
        super().__init__()

        self.width = float(width)
        self.height = float(height)

        self._bounds = None
        self._boundingRect = None
        self._lastViewSize = None

        self._diag = 0, 0, 1, 1

        self.pos = [0, 0]

        if pos is None:
            pos = Point(0,0)
        self.setPos(pos)

        if pen is None:
            pen = (200, 200, 100)
        self.setPen(pen)
        
    def setPen(self, *args, **kwargs):
        """Set the pen for drawing the line. Allowable arguments are any that are valid
        for :func:`mkPen <pyqtgraph.mkPen>`."""
        self.pen = fn.mkPen(*args, **kwargs)
        self.update()

    def setPos(self, pos):

        if type(pos) in [list, tuple]:
            newPos = pos
        elif isinstance(pos, QtCore.QPointF):
            newPos = [pos.x(), pos.y()]

        if self.pos != newPos:
            self.pos = newPos
            self._invalidateCache()
            super().setPos(Point(self.pos))

    def getXPos(self):
        return self.pos[0]

    def getYPos(self):
        return self.pos[1]

    def getPos(self):
        return self.pos

    def _invalidateCache(self):
        self._boundingRect = None

    def _computeBoundingRect(self):
        # bounds of containing ViewBox mapped to local coords.
        view_rect = self.viewRect()
        if view_rect is None:
            return QtCore.QRectF()
        
        ## add a 4-pixel radius around the line for mouse interaction.

        ## get pixel length orthogonal to the line
        px_size = self.pixelLength(direction=Point(1, 0), ortho=True)
        if px_size is None:
            px_size = 0
        
        # width = float(view_rect.width()) * 0.1
        # height = float(view_rect.height()) * 0.1
        width = self.width * px_size / 2
        height = self.height * px_size / 2
        bounding_rect = QtCore.QRectF(view_rect)
        bounding_rect.setLeft(-width)
        bounding_rect.setRight(width)
        bounding_rect.setBottom(-height)
        bounding_rect.setTop(height)
        bounding_rect = bounding_rect.normalized()

        view_size = self.getViewBox().size()

        if self._bounds != bounding_rect or self._lastViewSize != view_size:
            self._bounds = bounding_rect
            self._lastViewSize = view_size
            self.prepareGeometryChange()

        self._lastViewRect = view_rect

        return self._bounds

    def boundingRect(self):
        if self._boundingRect is None:
            self._boundingRect = self._computeBoundingRect()
        self._diag = self._boundingRect.left(), self._boundingRect.top(),\
            self._boundingRect.right(), self._boundingRect.bottom()
        return self._boundingRect

    def paint(self, p, *args):
        p.setRenderHint(p.Antialiasing)

        left, top, right, bottom = self._diag
        hor0 = left, 0.0
        hor1 = right, 0.0
        ver0 = 0.0, top
        ver1 = 0.0, bottom

        self.pen.setJoinStyle(QtCore.Qt.MiterJoin)
        p.setPen(self.pen)
        p.drawLine(qc.QPointF(*ver0), qc.QPoint(*ver1))
        p.drawLine(qc.QPointF(*hor0), qc.QPoint(*hor1))
        
    def viewTransformChanged(self):
        """
        Called whenever the transformation matrix of the view has changed.
        (eg, the view range has changed or the view was resized)
        """
        self._invalidateCache()
