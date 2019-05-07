"""Simple example to test viewbox based approaches
"""


import random
import pyqtgraph as pg
from PyQt5.QtGui import QPen, QColor
from monkeyview import GlobalView, ViewBox, GlobalGroup
from pyqtgraph.graphicsItems.ViewBox.ViewBox import ChildGroup
import IPython as ip

from pyqtgraph.Qt import QtGui as qg, QtCore as qc

import pyqtgraph as pg
import numpy as np


class Poly(pg.GraphicsObject):

    def __init__(self, color):
        super().__init__()

        pos = qc.QPointF(0, 0)
        self.setPos(pos)

        pen = QPen()
        pen.setColor(QColor(*color))
        pen.setWidth(1)
        self.setPen(pen)

        pts0 = []
        pts1 = []
        r = 10
        for x in np.linspace(-9.9, 9.9, 20):
            disc = r**2 - x**2
            y = np.sqrt(disc)
            pts0.append((x + random.random(), y + random.random()))
            pts1.append((x + random.random(), - y - random.random()))

        self.poly = qg.QPolygonF()
        for p in pts0 + pts1[::-1]:
            self.poly.append(qc.QPointF(*p))

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

    def paint(self, p, *args):
        p.setRenderHint(p.Antialiasing)

        left, top, right, bottom = (0, 0, 2, 2)
        hor0 = left, 0.0
        hor1 = right, 0.0
        ver0 = 0.0, top
        ver1 = 0.0, bottom

        self.pen.setJoinStyle(qc.Qt.MiterJoin)
        p.setPen(self.pen)
        p.drawPolygon(self.poly)

    def boundingRect(self):
        return self.poly.boundingRect()

app = qg.QApplication([])
layout = pg.GraphicsLayout(border=(100, 100, 100))

view = pg.GraphicsView()
view.setCentralItem(layout)
view.show()

poly0 = Poly(color=(255, 99, 71, 255))
poly0.setPos((5, 5))
poly1 = Poly(color=(99, 255, 71, 255))
poly1.setPos((10, 10))
poly2 = Poly(color=(255, 255, 71, 255))
poly2.setPos((15, 15))

global_items = [poly2]
view.scene().addItem(poly2)

vbox0 = GlobalView(lockAspect=True, globalItems=global_items)
vbox1 = GlobalView(lockAspect=True, globalItems=global_items)

layout.addItem(vbox0)
layout.addItem(vbox1)

vbox0.addItem(poly0)
vbox1.addItem(poly1)

# vbox0.childGroup.setParentItem(vbox1)

assert vbox0.scene() is vbox1.scene()

print('go!')
app.exec_()
