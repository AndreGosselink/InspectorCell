"""CrossHair for channel instances
"""
import pyqtgraph as pg
from AnyQt.QtGui import QPen, QColor, QBrush, QPainter, QPixmap, QPicture
from AnyQt import QtCore as qc, QtGui as qg
from AnyQt.QtWidgets import QGraphicsItem
import AnyQt.QtCore as qc
import pyqtgraph as pg
import pyqtgraph.functions as fn
from pyqtgraph import Point

import numpy as np


class CrossHair(pg.GraphicsObject):

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFlag(QGraphicsItem.ItemIsFocusable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptHoverEvents(False)

        # init properties, set them to defaults
        self._cross = None
        # self._circle = None
        self._radius = 0
        self._pen = None
        self.width = None
        self.height = None
        self.setProperties()

        # reference to which the infocpx belongs to
        self.ref = None

        self.setProperties()
        self.oldBoundingRect = self.boundingRect()

    def setProperties(self, color=(205, 117, 40, 200), width=20, height=20,
                      thickness=2.3, radius=0):
        """set the properties of the infobox
        """
        self._pen = fn.mkPen(*color)
        self._pen.setWidth(thickness)

        self.width, self.height = width, height

        # self._cross = QPixmap(width, height)
        # painter = QPainter(self._cross)
        # painter.fillRect(self._cross.rect(), QColor(0, 0, 0, 0));
        # painter.setPen(self._pen)
        # painter.drawLine(0, 0, 10, 10)
        # painter.drawLine(10, 0, 0, 10)
        # painter.end()

        if width > 0 and height > 0:
            self._cross = QPicture()
            painter = QPainter(self._cross)
            painter.setPen(self._pen)
            self._addCross(painter, width, height)
            painter.end()
        else:
            self._cross = QPicture()

        self._radius = radius
        self._width = width
        self._height = height
        # if radius > 0:
        #     self._circle = QPicture()
        #     painter = QPainter(self._circle)
        #     painter.setPen(self._pen)
        #     self._addCircle(painter, width, height, radius)
        #     painter.end()
        # else:
        #     self._circle = QPicture()

    def _addCross(self, painter, width, height):
        hpt0 = qc.QPointF(0, height/2)  
        hpt1 = qc.QPointF(width, height/2)  
        vpt0 = qc.QPointF(width/2, 0)  
        vpt1 = qc.QPointF(width/2, height)  
        painter.drawLine(hpt0, hpt1)
        painter.drawLine(vpt0, vpt1)

    # def _addCircle(self, painter, width, height, radius):
    #     center = qc.QPointF(width/2, height/2)  
    #     painter.drawEllipse(center, radius, radius)

    def setPos(self, pos):
        # self.oldBoundingRect = self.boundingRect()
        y = pos.y() - (self.height / 2)
        x = pos.x() - (self.width / 2)
        super().setPos(x, y)

    def getXPos(self):
        return self.pos[0]

    def getYPos(self):
        return self.pos[1]

    def getPos(self):
        return self.pos

    def boundingRect(self):
        brect = self._cross.boundingRect()
        brect.moveTo(self.pos().x(), self.pos().y())
        return brect

    def _drawCircle(self, painter, scale):
        pos = self.pos()
        center = qc.QPointF(
            pos.x() + self._width/2,
            pos.y() + self._height/2)  
        radx = self._radius * scale[0]
        rady = self._radius * scale[1]
        painter.setPen(self._pen)
        painter.drawEllipse(center, radx, rady)

    def paint(self, painter, rect, scale):
        # self._content.paint(painter, rect, target=None)
        # painter.drawPixmap(qc.QPointF(self.pos()), self._cross)

        painter.save()
        painter.drawPicture(self.pos(), self._cross)
        # painter.setTransform(transf)
        # painter.drawPicture(self.pos(), self._circle)
        if self._radius > 0:
            self._drawCircle(painter, scale)
        painter.restore()

        # painter.save()
        # painter.setCompositionMode(QPainter.CompositionMode_Source);
        # painter.drawPixmap(self.pos(), self._cross)
        # painter.restore()
