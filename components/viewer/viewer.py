# -*- coding: utf-8 -*-
"""Implements the main viewer element, to be used as a widget
generates views and manges them. implements interface to add and remove entities
and including background images.
"""

# built-ins
import warnings

# GUI stuff
import pyqtgraph as pg
import AnyQt.QtCore as qc
from AnyQt import QtGui as qg, QtCore as qc, QtWidgets as qw

# project
from tracker import CallTracker
from res import BackgroundImage


class Channel(pg.GraphicsView):
    """A single channel showing all objects in a scene and some channel
    dependen background
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background = BackgroundImage()

        self.enableMouse(True)
        self.setAspectLocked(True)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        self.background.paint(painter)

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
        ev.accept()


class Viewer():
    """Holds and generates the views, all manipulation of views and thus
    the view state over this class
    """

    def __init__(self, parent=None):

        # build ui part
        #TODO find proper parent
        self.widget = qw.QWidget()

        self.layout = qw.QGridLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.widget.setLayout(self.layout)

        # Channel, Scene
        self.views = {}
        self.scene = pg.GraphicsScene(parent=self.widget)
        
        # register calls to function to save viewstate
        # later on
        self.state = CallTracker()

    def set_gridlayout(self, rows, cols):
        """ sets up the main viewgrid, depending on row and col number
        """
        # self.layout.clear()
        self._spawn_views(rows=rows, cols=cols)

    def _spawn_views(self, rows, cols):
        """ generates row * cols viewboxes with label, background and
        foreground/overlay images
        """
        for row in range(rows):
            for col in range(cols):
                cur_index = row, col
                cur_view = self.views.get(cur_index, None)
                if cur_view is None:
                    #TODO find proper parent
                    cur_view = Channel()
                    # cur_view.sigRangeChanged.connect(self.sync_ranges)
                    cur_view.setScene(self.scene)

                self.views[cur_index] = cur_view
                self.layout.addWidget(cur_view, row, col)

    # @qc.pyqtSlot(object, object)
    def sync_ranges(self, src_view):
        """ Syncronizes the individual views
        """
        for cur_view in self.views.values():
            cur_view.blockSignals(True)

        #TODO might not be needed if it is, comment please...
        # src_view._resetTarget()
        new_xrange, new_yrange = src_view.viewRange()
        for cur_view in self.views.values():
            if not cur_view is src_view:
                #TODO same as above
                # cur_view._resetTarget()
                cur_view.setRange(
                    xRange=new_xrange, yRange=new_yrange, padding=0)

        for cur_view in self.views.values():
            cur_view.blockSignals(False)

    def setup_grid(self, rows, cols):
        """ DEPRECEATED
        """
        warnings.warn('please use Viewer.set_gridlayout instead',
                      DeprecationWarning)
        return self.set_gridlayout(rows=rows, cols=cols)
    
    def set_background(self, index, imagedata):
        """Sets the background of channel at index to imagedata
        will silently fail if there is no channel at index
        """
        chan = self.views.get(index, None)

        if chan is None:
            return

        chan.background.setImage(imagedata)

    @property
    def window(self):
        """ DEPRECEATED
        """
        warnings.warn('please use Viewer.widget instead',
                      DeprecationWarning)
        return self.widget

    def wheelEvent(self, ev):
        ev.ignore()
