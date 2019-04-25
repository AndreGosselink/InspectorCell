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

from ..events import ReposUpdated, ErrorEvent, ModifyResReq, ModifyView


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

        # last view hovered over
        self._active_view = None
        self._last_px = None

        # last repo update
        self.last_repo_update = None

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
                    if cur_index == (0, 0):
                        cur_view.show_roi()
                else:
                    self.log.debug('Reusing viewbox %s', str(cur_index))

                self.views[cur_index] = cur_view
                self.addItem(cur_view, row=row, col=col)

                #TODO Ugly, make it better with the one unifiede repo...
                if not self.last_repo_update is None:
                    self.update_repos(self.last_repo_update)

    @qc.pyqtSlot(object, object)
    def sync_ranges(self, src_view):
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

    def _remap_roi(self, roi):
        # ref_view = roi.parent()
        pos, size = roi.pos(), roi.size()
        # img_coords = ref_view.get_bg_coord(pos)
        # img_size = ref_view.get_bg_coord(size)
        xp0, yp0 = pos.x(), pos.y()
        xp1 = xp0 + size.x()
        yp1 = yp0 + size.y()
        xp0, yp0, xp1, yp1 = (int(np.ceil(v)) for v in [xp0, yp0, xp1, yp1])
        mapslice = np.s_[xp0:xp1, yp0:yp1]
        try:
            oids = self._oid_map[mapslice]
        except TypeError:
            oids = []
        oids = [oid for oid in np.unique(oids) if oid != 0]
        mod = {
            'oids': oids,
            'mapslice': mapslice,
        }
        return mod

    def customEvent(self, event):
        if event == ReposUpdated:
            self.update_repos(event.repos,
                              wipe=event.wipe,
                              roi=event.roi)
            event.accept()
        elif event == ModifyResReq:
            if event.res_type == 'obj.tag':
                if event.modification['objid'] <= 0:
                    event.accept()
                else:
                    event.ignore()
        elif event == ModifyView:
            if event.mod_type == 'oid.part':
                self.update_view(event.modification)
                event.accept()
            elif event.mod_type == 'sync':
                self.set_cursor_info(self._active_view, *self._last_px, show_obj=True)
                event.accept()
            else:
                msg = 'Unknown type for ModifyView event: {}'
                self.log.error(msg.format(event.mod_type))
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

    def get_oid(self, xpos, ypos):
        x, y = int(np.ceil(xpos)), int(np.ceil(ypos))
        try:
            oid = self._oid_map[x, y]
        except (TypeError, IndexError):
            oid = None
        return oid

    def set_cursor_info(self, view, x, y, show_obj=False):
        oid = self.get_oid(x, y)
        tags = []

        try:
            obj = self.get_object(oid)
        except KeyError:
            obj = None

        if obj is None or not show_obj:
            view.set_cursor_info(None, [])
            return

        tags = list(obj.tags)[::-1]
        tags.sort()
        scalar_tags = _scalars_to_tags(obj)
        scalar_tags.sort()
        tags = tags + scalar_tags

        view.set_cursor_info(oid, tags)

    def mouseMoveEvent(self, event):
        ch_coords = None

        self._last_px = None
        self._active_view = None
        for cur_view in self.views.values():
            view_rect = cur_view.boundingRect()
            view_coords = cur_view.mapFromParent(event.pos())
            if view_rect.contains(view_coords):
                bg_coord = cur_view.get_bg_coord(view_coords)
                xpos, ypos = bg_coord.x(), bg_coord.y()
                self._active_view = cur_view
                self._last_px = xpos, ypos
                break

        if not self._last_px is None:
            ch_point = qc.QPointF(*self._last_px)
            for cur_view in self.views.values():
                cur_view.set_crosshair(ch_point)
                show = cur_view is self._active_view
                self.set_cursor_info(cur_view, *self._last_px, show_obj=show)

        event.ignore()
        super().mouseMoveEvent(event)

    def update_repos(self, repo_update, wipe=False, roi=False):
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
        self.views[(0, 0)].show_roi(roi)
        self.get_objid_map()

    def update_view(self, mapslice):
        # just distributing the event to all views
        for cur_view in self.views.values():
            cur_view.redraw(mapslice)

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

    def keyPressEvent(self, event):
        #TODO remove this hack
        if self._active_view is None:
            return

        has_roi = not self._active_view.roi is None

        if event.key() == qc.Qt.Key_Plus or event.key() == qc.Qt.Key_Minus:
            event.accept()
            xpos, ypos = self._last_px
            oid = self.get_oid(xpos, ypos)
            if event.key() == qc.Qt.Key_Plus:
                operand = 1
            else:
                operand = -1
            img_name = self._active_view.last_loaded['bg']
            mod = {'objid': oid,
                   'img_name': img_name,
                   'operand': operand
                  }
            mod_scalar = ModifyResReq(
                res_type='obj.scalar',
                modification=mod)
            qc.QCoreApplication.postEvent(self.parent(), mod_scalar)
        elif event.key() == qc.Qt.Key_H:
            self._active_view.fit_to_images()
            event.accept()
        elif event.key() == qc.Qt.Key_R and has_roi:
            event.accept()
            mod = self._remap_roi(self._active_view.roi)
            merge_event = ModifyResReq(
                res_type='obj.reduce',
                modification=mod)
            qc.QCoreApplication.postEvent(self.parent(), merge_event)
        elif event.key() == qc.Qt.Key_M and has_roi:
            event.accept()
            mod = self._remap_roi(self._active_view.roi)
            merge_event = ModifyResReq(
                res_type='obj.merge',
                modification=mod)
            qc.QCoreApplication.postEvent(self.parent(), merge_event)
        elif event.key() == qc.Qt.Key_D:
            if self._last_px is None:
                return
            xpos, ypos = self._last_px
            oid = self.get_oid(xpos, ypos)
            del_event = ModifyResReq(
                res_type='obj.delete',
                modification=oid)
            qc.QCoreApplication.postEvent(self.parent(), del_event)
        elif event.key() == qc.Qt.Key_C:
            if self._last_px is None:
                return
            ypos, xpos = self._last_px
            mk_event = ModifyResReq(
                res_type='obj.create',
                modification=(xpos, ypos))
            qc.QCoreApplication.postEvent(self.parent(), mk_event)
        elif event.key() == qc.Qt.Key_F and has_roi:
            if self._last_px is None:
                return
            xpos, ypos = self._last_px
            self._active_view.roi.setPos(xpos, ypos)
        else:
            event.ignore()

def _scalars_to_tags(obj):
    """Convert all scalars in an object to tags
    """
    scalar_tags = []
    for scalar_name, value in obj.scalars.items():
        if value > 0:
            sign = '+'
        elif value < 0:
            sign = '-'
        else:
            continue
        value = abs(value)
        if value > 3:
            mag = '{}{}{}'.format(sign, value - 2, sign)
        else:
            mag = sign * value
        scalar_tags.append(scalar_name + mag)
    return scalar_tags


