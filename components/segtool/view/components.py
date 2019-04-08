# -*- coding: utf-8 -*-

import numpy as np

import PyQt5
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QRectF, QPointF
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QFileDialog

import pyqtgraph as pg
from pyqtgraph.graphicsItems.ViewBox.ViewBoxMenu import ViewBoxMenu

import IPython as ip


defaults_background = dict(
    levels=np.array([0, 0xffff], dtype=np.uint16),
    autoLevels=False,
    autoDownsample=False,
)

defaults_overlay = dict(image=None,
    levels=np.array([[0, 0xff], [0, 0xff], [0, 0xff]], dtype=np.uint8),
    autoLevels=False,
    autoDownsample=False,
    compositionMode=QPainter.CompositionMode_SourceOver,
)


class OverlayImage(pg.ImageItem):

    def __init__(self):
        super().__init__(**defaults_overlay)

    @pyqtSlot(object, object, object, object, object, object)
    def _draw(self, kernds, r0ds, bytes_per_row, brush_rgba, byte0, update_rect):
        for r, kernrow in enumerate(kernds, r0ds):
            arr = self.qimage.scanLine(r).asarray(bytes_per_row)
            for i, m in enumerate(kernrow):
                if not m:
                    continue
                else:
                    # additional lookups for each byte/pixel makes it slow...
                    for b, val in enumerate(brush_rgba, byte0 + (4 * i)):
                        arr[b] = val
         
        self.update(update_rect)

    def mouseClickEvent(self, ev):
        if ev.button() == Qt.RightButton:
            self._last_rightclick = ev.pos()


class DrawOverlayImage(OverlayImage):
    """ Detexts drawing, emits signal accordingly
    """

    sigOverlayImageChange = pyqtSignal(object, object, object, object, object, object)

    def _get_objid_at(self, atrow, atcol):
        raise ValueError('ObjId Map not set')

    def set_brush(self, radius=None, rgba=None):
        if not rgba is None:
            self.brush_rgba = rgba

        if not radius is None:
            rrange = np.arange(-radius, radius+1)
            h, w = np.meshgrid(rrange, rrange)
            self.kern = np.sqrt(h**2 + w**2) <= radius

    def drawAt(self, row, col, objid):
        try:
            # might not be present if image was not rendered yet
            colds, rowds = self._lastDownsample
        except AttributeError as e:
            colds = rowds = 1
 
        w = self.kern.shape[0]
        c0, r0 = col - (w // 2), row - (w // 2)
        c1, r1 = c0 + w, r0 + w
        update_rect = QRectF(c0, r0, c1, r1)

        # draw the object id map
        self.objid_map[r0:r1, c0:c1][self.kern] = objid

        # iterate over kernel, skipping lines based on the downsampling
        # thisl will result in degraded kernel shape and in the worst case
        # result in loss of rowds-1 or colds-1 lines/cols from the brushkernel
        c0ds = int(round(c0 / colds))
        r0ds = int(round(r0 / rowds))

        kernds = self.kern[::rowds,::colds]
        rows = kernds.shape[0]
        byte0 = c0ds * 4
        bytes_per_row = byte0 + (kernds.shape[1] * 4)

        self._draw(kernds, r0ds, bytes_per_row, self.brush_rgba, byte0, update_rect)
        self.sigOverlayImageChange.emit(kernds, r0ds, bytes_per_row, self.brush_rgba, byte0, update_rect)

    def mouseDragEvent(self, ev):
        row, col, objid = self.get_drawprops(ev)

        if ev.button() == Qt.LeftButton and self.kern is not None:
            self.drawAt(row, col, objid)
            ev.accept()
        elif ev.button() == Qt.RightButton:
            ev.ignore()

    def mouseClickEvent(self, ev):
        row, col, objid = self.get_drawprops(ev)

        if ev.button() == Qt.RightButton:
            if self.raiseContextMenu(ev):
                ev.accept()
        elif ev.button() == Qt.LeftButton and self.kern is not None:
            self.drawAt(row, col, objid)
            ev.accept()

    def get_drawprops(self, ev):
        pos = ev.pos()
        # padding border, not drawable
        pad = int(np.ceil(self.kern.shape[0] / 2))
        # when dragging default to min max possible values
        row = min(self._height - pad, max(pad, int(pos.y())))
        col = min(self._width - pad, max(pad, int(pos.x())))

        # for the starting pos if applicable
        try:
            atpos = ev.lastPos()
            atrow = min(self._height - pad, max(pad, int(atpos.y())))
            atcol = min(self._width - pad, max(pad, int(atpos.x())))
        except:
            atrow, atcol = row, col

        objid_at = self._get_objid_at(atrow, atcol)

        if objid_at == 0:
            objid_at = np.max(self.objid_map) + 1

        return row, col, objid_at




