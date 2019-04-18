# -*- coding: utf-8 -*-

"""Implements the viewer element. Is completly accessed by teh controller
Holds all gui QtWidget and gui elements
"""
import logging

import AnyQt.QtCore as qc
import AnyQt.QtWidgets as qw

from . import get_logger_name

from .menubar import MainMenuBar
from .propwin import PropWindow
from .viewgrid import ViewGrid

from ..events import (LoadResReq, NewViewProps, ReposUpdated, ErrorEvent,
                      SaveResReq, GenOverlayReq, ModifyResReq)


class DataViewer(qw.QMainWindow):

    # signals/function triggers as outside connection/api
    sig_req_load_imagedir = qc.pyqtSignal(str)
    sig_req_load_imagesel = qc.pyqtSignal(list)
    sig_req_load_objmap = qc.pyqtSignal(str)
    sig_req_load_overlaymaps = qc.pyqtSignal(list)
    sig_req_load_objzip = qc.pyqtSignal(str)
    sig_req_load_objtags = qc.pyqtSignal(str)
    sig_req_save_objzip = qc.pyqtSignal(str)
    sig_req_tag_overlay = qc.pyqtSignal(list, str)
    sig_req_modify_tags = qc.pyqtSignal(list)
    sig_req_modify_objtag = qc.pyqtSignal(int, str)

    def __init__(self, parent=None, logger_domain=None):
        super().__init__(parent=None)

        self.logger_name = get_logger_name(name='DataViewer',
                                           domain=logger_domain)

        self.log = logging.getLogger(self.logger_name)

        self.view_props = {'rows': 2,
                           'cols': 2,
                           'crosshair': False}

        self.setObjectName('SegTool')
        self.resize(800, 600)
        # self.showFullScreen()

        self.build_ui()
        self.connect_ui()

        self.finalize()

    def finalize(self):
        """ calls that need to be make, after everyhing is connected
        """
        self.update_main_view()

    def build_ui(self):
        """Builds all general elements of the main window
        """
        # building the menu bar and status bar of the window
        self.menu_bar = MainMenuBar(parent=self)
        self.setMenuBar(self.menu_bar)
        status_bar = qw.QStatusBar(parent=self)
        self.setStatusBar(status_bar)

        # setting the image viewgrid
        self.viewgrid = ViewGrid(
            parent=self,
            logger_domain=self.logger_name,)
        self.setCentralWidget(self.viewgrid)

    def update_main_view(self):
        self.viewgrid.setup_grid(
            rows=self.view_props['rows'],
            cols=self.view_props['cols'],
            crosshair=self.view_props['crosshair'],)

    def connect_ui(self):
        """Connect end and bits
        """
        self.menu_bar.act_quit_app.triggered.connect(self.close)

    def customEvent(self, event):
        """ routing of my custom events
        used to propagate stuff that happens to the surface
        """
        if event == LoadResReq:
            self.req_load_res(event)
            event.accept()
        elif event == SaveResReq:
            self.req_save_res(event)
            event.accept()
        elif event == NewViewProps:
            self.view_props.update(event.view_props)
            self.update_main_view()
            event.accept()
        elif event == ReposUpdated:
            self.viewgrid.event(event)
            self.menu_bar.event(event)
        elif event == GenOverlayReq:
            self.gen_overlay_req(event)
        elif event == ModifyResReq:
            self.modify_res(event)
        elif event == ErrorEvent:
            self.log.error(event.msg)
            self.statusBar().showMessage(event.msg)
            event.accept()
        else:
            event.ignore()

    def gen_overlay_req(self, event):
        if event.req_type == 'tagmap':
            self.sig_req_tag_overlay.emit(list(event.args), str(event.name))
        else:
            self.log.error('Unknown request type: %s', event.req_type)
        event.accept()

    def modify_res(self, event):
        if event.res_type == 'tags':
            self.sig_req_modify_tags.emit(list(event.modification))
        elif event.res_type == 'obj.tag':
            obj_id = int(event.modification['objid'])
            tag = str(event.modification['tag'])
            self.sig_req_modify_objtag.emit(obj_id, tag)
        else:
            self.log.error('Unknown request type: %s', event.req_type)
        event.accept()

    def req_load_res(self, event):
        if event.res_type == 'img.dir':
            self.sig_req_load_imagedir.emit(event.res_path)
        elif event.res_type == 'img.sel':
            self.sig_req_load_imagesel.emit(event.res_pathes)
        elif event.res_type == 'overlay.map':
            self.sig_req_load_overlaymaps.emit(event.res_pathes)
        elif event.res_type == 'obj.map':
            self.sig_req_load_objmap.emit(event.res_path)
        elif event.res_type == 'obj.zip':
            self.sig_req_load_objzip.emit(event.res_path)
        elif event.res_type == 'obj.tag':
            self.sig_req_load_objtags.emit(event.res_path)
        else:
            self.log.debug('Cant handle {}'.format(event.res_type))
            event.ignore()

    def req_save_res(self, event):
        if event.res_type == 'obj.zip':
            self.sig_req_save_objzip.emit(event.res_path)
