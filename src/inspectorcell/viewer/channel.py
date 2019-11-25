# -*- coding: utf-8 -*-
"""the channel used to display images, entities and forground annotations
"""

# built-ins
import sys
import warnings
import platform

# extern
import cv2
import numpy as np

# GUI stuff
import pyqtgraph as pg
from AnyQt import QtCore as qc, QtWidgets as qw, QtGui as qg
from AnyQt.QtWidgets import (QGraphicsRectItem, QGraphicsTextItem, QRubberBand,
                             QStyleOptionGraphicsItem as SOGI)
from pyqtgraph import Point

from ..event import ResetZoomEvent, ZoomEvent
from .image import BackgroundImage
from .label import ChannelLabel


class Channel(pg.GraphicsView):
    """A single channel showing all objects in a scene and some channel
    dependen background
    """

    # sigCrossHairMoved = qc.pyqtSignal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background = BackgroundImage()

        self.enableMouse(True)
        self.setAspectLocked(True)

        # readout label in channel
        self.chanLabel = ChannelLabel()
        self.chanLabel.set(0, text='INIT')
        self.chanLabel.setFlags(qw.QGraphicsItem.ItemIgnoresTransformations)
        self.chanLabel.setPos(10, 10)

        self.init_range = self.range
        self._infoBox = None
        self._crossHair = None
        self._rubberBand = None
        self._origin = None
        self._frame = None

        # initialize last mouse pos
        self.lastMousePos = Point(0, 0)

        #MAC needs different mouse handling
        if platform.system().lower() == 'darwin':
            self._dynamicMouseMode = False
        else:
            self._dynamicMouseMode = True

        # initialize last mouse pos
        self.lastMousePos = Point(0, 0)

        # MAC needs different mouse handling
        if platform.system().lower() == 'darwin':
            self._dynamicMouseMode = False
        else:
            self._dynamicMouseMode = True
    
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        self.background.paint(painter)

    def drawForeground(self, painter, rect):
        # super().drawForeground(painter, rect)
        painter.save()
        transf = painter.transform()
        scale = transf.m11(), transf.m22()
        painter.resetTransform()
        self.chanLabel.paint(painter, rect)

        if not self._infoBox is None:
            self._infoBox.paint(painter, rect)

        if not self._crossHair is None:
            self._crossHair.paint(painter, rect, scale)

        painter.restore()

        if not self._frame is None:
            self._frame.paint(painter, self.viewRect())

    def setHighlightFrame(self, frame):
        """sets the highlighting frame
        """
        if frame is None:
            self._frame = None
            return None

        self._frame = frame

    def setInfoBox(self, infoBox, ref=None):
        """sets the infobox containing information related to
        to some entity confined in the QRectF ref
        """
        if infoBox is None:
            self._infoBox = None
            return None

        self._infoBox = infoBox

        if ref is None:
            raise AttributeError('Missing rect=QRectF attribute')

        ref = self.mapFromScene(ref).boundingRect()
        self._infoBox.setPos(ref.bottomRight())

    def customEvent(self, event):

        if event == ResetZoomEvent:

            if event.autorange:
                if self.scene().itemsBoundingRect().isEmpty():
                    self.setRange(self.init_range, padding=0)
                else:
                    self.setRange(self.scene().itemsBoundingRect(), padding=0)
            else:
                self.setRange(self.init_range, padding=0)

            event.accept()

        if event == ZoomEvent:
            if event.zoomIn:
                scf = 1.2
            else:
                scf = 0.8

            self._zoom(scf)
            event.accept()

    def _zoom(self, scf, center=None):
        #XXX unified use of zoom in whole app
        self.scale(scf, scf, center=center)
        self.sigDeviceRangeChanged.emit(self, self.range)

    def wheelEvent(self, event):
        """rewrtiting as event.delta seems to be gone
        """
        if event.angleDelta().y() > 0:
            scf = 1.2
        else:
            scf = 0.8

        center=self.mapToScene(event.pos())
        self._zoom(scf, center)

        event.accept()

    def updateBackground(self):
        """Triggers update of scene, only in the areas where
        foreground elements are located
        """
        self.scene().invalidate(self.background.boundingRect(),
                                qw.QGraphicsScene.BackgroundLayer)
        self.scene().update()

    def updateForeground(self):
        """Triggers update of scene, only in the areas where
        foreground elements are located
        """
        # TODO not hole scene, but only the relevant areas
        # infobox mapped to scene and text mapped to scene
        self.scene().invalidate(self.range,
                                qw.QGraphicsScene.ForegroundLayer)
        self.scene().update()

    def mousePressEvent(self, ev):
        #XXX unify usage. For now overwriting modes on the fly
        # mouse button determines if paning or selecting is done
        #XXX do all mouse stuff either in channel or in scene
        drawing = self.scene().mode != 'N'
        if self._dynamicMouseMode and not drawing:
            if ev.buttons() == qc.Qt.MidButton:
                self.parent().mouseMode = self.parent().PanMode
            elif ev.buttons() == qc.Qt.LeftButton:
                self.parent().mouseMode = self.parent().RectMode

        if self.parent().mouseMode == self.parent().RectMode:
            self._origin = ev.pos()
            if self._rubberBand is None:
                self._rubberBand = QRubberBand(QRubberBand.Rectangle,
                                               parent=self)
            self._rubberBand.setGeometry(qc.QRect(self._origin, qc.QSize()))
            self._rubberBand.show()

        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        """Re-implementation of mouseMoveEvent for QGraphicsView
        """
        delta = Point(ev.pos() - self.lastMousePos)
        self.lastMousePos = Point(ev.pos())

        if not self._crossHair is None:
            self._crossHair.setPos(self.lastMousePos)
            # self.sigCrossHairMoved.emit(self.lastMousePos)

        super().mouseMoveEvent(ev)
        ev.ignore()

        if not self.mouseEnabled:
            return

        self.sigSceneMouseMoved.emit(self.mapToScene(ev.pos()))

        ## Ignore event if an item in the scene has already claimed it.
        if self.clickAccepted:
            return

        drawing = self.scene().mode != 'N'

        if self.parent().mouseMode == self.parent().PanMode:
            if ev.buttons() == qc.Qt.RightButton:
                delta = Point(
                    np.clip(delta[0], -50, 50), np.clip(-delta[1], -50, 50))

                scale = 1.01 ** delta
                self.scale(scale[0], scale[1],
                           center=self.mapToScene(self.mousePressPos))

                self.sigDeviceRangeChanged.emit(self, self.range)

            ## Allow panning by left or mid button.
            elif ev.buttons() in [qc.Qt.MidButton, qc.Qt.LeftButton]:
                px = self.pixelSize()
                tr = -delta * px

                self.translate(tr[0], tr[1])
                self.sigDeviceRangeChanged.emit(self, self.range)
        elif not drawing:
            if ev.buttons() in [qc.Qt.MidButton, qc.Qt.LeftButton]:
                #ev.pos()).normalized())
                self._rubberBand.setGeometry(
                    qc.QRect(self._origin, ev.pos()).normalized())

    def mouseReleaseEvent(self, ev):
        rectMode = self.parent().mouseMode == self.parent().RectMode
        drawing = self.scene().mode != 'N'
        if rectMode and not drawing:
            self._rubberBand.hide()

            rect = self.mapToScene(self._rubberBand.geometry())

            area = qg.QPainterPath()

            area.addPolygon(rect)
            self.scene().setSelectionArea(area)

        super().mouseReleaseEvent(ev)
