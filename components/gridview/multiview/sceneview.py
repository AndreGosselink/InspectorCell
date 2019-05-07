# -*- coding: utf-8 -*-
import numpy as np

import AnyQt.QtCore as qc
import AnyQt.QtGui as qg
import AnyQt.QtWidgets as qw

import pyqtgraph as pg


class SceneViewer(pg.GraphicsView):
    pass

    def wheelEvent(self, ev):
        qg.QGraphicsView.wheelEvent(self, ev)
        if not self.mouseEnabled:
            ev.ignore()
            return
        if ev.angleDelta().y() > 0:
            sc = 1.2
        else:
            sc = 0.8
        # sc = 1.001 ** ev.delta()
        #self.scale *= sc
        #self.updateMatrix()
        self.scale(sc, sc)
