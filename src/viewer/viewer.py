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
        # implicit drawing at (0, 0)
        self.background.paint(painter)

    def wheelEvent(self, event):
        """We ignore the event here and process
        it in the Viewer
        """
        event.ignore()

    def wheelEvent(self, event):
        """rewrtiting as event.delta seems to be gone
        """
        if event.angleDelta().y() > 0:
            scf = 1.2
        else:
            scf = 0.8
        self.scale(scf, scf)
        event.accept()

    
class Viewer(qw.QWidget):
    """Holds and generates the views, all manipulation of views and thus
    the view state over this class
    """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # # build ui part
        # #TODO find proper parent
        # self.widget = qw.QWidget()

        self.grid_layout = qw.QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.grid_layout)

        # Channel, Scene
        self.channels = {}
        self.entity_scn = pg.GraphicsScene(parent=self)
        self.empty_scn = pg.GraphicsScene(parent=self)
        
        # register calls to function to save viewstate
        # later on
        self.state = CallTracker()

    def set_gridlayout(self, rows, cols):
        """ sets up the main viewgrid, depending on row and col number
        """
        self._spawn_views(rows=rows, cols=cols)

    def add_item(self, item):
        self.entity_scn.addItem(item)

    def _spawn_views(self, rows, cols):
        """ generates row * cols viewboxes with label, background and
        foreground/overlay images
        """
        for row in range(rows):
            for col in range(cols):
                cur_index = row, col
                cur_chan = self.channels.get(cur_index, None)
                if cur_chan is None:
                    #TODO find proper parent
                    cur_chan = Channel(self, useOpenGL=False)
                    cur_chan.sigDeviceRangeChanged.connect(self.sync_ranges)
                    cur_chan.setScene(self.empty_scn)

                self.channels[cur_index] = cur_chan
                self.grid_layout.addWidget(cur_chan, row, col)

    @qc.pyqtSlot(object, object)
    def sync_ranges(self, src_chan, new_range):
        """ Syncronizes the individual views
        """
        for cur_chan in self.channels.values():
            cur_chan.blockSignals(True)
        
        for cur_chan in self.channels.values():
            if not cur_chan is src_chan:
                cur_chan.setRange(new_range, padding=0)

        for cur_chan in self.channels.values():
            cur_chan.blockSignals(False)

    def set_background(self, index, imagedata):
        """Sets the background of channel at index to imagedata
        will silently fail if there is no channel at index
        """
        chan = self.channels.get(index, None)

        if chan is None:
            return

        chan.background.setImage(imagedata)

    def show_entities(self, index, show=True):
        """Sets channel at index to show entities
        will silently fail if there is no channel at index
        """
        chan = self.channels.get(index, None)

        if chan is None:
            return

        if show:
            chan.setScene(self.entity_scn)
        else:
            chan.setScene(self.empty_scn)


    # DEPRECIATED functions or properties
    @property
    def window(self):
        """ DEPRECEATED
        """
        warnings.warn('please use Viewer instance directly',
                      DeprecationWarning)
        return self

    def setup_grid(self, rows, cols):
        """ DEPRECEATED
        """
        warnings.warn('please use Viewer.set_gridlayout instead',
                      DeprecationWarning)
        return self.set_gridlayout(rows=rows, cols=cols)
