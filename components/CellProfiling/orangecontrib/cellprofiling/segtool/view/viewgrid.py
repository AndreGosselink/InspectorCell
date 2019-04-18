# -*- coding: utf-8 -*-

import re
import warnings
import logging

# from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QRectF, QPointF
import PyQt5.QtCore as qc
import PyQt5.QtGui as qg
import PyQt5.QtWidgets as qw

import pyqtgraph as pg

import numpy as np

from . import get_logger_name
from .viewbox import GridViewBox
from .imgprocesswin import ContrastEnhanceWin
from .images import get_flipped

from ..events import ReposUpdated, ErrorEvent, ModifyResReq


class ViewGrid(pg.GraphicsLayoutWidget):
    """ImageContainer holding ImageItem and all data in the current MICS stack
    optimized for 16 bit and with patched drawing capabilities
    """

    def __init__(self, parent=None, logger_domain=None):
        super().__init__(parent=parent)

        # logging stuff
        self.logger_name = get_logger_name(name='ViewGrid',
                                           domain=logger_domain)
        self.log = logging.getLogger(self.logger_name)
        self.log.setLevel(logging.DEBUG)

        # # ViewBox
        self.views = {}
        self.layout = (-1, -1)

        # last repo update
        self.last_repo_update = None

        # tag selection to be used by views
        self.tag_selection = []

        # keeps state for all viewboxes, if image_repos was just loaded
        self.just_loaded = False

        self.contrast_win = ContrastEnhanceWin(img_item=None,
                                               enhancer=None, parent=self)

        self._oid_map = None

    def setup_grid(self, cols, rows, crosshair=False):
        """ sets up the main viewgrid, depending on row and col number
        """
        #TODO add col/rowspan?
        # generate ViewBox
        
        if self.layout != (cols, rows):
            self.log.debug('removing view boxes...')
            self.clear()
            self.layout = (cols, rows)
            self._spawn_views(cols, rows)

        if crosshair:
            pen = (200, 200, 100, 255)
        else:
            pen = (0, 0, 0, 0)

        for cur_view in self.views.values():
            cur_view.crosshair.setPen(pen)


    def _spawn_views(self, cols, rows):
        """ generates row * cols viewboxes with label, background and
        foreground/overlay images
        """
        for col in range(cols):
            for row in range(rows):
                cur_index = col, row
                cur_view = self.views.get(cur_index, None)
                if cur_view is None:
                    self.log.debug('Creating viewbox %s', str(cur_index))
                    cur_view = GridViewBox(default_label=str(cur_index),
                                           drawable=False, grid=self,
                                           parent=self.ci,
                                           enhance_callback=self.enhance_view)
                    cur_view.sigRangeChanged.connect(self.sync_ranges)
                else:
                    self.log.debug('Reusing viewbox %s', str(cur_index))

                self.views[cur_index] = cur_view
                self.addItem(cur_view, row=row, col=col)

                #TODO Ugly, make it better with the one unifiede repo...
                if not self.last_repo_update is None:
                    self.update_repos(self.last_repo_update)

    @qc.pyqtSlot(object, object)
    def sync_ranges(self, src_view, sig_range):
        """ Syncronizes the individual views
        """
        # sync changed, so its not 'just loaded' anymore
        self.just_loaded = False

        for cur_view in self.views.values():
            cur_view.blockSignals(True)

        src_view._resetTarget()
        new_xrange, new_yrange = src_view.viewRange()
        for cur_view in self.views.values():
            if not cur_view is src_view:
                cur_view._resetTarget()
                cur_view.setRange(
                    xRange=new_xrange, yRange=new_yrange, padding=0)

        for cur_view in self.views.values():
            cur_view.blockSignals(False)

    def customEvent(self, event):
        if event == ReposUpdated:
            self.update_repos(event.repos, wipe=event.wipe)
            event.accept()
        elif event == ModifyResReq:
            if event.res_type == 'obj.tag':
                if event.modification['objid'] <= 0:
                    event.accept()
                else:
                    event.ignore()
        else:
            event.ignore()

    def get_objid_map(self):
        misc_rep = self.last_repo_update['misc']
        callback = misc_rep['object_id_map']
        try:
            self._oid_map = get_flipped(callback())
        except ValueError:
            self._oid_map = None

    def get_object(self, oid):
        if oid is None:
            raise KeyError('Not a valid oid!')
        misc_rep = self.last_repo_update['misc']
        callback = misc_rep['object']
        try:
            return callback(oid)
        except ValueError:
            return None

    def set_cursor_info(self, view, x, y):
        x, y = int(np.ceil(x)), int(np.ceil(y))
        try:
            oid = self._oid_map[x, y]
        except (TypeError, IndexError):
            oid = None

        try:
            obj = self.get_object(oid)
            tags = obj.tags
        except KeyError:
            tags = []

        view.set_cursor_info(oid, tags)

    def mouseMoveEvent(self, event):
        ch_coords = None
        for cur_view in self.views.values():
            view_rect = cur_view.boundingRect()
            view_coords = cur_view.mapFromParent(event.pos())
            if view_rect.contains(view_coords):
                xpos, ypos = cur_view.get_bg_coord(view_coords)
                self.set_cursor_info(cur_view, xpos, ypos)
                cur_view.set_crosshair(qc.QPointF(-100, -100))
                ch_coords = qc.QPointF(xpos, ypos)
                break
        
        if not ch_coords is None:
            for cur_view in self.views.values():
                cur_view.set_crosshair(ch_coords)

        event.ignore()
        super().mouseMoveEvent(event)

    def update_repos(self, repo_update, wipe=False):
        # just distributing the event to all views
        for cur_view in self.views.values():
            #TODO unify me plz one repo/injector for all
            #TODO more unification, update callbacks inection
            # call these whenever needed
            cur_view.update_repos(repo_update)
            self.last_repo_update = repo_update.copy()
            if wipe:
                cur_view.wipe_images()
                self.just_loaded = True
        self.get_objid_map()

    def update_tag_selection(self, new_tags):
        # just distributing the event to all views
        for cur_view in self.views.values():
            #TODO unify me plz one repo/injector for all
            cur_view.update_tag_selection(new_tags)

    def enhance_view(self, view):
        img_item = view.layer_data['bg']['img']
        self.contrast_win.img_item = img_item
        self.contrast_win.enhancer = view.enhancer
        self.contrast_win.set_controls()
        self.contrast_win.show()
