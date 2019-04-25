# -*- coding: utf-8 -*-
import numpy as np

import AnyQt.QtCore as qc
import AnyQt.QtGui as qg
import AnyQt.QtWidgets as qw

import pyqtgraph as pg

from images import BackgroundImage, ForegroundImage
from templates import get_viewbox_label_html

from events import ErrorEvent, ReposUpdated, ModifyResReq
from enhancer import Enhancer
from crosshair import CrossHair


class MergeROI(pg.RectROI):
    pass

class GridViewBoxLabel(pg.TextItem):

    def __init__(self, *args, **kwargs):
        super().__init__()
        self.cur_text = {'fg': None, 'bg': None, 'misc': None}

    def set_label_text(self, bg_txt=None, fg_txt=None, misc=None,
                       bgcolor='#000000', fgcolor='#10AA00'):

        for new, key in zip((bg_txt, fg_txt, misc), ('bg', 'fg', 'misc')):
            cur = self.cur_text[key]
            if not new is None:
                self.cur_text[key] = new

        bg_txt, fg_txt = self.cur_text['bg'], self.cur_text['fg']
        misc_txt = self.cur_text['misc']
        html_text = get_viewbox_label_html(bg_txt, fg_txt, misc,
                                           bgcolor, fgcolor)
        self.setHtml(html_text)


#TODO make one viewboxmenu for all viewboxes?
class GridViewBoxMenu(qg.QMenu):

    def __init__(self, view=None):
        super().__init__()

        self.view = view
        self.background_images = {}

        bg_menu = self.addMenu('Select &Background...')
        fg_menu = self.addMenu('Select &Foreground...')
        self.addSeparator()
        tag_menu = self.addMenu('Set &Tag...')
        self.addSeparator()
        self.enhance = self.addAction('&Enhance BG...')

        # alpha channel control
        alpha_menu = self.addMenu('&Opacity')
        self.alpha_slider = qw.QSlider()
        self.alpha_slider.setMinimum(0)
        self.alpha_slider.setMaximum(100)
        self.alpha_slider.setSingleStep(1)
        self.alpha_slider.setPageStep(10)
        alpha_action = qg.QWidgetAction(self)
        alpha_action.setDefaultWidget(self.alpha_slider)
        alpha_menu.addAction(alpha_action)
        self.alpha_slider.valueChanged.connect(self._new_alpha)

        self.selectors = {'bg': bg_menu,
                          'fg': fg_menu,
                          'tags': tag_menu,
                         }

        self._tag_selection = set([])

    def update_selection(self, names, layer_name):
        name_selection = set(names)
        try:
            name_selection.remove('None')
        except KeyError:
            pass # non None entry found
        
        name_selection = list(name_selection)
        name_selection.sort()
        name_selection = ['None'] + name_selection

        if layer_name in ('fg', 'bg'):
            self._set_image_selector(name_selection, layer_name)
        elif layer_name == 'tags':
            self._tag_selection = name_selection
            # self._set_tag_selector(name_selection, layer_name)

    def _set_image_selector(self, names, layer_name):
        selector = self.selectors[layer_name]
        selector.clear()
        for a_name in names:
            new_action = selector.addAction(
                a_name, self.trig_dat_loading)
            # used in the trigger to ask for correct image to load
            new_action.callback_info = a_name, layer_name

    def update(self):
        self._set_tag_selector()

    def _set_tag_selector(self):
        selector = self.selectors['tags']
        selector.clear()
        if self.view.over_object <= 0:
            return
        for a_name in self._tag_selection:
            new_action = selector.addAction(
                a_name, self.trig_tag_setting)
            # used in the trigger to ask for correct image to load
            new_action.callback_info = a_name

    def _new_alpha(self):
        new_alpha = self.alpha_slider.value()
        self.view.set_alpha(new_alpha / 100.0)

    @qc.pyqtSlot()
    def trig_dat_loading(self):
        name, layer = self.sender().callback_info
        self.view.load_image(name, layer)

    @qc.pyqtSlot()
    def trig_tag_setting(self):
        tag = self.sender().callback_info
        self.view.update_tag(tag)


