# -*- coding: utf-8 -*-

"""Implements the main viewer element.
"""

import AnyQt.QtCore as qc
import AnyQt.QtWidgets as qw

from viewbox import GridViewBox


class ViewGrid(pg.GraphicsLayoutWidget):
    """Holds and generates the views
    """

    def __init__(self, parent=None, logger_domain=None):
        super().__init__(parent=parent)

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


class DataViewer(qw.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent=None)

        self.view_props = {'rows': 2,
                           'cols': 2,
                           'crosshair': False}

        self.setObjectName('GridViewWidget')

        self.build_ui()
        self.connect_ui()

        self.update_main_view()

    def build_ui(self):
        """Builds all general elements of the main window
        """
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

