"""silly cirles to play around with and other util stuff
"""

import random
from pyqtgraph.Qt import QtGui as qg, QtCore as qc

import pyqtgraph as pg
import numpy as np


class Poly(pg.GraphicsObject):
    """simple testing object
    """

    def __init__(self, color=(255, 180, 50, 255), pts=5, rad=10):
        """
        color: color of pen
        pts: number of points in polygon
        rad: radius of polygons
        """
        super().__init__()

        pos = qc.QPointF(0, 0)
        self.picture = None

        self.setPos(pos)

        pen = qg.QPen()
        pen.setColor(qg.QColor(*color))
        pen.setWidth(1)
        pen.setJoinStyle(qc.Qt.MiterJoin)
        self.setPen(pen)

        pts0 = []
        pts1 = []
        pts = int(np.round(pts / 2))
        for x in np.linspace(-9.9, 9.9, pts):
            disc = rad**2 - x**2
            y = np.sqrt(disc)
            pts0.append((x + random.random(), y + random.random()))
            pts1.append((x + random.random(), - y - random.random()))

        self.poly = qg.QPolygonF()
        for p in pts0 + pts1[::-1]:
            self.poly.append(qc.QPointF(*p))

        self.generate_picture()

    def _invalidateCache(self):
        self._boundingRect = None

    def setPen(self, *args, **kwargs):
        """Set the pen for drawing the line. Allowable arguments are any that are valid
        for :func:`mkPen <pyqtgraph.mkPen>`."""
        self.pen = pg.fn.mkPen(*args, **kwargs)
        self.update()

    def setPos(self, pos):

        if type(pos) in [list, tuple]:
            newPos = pos
        elif isinstance(pos, qc.QPointF):
            newPos = [pos.x(), pos.y()]

        if self.pos != newPos:
            self.pos = newPos
            self._invalidateCache()
            super().setPos(qc.QPointF(self.pos[0], self.pos[1]))

    def getXPos(self):
        return self.pos[0]

    def getYPos(self):
        return self.pos[1]

    def getPos(self):
        return self.pos

    def generate_picture(self):
        ## pre-computing a QPicture object allows paint() to run much more quickly, 
        ## rather than re-drawing the shapes every time.
        self.picture = qg.QPicture()
        p = qg.QPainter(self.picture)
        p.setPen(self.pen)
        p.drawPolygon(self.poly)
        p.end()

    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return self.poly.boundingRect()