class GridViewBox(pg.ViewBox):

    def __init__(self, default_label='N/A', grid=None, drawable=False,
                 parent=None, enhance_callback=None):
        """ Class implementing the drawing handling
        """
        super().__init__(invertY=True, parent=parent, lockAspect=True)

        self.disableAutoRange()

        self.default_label = default_label

        self.paning_btn = qc.Qt.RightButton
        self.draw_btn = qc.Qt.LeftButton
        self.context_btn = qc.Qt.RightButton

        # containing ViewGrid
        self.grid = grid
        self.roi = None

        # callbacks for the layers
        #TODO really store the repos on one point in the app
        # and let the layer data point to it only
        self.layer_data = {'bg': {'img': None, 'rep': {}},
                           'fg': {'img': None, 'rep': {}},
                           }

        self.last_loaded = {'bg': 'None',
                            'fg': 'None',}

        # image label
        self.imagelabel = GridViewBoxLabel()
        self.addItem(self.imagelabel)
        self.imagelabel.setZValue(10)

        self.drawable = drawable

        self.over_object = -1
        self.clicked_object = -1

        self._enhance_callback = enhance_callback

        # if drawable:
        #     self.overlay_image = DrawOverlayImage()
        # else:
        #     self.overlay_image = OverlayImage()
        # self.addItem(self.overlay_image)

        # context menu
        self.setMenuEnabled()
        self.menu = GridViewBoxMenu(view=self)
        self.menu.enhance.triggered.connect(self.req_enhancment)

        # preprocessing pipeline
        self.enhancer = Enhancer()
        self.enhancing = False

        # crosshair
        self.crosshair = CrossHair()
        # self.crosshair = Line()
        self.addItem(self.crosshair)
        self.crosshair.setZValue(9)

    def set_alpha(self, value):
        image = self.layer_data['fg']['img']
        if not image is None:
            image.setOpacity(value)
        else:
            err = ErrorEvent(msg='Could not set alpha: no foreground loaded!')
            qc.QCoreApplication.postEvent(self.grid, err)

    def fit_to_images(self):
        image_items = [layer['img'] for layer in self.layer_data.values()]
        self.autoRange(padding=0, items=image_items)

    def update_repos(self, new_repos):
        """distrobuting the good news
        """
        for layer_name in ('fg', 'bg'):
            new_repo = new_repos[layer_name]
            layer = self.layer_data[layer_name]
            layer['rep'] = new_repo
            new_selection = layer['rep'].keys()
            self.menu.update_selection(new_selection, layer_name)

        tag_callback = new_repos['tags']
        self.update_tag_selection(*tag_callback())

    def update_tag_selection(self, obj_tags, custom_tags):
        tag_selection = list(obj_tags.union(custom_tags))
        self.menu.update_selection(tag_selection, 'tags')

    def update_tag(self, tag):
        mod = {'tag': tag,
               'objid': self.clicked_object,}
        mod_res = ModifyResReq(res_type='obj.tag', modification=mod)
        qc.QCoreApplication.postEvent(self.grid, mod_res)

    def set_image(self, img_data, layer):
        """ Sets the background of the view
        """
        img_classes = {'bg': BackgroundImage, 'fg': ForegroundImage,}
        layer_z = {'bg': 0, 'fg': 1,}

        img = self.layer_data[layer]['img']
        if img is None:
            ImgClass = img_classes[layer]
            img = self.layer_data[layer]['img'] = ImgClass(parent=self)
            self.addItem(img)

        img.setImage(img_data)
        img.setZValue(layer_z[layer])

        if layer == 'bg' and self.enhancing:
            img.setLookupTable(self.enhancer.get_scaling_lut(),
                               update=True)
        if layer == 'fg':
            self.set_alpha(0.3)
            self.menu.alpha_slider.setValue(30)

        if self.grid.just_loaded:
            self.fit_to_images()

    def set_crosshair(self, coords):
        self.crosshair.setPos(coords)

    def set_cursor_info(self, obj_id=None, tags=[]):
        if obj_id is None:
            self.imagelabel.set_label_text(None, None, '')
            self.over_object = -1
        else:
            tag_text = ', '.join(tags)
            # pos_text = self.imagelabel.cur_text['misc']
            pos_text = ' ObjID: {} | Tags: {}'.format(obj_id, tag_text)
            self.imagelabel.set_label_text(None, None, pos_text)
            self.over_object = obj_id

    def get_bg_coord(self, pos):
        bg = self.layer_data['bg']['img']
        bg_coord = self.mapToItem(bg, pos)
        return bg_coord

    def _fetch_image(self, img_name, layer):
        layer_repo = self.layer_data[layer]['rep']
        callback = layer_repo.get(img_name, None)
        try:
            ret = callback()
        except (TypeError, ValueError) as err:
            msg = 'Could not fetch image {} for {}: {}'
            self.post_error(msg.format(img_name, layer, str(err)))
            ret = None
        return ret

    def _update_image(self, img_name, layer):
        self.set_label(**{layer: img_name})# hacky...
        self.last_loaded[layer] = img_name

    def load_image(self, img_name, layer):
        img = self._fetch_image(img_name, layer)
        if not img is None:
            self.set_image(img, layer)
            self._update_image(img_name, layer)

    def set_label(self, bg=None, fg=None, bgcolor='#000000',
                  fgcolor='#10AA00'):
        """Sets the label
        """
        self.imagelabel.set_label_text(bg, fg, bgcolor=bgcolor, fgcolor=fgcolor)

    def wipe_images(self):
        """Clears everything
        """
        self.set_label(self.default_label)
        for layer in ('fg', 'bg'):
            layer_repo = self.layer_data[layer]['rep']
            try:
                blank_callback = layer_repo['None']
                self.set_image(blank_callback(), layer)
            except (KeyError, AttributeError):
                pass # nothing to wipe then

    def post_error(self, msg):
        err = ErrorEvent(msg)
        qc.QCoreApplication.postEvent(self.grid, err)

    def setRange(self, *args, **kwargs):
        super().setRange(*args, **kwargs)
        (new_x, _), (new_y, _) = self.state['viewRange']
        self.imagelabel.setPos(new_x, new_y)

    def redraw(self, mapslice):
        #TODO use signaling here
        layer = 'fg'
        if self.last_loaded[layer] == 'None':
            return
        img_name = self.last_loaded[layer]

        cur_opacity = self.layer_data[layer]['img'].opacity()
        img = self._fetch_image(img_name, layer)
        if not img is None:
            self.set_image(img, layer)
        self.layer_data[layer]['img'].setOpacity(cur_opacity)

    @qc.pyqtSlot()
    def req_enhancment(self):
        self.enhancing = True
        if not self._enhance_callback is None:
            self._enhance_callback(self)

    def mouseDragEvent(self, event):
        # paning and scaling, pass the drawing button
        if event.button() & self.paning_btn:
            self._pan_view(event)
            event.accept()

    def _pan_view(self, ev):
        pos = ev.pos()
        lastPos = ev.lastPos()
        dif = pos - lastPos
        dif = dif * -1

        ## Ignore axes if mouse is disabled
        mask = np.array([1.0, 1.0], dtype=float)

        # paning
        if self.state['mouseMode'] == pg.ViewBox.RectMode:
            # This is the final move in the drag; changethe view scale now
            if ev.isFinish():
                # print "finish"
                self.rbScaleBox.hide()
                p0, p1 = pg.Point(ev.buttonDownPos(ev.button())), pg.Point(pos)
                ax = qc.QRectF(p0, p1)
                ax = self.childGroup.mapRectFromParent(ax)
                self.showAxRect(ax)
                self.axHistoryPointer += 1
                self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
            else:
                ## update shape of scale box
                self.updateScaleBox(ev.buttonDownPos(), ev.pos())
        else:
            tr = dif * mask
            tr = self.mapToView(tr) - self.mapToView(pg.Point(0,0))
            x = tr.x() if mask[0] == 1 else None
            y = tr.y() if mask[1] == 1 else None

            self._resetTarget()
            if x is not None or y is not None:
                self.translateBy(x=x, y=y)
            self.sigRangeChangedManually.emit(self.state['mouseEnabled'])

    def mouseClickEvent(self, event):
        if event.button() == self.context_btn:
            self.menu.update()
            self.raiseContextMenu(event)
            self.clicked_object = self.over_object
            event.ignore()

    def customEvent(self, event):
        if event == ReposUpdated:
            self.update_repos(event)
            event.accept()
        else:
            event.ignore()

    def show_roi(self, show=False):
        if self.roi is None:
            self.roi = MergeROI(
                [0, 0], size=[20, 20], angle=0.0, invertible=False,
                maxBounds=None, snapSize=1.0, scaleSnap=False,
                translateSnap=False, rotateSnap=False, parent=None,
                pen=(0, 9), movable=True, removable=False)
            self.roi.setZValue(9)
            self.roi.grid = self.grid
            self.addItem(self.roi)
        self.roi.setVisible(show)

    @property
    def tag_selection(self):
        return self.menu._tag_selection.copy()
