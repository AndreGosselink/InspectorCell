# -*- coding: utf-8 -*-
"""Implements the main viewer element, to be used as a widget
generates views and manges them. implements interface to add and remove entities
and including background images.
"""

# built-ins
import warnings

# extern
import cv2

# GUI stuff
import pyqtgraph as pg
from AnyQt import QtCore as qc, QtWidgets as qw, QtGui as qg

# project
from ..graphics.scene import ViewerScene
from ..util import CallTracker
from .image import BackgroundImage
from .label import ChannelLabel
from .context import ContextMenu


class Channel(pg.GraphicsView):
    """A single channel showing all objects in a scene and some channel
    dependen background
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background = BackgroundImage()

        self.enableMouse(True)
        self.setAspectLocked(True)
        
        # readout label in channel
        self.chanLabel = ChannelLabel()
        self.chanLabel.set(0, text='INIT')
        self.chanLabel.setFlags(qw.QGraphicsItem.ItemIgnoresTransformations)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        # implicit drawing at (0, 0)
        self.background.paint(painter)

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        self.chanLabel.paint(painter, rect)

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
        self.entity_scn = ViewerScene(parent=self)
        self.empty_scn = ViewerScene(parent=self)
        self._activeChannel = None

        # Context menu
        self.contextMenu = ContextMenu()
        self.contextBtn = qc.Qt.RightButton
        
        # register calls to function to save viewstate
        # later on
        # self.state = CallTracker()

        self.viewSetup = {
            'rows': 2,
            'cols': 2,
            'cross': False,
        }

        self.imageRepository = {'background': {}}

        self._connect()

    def _connect(self):
        """connects
        """
        # proxy signal through
        self.contextMenu.sigSelected.connect(self.loadImage)
        self.contextMenu.sigShowItems.connect(self.changeItemVisibility)

    def update(self):
        """view layout, crosshair and other from 
        self.viewSetup
        """
        self._spawn_views(cols=self.viewSetup['cols'],
                          rows=self.viewSetup['rows'])

    def setBackgroundSelection(self, imageSelection):
        """view layout, crosshair and other from 
        self.viewSetup
        """
        rep = self.imageRepository['background'] = dict(imageSelection)
        self.contextMenu.updateSelection(rep.keys(), 'channelBg')

    def setGridlayout(self, rows, cols):
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

    def mousePressEvent(self, event):
        if event.button() == self.contextBtn:
            self.contextMenu.popup(event.screenPos().toPoint())
            self.setActiveChannel(event)

        event.ignore()
        super().mousePressEvent(event)

    def setActiveChannel(self, event):
        for curIndex, curChan in self.channels.items():
            if curChan.underMouse():
                self._activeChannel = curIndex
                break

        # if not ch_coords is None:
        #     for cur_view in self.views.values():
        #         cur_view.set_crosshair(ch_coords)

        event.ignore()
        super().mouseMoveEvent(event)

    def set_background(self, index, imagedata):
        """Sets the background of channel at index to imagedata
        will silently fail if there is no channel at index
        """
        chan = self.channels.get(index, None)

        if chan is None:
            return

        chan.background.setImage(imagedata)

    @qc.pyqtSlot(str, str)
    def loadImage(self, aName, selector):
        """load image to selector
        """
        if selector == 'channelBg':
            path = self.imageRepository['background'][aName]
            img = cv2.imread(str(path), cv2.IMREAD_ANYDEPTH)
            if not img is None and not self._activeChannel is None:
                self.set_background(self._activeChannel, img)
            elif img is None:
                self.set_background(self._activeChannel, np.array([], int))

    @qc.pyqtSlot(bool)
    def changeItemVisibility(self, visible):
        """change visivility of items in last active channel
        """
        self.show_entities(self._activeChannel, visible)

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
    
    @qc.pyqtSlot(str, str)
    def changeResource(self, resName, locationName):
        if locationName == 'channelBg':
            print('request for resName', resName)

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
        warnings.warn('please use Viewer.setGridlayout instead',
                      DeprecationWarning)
        return self.setGridlayout(rows=rows, cols=cols)

    def set_gridlayout(self, rows, cols):
        """ DEPRECEATED
        """
        warnings.warn('please use Viewer.setGridlayout instead',
                      DeprecationWarning)
        return self.setGridlayout(rows=rows, cols=cols)
