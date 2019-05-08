# -*- coding: utf-8 -*-

"""Implements the main viewer element, to be used as a widget
generates views and manges them. implements interface to add and remove entities
and including background images.
"""
import warnings
import inspect

import AnyQt.QtCore as qc
import AnyQt.QtWidgets as qw

import pyqtgraph as pg


class Channel(pg.GraphicsView):
    """A single channel showing all objects in a scene and some channel
    dependen background
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.background = BackgroundImage()

    def drawBackground(self, painter, rect):
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


class ViewStateTracker():
    """Class holding all information of the current viewer State and methods
    to save/load the state
    """

    def __init__(self, rows=2, cols=2, crosshair=False):
        self.crosshair = crosshair
        self.calls = {}

    def get_tracker(self, key, func):
        """get an wrapper to func if key is a key in track
        the wrapper will map the function call and store the
        parameters in ViewState.track
        """
        if key in self.track:
            # get signature names of function to track
            sig = inspect.signature(func)
            pnames = sig.parameters.keys()
            # define the wrapper function
            def _tracker(*args, **kwargs):
                self.calls[key] = dict(zip(pnames, args))
                self.calls[key].update(kwargs)
                return func(*args, **kwargs)
            # return the wrapped function
            return _tracker
        else:
            # otherwise just return the bare function
            return func


class Viewer():
    """Holds and generates the views, all manipulation of views and thus
    the view state over this class
    """

    def __init__(self, parent=None):

        # build ui part
        self.window = qw.QMainWindow(parent)
        self.layout = pg.GraphicsLayoutWidget(parent)
        self.window.setCentralWidget(self.layout)

        # Channel, Scene
        self.views = {}
        self.scene = None

        # the state object
        self.state = ViewStateTracker()

    def __getattr__(self, name):
        """wraps all registered calls to the state object. Allows
        on-the-fly tracking for registers calls that have relevant side
        effects
        """
        attr = self.__dict__[name]
        return self.state.get_tracker(name, attr)

    def set_gridlayout(self, rows, cols):
        """ sets up the main viewgrid, depending on row and col number
        """
        if self.state.gridlayout != (rows, cols):
            self.layout.clear()
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
                    cur_view = ()
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

    def setup_grid(self, rows, cols):
        """ DEPRECEATED
        """
        warnings.warn('please use Viewer.set_gridlayout instead',
                      DeprecationWarning)
        self.set_gridlayout(rows=rows, cols=cols)
