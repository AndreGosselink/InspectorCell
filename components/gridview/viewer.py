# -*- coding: utf-8 -*-

"""Implements the main viewer element.
"""

import AnyQt.QtCore as qc
import AnyQt.QtWidgets as qw

from viewbox import GridViewBox

import pyqtgraph as pg


class ViewState():
    """Class holding all information of the current viewer State and methods
    to save/load the state
    """
    def __init__(self, rows=2, cols=2, crosshair=False):
        self.crosshair = crosshair
        self.gridlayout = (rows, cols)

    @property
    def rows(self):
        return self.gridlayout[0]

    @property
    def cols(self):
        return self.gridlayout[1]


class Viewer():
    """Holds and generates the views, all manipulation over this
    instance
    """

    def __init__(self, parent=None):

        # build ui part
        self.window = qw.QMainWindow(parent)
        self.layout = pg.GraphicsLayoutWidget(parent)
        self.window.setCentralWidget(self.layout)

        # self.setObjectName('GridViewWidget')

        # ViewBox
        self.views = {}
        self.state = ViewState()

    def setup_grid(self, rows, cols):
        """ sets up the main viewgrid, depending on row and col number
        """
        if self.state.gridlayout != (rows, cols):
            self.layout.clear()
            self.state.gridlayout = (rows, cols)
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
                    cur_view = GridViewBox()
                    cur_view.sigRangeChanged.connect(self.sync_ranges)

                self.views[cur_index] = cur_view
                self.layout.addItem(cur_view, row, col)

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
