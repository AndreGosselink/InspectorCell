import random
import pyqtgraph as pg
from PyQt5.QtGui import QPen, QColor

from pyqtgraph.Qt import QtGui as qg, QtCore as qc

import pyqtgraph as pg
import numpy as np


class Poly(pg.GraphicsObject):

    def __init__(self):
        """
        just a crosshair
        """
        super().__init__()

        self._diag = (0, 0, 1, 1)

        pos = qc.QPointF(0, 0)
        self.setPos(pos)

        pen = QPen()
        pen.setColor(QColor(255, 99, 71, 255))
        pen.setWidth(1)
        self.setPen(pen)

        pts_num = 50 # to make contour more clear
        x0, y0 = 100, 100 # with 0,0 contour can be drawn out of view (minus coordinates values)
        pts = []
        for i in range(pts_num):
            py = random.random()
            dx = random.random()
            if random.random() > 0.8:
                x0 += dx
            else:
                x0 -= dx
            if random.random() > 0.9:
                y0 += dx
            else:
                y0 -= dx
            pts.append((x0, y0))

        self.poly = qg.QPolygonF()
        for p in pts:
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

        left, top, right, bottom = self._diag
        hor0 = left, 0.0
        hor1 = right, 0.0
        ver0 = 0.0, top
        ver1 = 0.0, bottom

        self.pen.setJoinStyle(qc.Qt.MiterJoin)
        p.setPen(self.pen)
        # p.drawLine(qc.QPointF(*ver0), qc.QPoint(*ver1))
        # p.drawLine(qc.QPointF(*hor0), qc.QPoint(*hor1))
        p.drawPolygon(self.poly)

    def viewTransformChanged(self):
        """
        Called whenever the transformation matrix of the view has changed.
        (eg, the view range has changed or the view was resized)
        """
        self._invalidateCache()

app = qg.QApplication([])
layout = pg.GraphicsLayout(border=(100,100,100))

view = pg.GraphicsView()
view.setCentralItem(layout)
view.show()

vbox0 = layout.addViewBox(lockAspect=True)
vbox1 = layout.addViewBox(lockAspect=True)

vbox0.scene().addItem(Poly())


## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        qg.QApplication.instance().exec_()
