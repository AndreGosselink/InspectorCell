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


class HighlightFrame(pg.GraphicsObject):

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFlag(QGraphicsItem.ItemIsFocusable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setAcceptHoverEvents(False)

        # init properties, set them to defaults
        self._pen = None
        self.setProperties()

        # reference to which the infocpx belongs to
        self.ref = None

        self.setProperties()
        self._lastBoundingrect = None

    def setProperties(self, color=(255, 223, 59, 200), thickness=2.3):
        """set the properties of the frame
        """
        self._pen = fn.mkPen(*color)
        self._pen.setWidth(thickness)

    def boundingRect(self):
        if self._lastBoundingrect is None:
            self._lastBoundingrect = qc.QRectF(0, 0, 1, 1)

        return self._lastBoundingrect

    def paint(self, painter, rect):
        painter.save()
        painter.setBrush(qc.Qt.NoBrush)
        painter.setPen(self._pen)
        painter.drawRect(rect)
        self._lastBoundingrect = qc.QRectF(rect)
        painter.restore()
