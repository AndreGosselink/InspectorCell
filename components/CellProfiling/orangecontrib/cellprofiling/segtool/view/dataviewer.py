# -*- coding: utf-8 -*-

"""Implements the viewer element. Is completly accessed by teh controller
Holds all gui QtWidget and gui elements
"""
import logging
from pathlib import Path
import yaml

import PyQt5.QtCore as qc
import PyQt5.QtWidgets as qw

from . import get_logger_name

from .menubar import MainMenuBar
from .propwin import PropWindow
from .viewgrid import ViewGrid

from ..events import (LoadResReq, NewViewProps, ReposUpdated, ErrorEvent,
                      SaveResReq, GenOverlayReq, ModifyResReq, ModifyView)


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
    sig_req_reduce_obj = qc.pyqtSignal(dict)
    sig_req_merge_obj = qc.pyqtSignal(dict)
    sig_req_delete_obj = qc.pyqtSignal(int)
    sig_req_create_obj = qc.pyqtSignal(tuple)
    sig_req_change_scalar = qc.pyqtSignal(dict)

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
        elif event == ModifyView:
            self.viewgrid.event(event)
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
        elif event.res_type == 'obj.reduce':
            self.sig_req_reduce_obj.emit(event.modification)
        elif event.res_type == 'obj.merge':
            self.sig_req_merge_obj.emit(event.modification)
        elif event.res_type == 'obj.delete':
            self.sig_req_delete_obj.emit(event.modification)
        elif event.res_type == 'obj.create':
            self.sig_req_create_obj.emit(event.modification)
        elif event.res_type == 'obj.scalar':
            self.sig_req_change_scalar.emit(event.modification)
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
        elif event.res_type == 'view.yaml':
            self.load_view_state(event.res_path)
        else:
            self.log.debug('Cant handle {}'.format(event.res_type))
            event.ignore()

    def req_save_res(self, event):
        if event.res_type == 'obj.zip':
            self.sig_req_save_objzip.emit(event.res_path)
        elif event.res_type == 'view.yaml':
            self.save_view_state(event.res_path)

    def save_view_state(self, path):
        path = Path(path)
        grid = self.viewgrid

        state = {
            'layout': list(grid.layout),
            'tag_sel': [],
            'view_setups': [],
        }

        ref_view = grid.views.get((0, 0), None)
        state['tag_sel'] = list(ref_view.tag_selection)
        if not ref_view is None:
            state['range'] = ref_view.viewRange()
        else:
            state['range'] = None

        view_setups = state['view_setups']
        for idx, view in grid.views.items():
            try:
                fg_op = view.layer_data['fg']['img'].opacity()
            except AttributeError:
                fg_op = None
            if view.enhancing is False:
                enhancement = None
            else:
                enhancement = [list(view.enhancer.adjust_from),
                               list(view.enhancer.adjust_to)]
            view_state = {
                'fg': view.last_loaded['fg'],
                'bg': view.last_loaded['bg'],
                'bg_enhance': enhancement,
                'fg_alpha': fg_op,
                'index': list(idx),}
            view_setups.append(view_state)

        with path.open('w') as yml:
            yaml.dump(state, yml)

    def load_view_state(self, path):
        path = Path(path)
        grid = self.viewgrid

        with path.open('r') as yml:
            state = yaml.load(yml)

        cols, rows = state['layout']
        # self.log.debug('restoring layout (%d, %d)', cols, rows)
        grid.setup_grid(cols, rows)
        # self.log.debug('restoring tags %s', str(state['tag_sel']))
        self.sig_req_modify_tags.emit(state['tag_sel'])

        grid.just_loaded = False

        for view_state in state['view_setups']:
            idx = tuple(view_state['index'])
            view = grid.views[idx]

            enhancement = view_state['bg_enhance']
            if not enhancement is None:
                adj_from, adj_to = enhancement
                view.enhancer.adjust_from = adj_from
                view.enhancer.adjust_to = adj_to
                view.enhancing = True
            else:
                view.enhancing = False

            for layer in ('bg', 'fg'):
                img_name = view_state[layer]
                view.load_image(img_name, layer)
            fg_alpha = view_state['fg_alpha']

            if not fg_alpha is None:
                view.set_alpha(fg_alpha)

        vrange = state['range']
        ref_view = grid.views.get((0, 0), None)
        new_xrange, new_yrange = vrange
        ref_view.setRange(
            xRange=new_xrange, yRange=new_yrange, padding=0)
