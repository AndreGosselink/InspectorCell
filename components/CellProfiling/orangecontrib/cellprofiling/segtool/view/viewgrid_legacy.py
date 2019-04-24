# -*- coding: utf-8 -*-

import re
import warnings
import logging

import PyQt5.QtCore as qc
# import Qt, pyqtSignal, pyqtSlot, QRectF, QPointF
import PyQt5.QtGui as qg
#import QKeyEvent

import pyqtgraph as pg

import numpy as np


from .components import SegmentViewBox
from ....logutil import get_logger_name


class ViewGrid(pg.GraphicsLayoutWidget):
    """ImageContainer holding ImageItem and all data in the current MICS stack
    optimized for 16 bit and with patched drawing capabilities
    """

    sig_tags_changed = qc.pyqtSignal(list)

    def __init__(self, logger_domain=None):
        #TODO image stack always initialized with parameter
        # (can be overwritten, though)
        super().__init__()

        self.logger_name = get_logger_name(name='ViewGrid',
                                           domain=logger_domain)
        self.log = logging.getLogger(self.logger_name)
        self.log.setLevel(logging.INFO)

        # ViewBox
        self.grid_layout = None

        # self._tags = []

        # self._keymap = {Qt.Key_N: {'help': 'Next Object Id',
        #     'func': self._focus_next_oid},
        #         }

    def setup_grid(self, rows, cols):

        # generate MainViewBox
        mainview = SegmentViewBox(drawable=False)
        self._connect_mainview(mainview)
        self.views['main'] = mainview

        # generate ViewBoxes
        for r in range(rows):
            for c in range(cols):
                self.views[r, c] = SegmentViewBox(drawable=False)

        for idx, vw in self.views.items():
            if idx == 'main':
                self.addItem(vw, row=0, col=0, rowspan=mainview_span,
                    colspan=mainview_span)
            else:
                r, c = idx
                self.addItem(vw, row=r, col=c+mainview_span, rowspan=1,
                    colspan=1)

        if not self.image_stack is None:
            self.set_image_stack(self.image_stack)

    def _connect_mainview(self, mainview):
        # initial tag setting and assignment
        self.sig_tags_changed.connect(mainview.menu.set_tags)
        self.sig_tags_changed.emit(self._tags)
        mainview.menu.sig_tag_assigned.connect(self.set_tag_at)
        # connect trigger for saving/writing
        mainview.menu.sig_save_objects.connect(self.save_objects)
        mainview.menu.sig_load_objects.connect(self.load_objects)
        # connect trigger for view updates
        mainview.sigRangeChanged.connect(self.update_views)

    def set_image_stack(self, image_stack):
        self.image_stack = image_stack

        if self.view_setup is None:
            return

        self.view_setup = self._set_stackindices(self.view_setup,
            self.image_stack)
        self.log.info('skip object overlay rendering!')
        # self.views['main'].overlay_image._get_objid_at = \
        #     self.image_stack.get_oid_at

    # def draw_images(self):
    #     if self.view_setup is None or self.image_stack is None:
    #         raise ValueError('Set image stack and view setup first')

    #     for k, d in list(self.view_setup.items()):
    #         # get params
    #         vb = self.views[k]
    #         idx = d['index']
    #         label = d['label']
    #         label_template = vb.label_template

    #         # set background image
    #         bgimg = self.image_stack.image_data[idx]
    #         vb.background_image.setImage(bgimg)

    #         # set overlay image
    #         oid_map = self.image_stack.oid_map
    #         olimg = self._get_rgba_overlay(oid_map)
    #         vb.overlay_image.setImage(olimg)

    #         # set labels
    #         vb.label.setHtml(label_template.format(label))
    #         vb.label.setColor('10FF00')

    #     # intitialize first view/range
    #     vb = self.views['main']
    #     x1, y1 = self.image_stack.image_data[0].shape
    #     rtup = (0, x1), (0, y1)
    #     vb.setRange(xRange=rtup[0], yRange=rtup[1])
    #     self.update_views(vb, rtup)

    # def _set_stackindices(self, view_setup, image_stack):
    #     vs = view_setup.copy()

    #     for d in vs.values():
    #         rexp = re.compile(d['regex'], re.IGNORECASE)
    #         matches = [rexp.match(n) for n in image_stack.marker_list]

    #         #TODO filter ambigous matches
    #         indices = [not m is None for m in matches]
    #         if not any(indices):
    #             warnings.warn('Pattern {} not found'.format(d['regex']))
    #             idx = 0
    #             label = 'N/A'
    #         else:
    #             idx = int(indices.index(True))
    #             pm = matches[idx]
    #             label = d.get('label', None)
    #             if label is None:
    #                 gr = pm.groups()
    #                 if gr != (): label = gr[0]
    #                 else: label = 'N/A'

    #         d['index'] = idx
    #         d['label'] = label

    #     return vs

    # @pyqtSlot(object, object)
    # def update_views(self, vb, rtup):
    #     ((x0, x1), (y0, y1)) = rtup

    #     # calculate center pixel and pixelPerRange
    #     dx = (x1 - x0)
    #     dy = (y1 - y0)
    #     yc = dy / 2.0 + y0
    #     xc = dx / 2.0 + x0

    #     #TODO DebugMsg?
    #     if vb.width() > 0 and vb.height() > 0:
    #         ppx = dx / vb.width()
    #         ppy = dy / vb.height()
    #     else:
    #         ppx = 1
    #         ppy = 1

    #     # relative distances for labels from viewbox border
    #     lxp = 0.0
    #     lyp = 1.0

    #     # r = self.views['main'].label.boundingRect()
    #     self.views['main'].label.setPos(x0+(dx*lxp), y0+(dy*lyp))

    #     yhs, xhs = self.views[0, 0].height() / 2.0, self.views[0, 0].width() / 2.0

    #     #TODO DebugMsg?
    #     if yhs > 0 and xhs > 0:
    #         yxas = yhs / xhs
    #     else:
    #         yxas = 1

    #     if ppy > ppx:
    #         yhs *= ppy
    #         xhs = yhs / yxas
    #     else:
    #         xhs *= ppx
    #         yhs = xhs * yxas

    #     rows, cols = self.gridlayout
    #     xs0, xs1 = xc-xhs, xc+xhs
    #     ys0, ys1 = yc-yhs, yc+yhs
    #     for r in range(rows):
    #         for c in range(cols):
    #             sv = self.views[r, c]
    #             sv.setRange(xRange=(xs0, xs1), yRange=(ys0, ys1))
    #             sv.label.setPos(xs0+(xhs*lxp*2), ys0+(yhs*lyp*2))

    # def _focus_next_oid(self):
    #     oids = self.image_stack.oids

    #     if self.in_focus is None:
    #         nxt_oid = oids[0]
    #     else:
    #         cur_idx = oids.index(self.in_focus)
    #         try:
    #             nxt_oid = oids[cur_idx + 1]
    #         except IndexError:
    #             nxt_oid = oids[0]

    #     self.focus_oid(nxt_oid)

    # def focus_oid(self, oid):
    #     oid_mask = self.image_stack.oid_map == oid
    #     x0, x1, y0, y1 = self.get_segbounds(oid_mask)
    #     # percentual width of boundary from segment to img edge
    #     b = 0.01
    #     x0, y0 = (v * (1.0-b) for v in (x0, y0))
    #     # xRange and yRange seem to be halfoben intervalls thus +1
    #     x1, y1 = (v * (1.0+b) for v in (x1+1, y1+1))
    #     self.views['main'].setRange(xRange=(x0, x1), yRange=(y0, y1))
    #     self.in_focus = oid

    # def keyPressEvent(self, event):
    #     if type(event) is QKeyEvent:
    #         handler = self._keymap.get(event.key(), None)
    #         if not handler is None:
    #             handler['func']()
    #         event.accept()
    #     else:
    #         event.ignore()

    # def set_tagselection(self, list_of_tags):
    #     self._tags.clear()
    #     for t in list_of_tags:
    #         self._tags.append(t)
    #     self.sig_tags_changed.emit(self._tags)

    # @pyqtSlot(str)
    # def set_tag_at(self, tag):
    #     pos = self.views['main'].overlay_image._last_rightclick
    #     row, col = np.round(pos).astype(int)
    #     oid = self.image_stack.get_oid_at(row, col)
    #     # self.image_stack.add_tag(oid, tag)
    #     self.image_stack.assign_tag(oid, tag)

    # @pyqtSlot(str)
    # def save_objects(self, fname):
    #     if self.image_stack is None:
    #         raise ValueError('No stack initialized!')
    #     else:
    #         self.image_stack._save_objects(fname)

    # @pyqtSlot(str)
    # def load_objects(self, fname):
    #     if self.image_stack is None:
    #         raise ValueError('No stack initialized!')
    #     else:
    #         self.image_stack._load_objects(fname)
