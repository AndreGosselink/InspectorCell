"""Implements the adapter bewtween the inspectorcell core and the Orange3 App
"""
### Build-Ins
import os
import sys
from copy import copy, deepcopy
from pathlib import Path
import random

from Orange.widgets.utils.plot import OWButton, OWAction
from AnyQt.QtCore import pyqtSignal, pyqtSlot
from scipy import misc
import numpy as np

from threading import Timer

### Orange and Qt GUI elemetns
from Orange.widgets.visualize.owscatterplotgraph import DiscretizedScale
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.widgets import gui

from Orange.data import (
    Table as OTable, DiscreteVariable, StringVariable, ContinuousVariable,
    Domain, Instance)

from Orange.widgets.settings import (
    Setting, ContextSetting, DomainContextHandler, SettingProvider)

from Orange.widgets.utils.itemmodels import DomainModel
from Orange.widgets.utils.sql import check_sql_input
from Orange.statistics.util import bincount

from AnyQt import QtGui, QtCore, QtWidgets
from AnyQt.QtGui import QColor, QBrush, QPen, QIcon
from AnyQt.QtWidgets import (
    QStyle, QMenu, QSlider, QWidgetAction, QSpinBox, QWidget, QLabel,
    QGridLayout, QFileDialog, QHBoxLayout, QToolButton, QAction)

### Project

if __name__ == '__main__':
    # if run directly, this is propably for debugging reasons and therfor
    # we can assume the directory structure as found in the src dir
    # hence an relative import is needed, to avoid reinstalling all the time
    modpath = Path(__file__, '..', '..', '..', '..').absolute().resolve()
    print(modpath)
    sys.path.insert(0, str(modpath))

from inspectorcell import Controller
from inspectorcell.util import EntityContour
from inspectorcell.util.image import getImagedata


class SelectRadiusWidget(QWidget):
    valueChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent):
        QWidget.__init__(self, parent=parent)
        controlsLayout = QHBoxLayout(self)

        self.radiusSpinboxLabel = QLabel("Brush size:")

        self.radiusSpinbox = QSpinBox(self)
        self.radiusSpinbox.setRange(2, 100)
        self.radiusSpinbox.setValue(10)
        self.radiusSpinbox.setSingleStep(5)
        self.radiusSpinbox.setFixedWidth(50)
        self.radiusSpinbox.valueChanged.connect(self.radiusChanged)

        controlsLayout.addWidget(self.radiusSpinboxLabel)
        controlsLayout.addWidget(self.radiusSpinbox)

    def radiusChanged(self, value):
        self.valueChanged.emit(value)


class OWCellInpspector(OWWidget):
    name = "InspectorCell"
    description = "Randomly selects a subset of instances from the dataset"
    pluginPath = os.path.dirname(__file__)
    icon = os.path.join(pluginPath, 'icons', 'mywidget.svg')
    priority = 10
    penColor = QColor(0, 0, 0, 255)
    penWidth = 1.5
    max_cat = 15

    # # Should the widget construct a mainArea
    # want_main_area = True
    # # Should the widget construct a controlArea.
    # want_control_area = True

    attr_contour = ContextSetting(None)
    attr_eid = ContextSetting(None)
    attr_image = ContextSetting(None)
    autocommit = False

    class Inputs:
        images = Input('Images', OTable)

    # class Outputs:
    #     entities = Output('Entities', OTable)
    #     # selection = Output('Selected Entities', OTable)

    class Error(OWWidget.Error):
        no_valid_contours = Msg("No contours due to no valid data.")

    def __init__(self):
        super().__init__()
        # add on core
        self.controller = Controller()
        self.controller.initViewContext()
        self.controller.viewer.newDrawMode.connect(self._updateDraw)
        self.maskFile = None
        self.entity_data = None

        #TODO depreciated. controller gives signal, or compute only at 'Send'
        # self.controller.viewer.entity_scn.gfxAdded.connect(self.gfxAdd)
        # self.controller.viewer.entity_scn.gfxDeleted.connect(self.gfxDelete)
        # will contain data for entity creation
        self.entity_contours = None
        self.entity_ids = None

        # will be set by gui creation
        self.contour_var = None
        self.eid_var = None
        self.palette = None
        # self.maskFile = None

        self.opacity_var = 100
        self.setup_gui()
        
        self._autosaver = Timer(30, self._autosave)
        self._autosaver.start()

    def _autosave(self):
        self.controller.storeEntities(jsonFile=Path('autosave.ent'))

    def setup_gui(self):
        """Sets mainArea and the controlArea
        """
        # just add the viewer to the mainArea and we are done
        # with it
        mainlayout = self.mainArea.layout()
        mainlayout.addWidget(self.controller.viewer)

        widget = self.controller.viewer  # TestlWidget()
        widget.setGridlayout(2, 2)

        # # FIXME REMOVE AFTER DEBUG!
        # for i in range(2):
        #     for j in range(2):
        #         imdat = np.random.uniform(0, 0xfff, 4096 * 4096)
        #         imdat = imdat.reshape(4096, 4096).astype(np.uint16)
        #         bl0, bl1 = np.random.randint(96, 1024, 2)
        #         bu0, bu1 = np.random.randint(2048, 4000, 2)
        #         imdat[bl0:bu1, bl1:bu1] *= 2
        #         widget.setBackground(index=(i, j), imagedata=imdat,
        #                              name=str((i, j)))

        # widget.show_entities((0, 0))
        # ### REMOVE AFTER DEBUG!

        # and the control area
        # TODO into a seperate class or into a factory function

        self.setup_entity_gui()

        # send selected cells to output
        gui.auto_commit(self.controlArea, self, "autocommit", "Send Selected",
                        "Send Automatically", box=False)

    def setup_entity_gui(self):
        # use pathlib for path building
        pluginPath = Path(OWCellInpspector.pluginPath)
        iconPath = pluginPath / 'icons'

        box_entity = gui.vBox(self.controlArea, True)

        # entity contours
        self.contour_var = DomainModel(placeholder='None', separators=False)
        cb_attr_contour = gui.comboBox(
            box_entity, self, 'attr_contour', label='Contour:',
            model=self.contour_var, callback=self._entities_changed)

        # entity eids
        self.eid_var = DomainModel(placeholder='None', separators=False)
        cb_attr_eid = gui.comboBox(
            box_entity, self, 'attr_eid', label='IDs:', model=self.eid_var,
            callback=self._entities_changed)

        # entity tags
        btn_tag_edit = gui.button(
            box_entity, self, label='Tags...',
            callback=self.controller.viewer.showTagEditDialog)

        #XXX disabled feature
        # btnGenerateContoursFromMask = gui.button(
        #     box_entity,
        #     self,
        #     label='Generate contours from mask',
        #     callback=self._generateContoursFromMask)

        btnGenerateFromJson = gui.button(
            box_entity,
            self,
            label='Load from...',
            callback=self._entityLoad)

        btnDumpToJson = gui.button(
            box_entity,
            self,
            label='Save JSON to...',
            callback=self._jsonSave)

        box_graphics = gui.vBox(self.controlArea, True)
        btn_view_layout = gui.button(box_graphics, self, label='Set Layout',
            callback=self.controller.viewer.showViewSetupDialog)

        # adds opacity
        boxOpacity = gui.hBox(self.controlArea, True)
        slider_opacity = gui.hSlider(
            boxOpacity, self, value='opacity_var', label="Opacity: ",
            minValue=0, maxValue=255, step=5, callback=self._opacity_changed)

        # drawing elements
        boxObjectsEditing = gui.hBox(self.controlArea, "Object editing")

        self.tbGroup = QtGui.QButtonGroup(self)
        self.tbGroup.setExclusive(True)

        self.btnDraw = gui.toolButton(
            boxObjectsEditing, self, label='', callback=self._draw)

        self.btnDraw.setIcon(QIcon(str(iconPath / 'icons8-draw-40.png')))
        self.btnDraw.setToolTip('Draw')

        # set button context menu policy
        self.btnDraw.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.btnDraw.customContextMenuRequested.connect(self.on_context_menu)
        self.btnDraw.setCheckable(True)
        self.tbGroup.addButton(self.btnDraw)

        # create context menu
        self.popMenu = QtGui.QMenu(self)
        radiusSpinbox = SelectRadiusWidget(self)
        radiusSpinbox.valueChanged.connect(self._select_brush_size)

        widgetslider = QWidgetAction(self)
        widgetslider.setDefaultWidget(radiusSpinbox)
        self.popMenu.addAction(widgetslider)

        self.btnErase = gui.toolButton(boxObjectsEditing, self, label='',
            callback=self._erase)
        self.btnErase.setIcon(QIcon(str(iconPath / 'icons8-erase-48.png')))
        self.btnErase.setToolTip('Erase')
        self.btnErase.setCheckable(True)
        self.tbGroup.addButton(self.btnErase)

        btnMergeSelectedObjects = gui.toolButton(
            boxObjectsEditing, self, label='',
            callback=self._merge_selected_objects)

        btnMergeSelectedObjects.setIcon(QIcon(str(iconPath / 'icons8-merge-48.png')))
        btnMergeSelectedObjects.setToolTip('Merge')

        btnDeleteSelectedObjects = gui.toolButton(
            boxObjectsEditing, self, label='',
            callback=self._delete_selected_objects)

        btnDeleteSelectedObjects.setIcon(
            QIcon(str(iconPath / 'icons8-remove-48.png')))
        btnDeleteSelectedObjects.setToolTip('Delete')

        # zoom/select
        boxZoomSelect = gui.hBox(self.controlArea, "Zoom/Select")

        self.tbSelect = gui.toolButton(
            boxZoomSelect, self, label='', callback=self._select_button_clicked)
        self.tbSelect.setIcon(QIcon(str(iconPath / 'Dlg_arrow.png')))
        self.tbSelect.setToolTip('Select')
        self.tbSelect.setCheckable(True)
        self.tbGroup.addButton(self.tbSelect)

        self.tbPan = gui.toolButton(
            boxZoomSelect, self, label='', callback=self._pan_button_clicked)
        self.tbPan.setIcon(QIcon(str(iconPath / 'Dlg_pan_hand.png')))
        self.tbPan.setToolTip('Pan')
        self.tbPan.setCheckable(True)
        self.tbPan.setChecked(True)
        self.tbGroup.addButton(self.tbPan)

        self.tbZoomIn = gui.toolButton(
            boxZoomSelect, self, label='',
            callback=self._zoom_in_button_clicked)

        self.tbZoomIn.setIcon(QIcon(str(iconPath / 'Dlg_zoom_in.png')))
        self.tbZoomIn.setToolTip('Zoom in')

        self.tbZoomOut = gui.toolButton(
            boxZoomSelect, self, label='',
            callback=self._zoom_out_button_clicked)

        self.tbZoomOut.setIcon(QIcon(str(iconPath / 'Dlg_zoom_out.png')))
        self.tbZoomOut.setToolTip('Zoom out')

        self.tbZoomReset = gui.toolButton(
            boxZoomSelect, self, label='',
            callback=self._zoom_reset_button_clicked)

        self.tbZoomReset.setIcon(QIcon(str(iconPath / 'Dlg_zoom_reset.png')))

        self.tbZoomReset.setToolTip('Reset zoom')

        self.tbZoomResetAuto = gui.toolButton(
            boxZoomSelect, self, label='',
            callback=self._zoom_reset_autorange_button_clicked)

        self.tbZoomResetAuto.setIcon(
            QIcon(str(iconPath / 'Dlg_zoom_reset_auto.png')))
        self.tbZoomResetAuto.setToolTip('Reset zoom to autorange')

    def _zoom_in_button_clicked(self):
        self.controller.viewer.zoomIn()

    def _zoom_out_button_clicked(self):
        self.controller.viewer.zoomOut()

    def _zoom_reset_button_clicked(self):
        self.controller.viewer.resetZoom()

    def _zoom_reset_autorange_button_clicked(self):
        self.controller.viewer.resetZoom(autorange=True)

    def _entityLoad(self):
        dlg = QFileDialog(
            self,
            acceptMode=QFileDialog.AcceptOpen,
            fileMode=QFileDialog.ExistingFile
        )
        txtExt = ('.json', '.ent')
        txtGlob = ' '.join(['*{}'.format(ext) for ext in txtExt])

        imgExt = ('.tif', '.tiff', '.png', '.bmp', '.jpg')
        imgGlob = ' '.join(['*{}'.format(ext) for ext in imgExt])

        filters = ['Text ({})'.format(txtGlob), 'Images ({})'.format(imgGlob),
                   'All (*.*)']
        dlg.setNameFilters(filters)

        dlg.selectNameFilter(filters[0])

        if dlg.exec_() != QFileDialog.Accepted:
            # not accepted, return
            return

        try:
            srcfile = Path(dlg.selectedFiles()[0])
        except TypeError:
            # shouldn't happen but who knows what qt does
            return

        if srcfile.exists() and not srcfile.is_dir():
            if srcfile.suffix.lower() in txtExt:
                self.controller.clearEntities()
                self.controller.generateEntities(jsonFile=srcfile)
            elif srcfile.suffix.lower() in imgExt:
                self.controller.clearEntities()
                self.controller.generateEntities(entityMaskPath=srcfile)

    def _jsonSave(self):
        """save entities to json
        """
        jsonfile, _ = QFileDialog.getSaveFileName(
            parent=None,
            caption='Save objects to...',
            # directory=self.last_dir,
            filter='JSON (*.ent)',
        )
        if Path(jsonfile).parent.exists() and jsonfile != '':
            jsonfile = Path(jsonfile)
            if jsonfile.suffix != '.ent':
                jsonfile = jsonfile.with_suffix('.ent')
            self.controller.storeEntities(jsonFile=jsonfile)

    def _select_brush_size(self, value):
        self.controller.viewer.entity_scn.changeRadius(value)

    def _delete_selected_objects(self):
        self.controller.viewer.setMouseMode(self.controller.viewer.PanMode)
        self.tbPan.setChecked(True)
        self.controller.viewer.entity_scn.remove()

    def _merge_selected_objects(self):
        self.controller.viewer.setMouseMode(self.controller.viewer.PanMode)
        self.tbPan.setChecked(True)
        self.controller.viewer.entity_scn.merge()
    
    @pyqtSlot(str)
    def _updateDraw(self, mode):
        self.btnDraw.setChecked(False)
        self.btnErase.setChecked(False)
        self.tbSelect.setChecked(False)
        if mode == 'N':
            self.tbSelect.setChecked(True)
        elif mode == 'E':
            self.btnErase.setChecked(True)
        elif mode == 'D':
            self.btnDraw.setChecked(True)

    def _select_button_clicked(self):
        self.controller.viewer.setDrawMode('N')

    def _pan_button_clicked(self):
        self.controller.viewer.setDrawMode('N')

    def _draw(self):
        self.controller.viewer.setDrawMode('D')

    def _erase(self):
        self.controller.viewer.setDrawMode('E')

    def on_context_menu(self, point):
        # show context menu
        self.popMenu.exec_(self.btnDraw.mapToGlobal(point))

    def _entities_changed(self):
        """Set contour data after user selected
        """
        # no data
        if self.entity_data is None or self.attr_eid is None:
            return

        # TODO: ask user if he sure to change id, contours

        # get data columns from contour data and raise an error
        # if none can be extracted
        entity_contours_str = get_column(self.entity_data, self.attr_contour)
        entity_ids = get_column(self.entity_data, self.attr_eid)
        # no data
        if entity_contours_str is None or entity_ids is None:
            self.Error.clear()
            return

        entity_contours = []
        a_contour = EntityContour()
        try:
            for eid, str_contour in zip(entity_ids, entity_contours_str):
                a_contour.string = str_contour
                entity_contours.append((int(eid), a_contour.contour))
        except (TypeError, IndexError, AttributeError) as err:
            self.Error.no_valid_contours()
            return

        # clear all enteties as we use new dataset now...
        self.controller.clearEntities()

        # set entities with parsed contour data
        self.controller.generateEntities(entityContours=entity_contours)

    def gfxDelete(self, eid):
        if self.entity_data is None or self.attr_eid is None:
            return

        for d in self.entity_data:
            if d[self.attr_eid] == eid:
                d["Active"] = 0
                break

    # def gfxAdd(self, item):
    #     if self.entity_data is None or self.attr_eid is None:
    #         # TODO: if entity_data is none create new domain
    #         return

    #     inst = Instance(self.entity_data.domain)
    #     inst[self.attr_eid] = item.entity.eid
    #     inst["Active"] = 1
    #     a_contour = EntityContour()
    #     a_contour.contour = item.entity.contours
    #     inst[self.attr_contour] = a_contour.string

    def _opacity_changed(self):
        self.controller.viewer.setGlobalOpacity(self.opacity_var)

    # @Inputs.entities
    # @check_sql_input
    # def set_entities(self, entity_data):
    #     """set data domains to select from
    #     """
    #     if entity_data is not None:
    #         # create new orange data table
    #         active = DiscreteVariable("Active", ("No", "Yes"))
    #         my_attributes = []
    #         for attr in entity_data.domain.attributes:
    #             my_attributes.append(attr)
    #         my_attributes.append(active)

    #         domain = Domain(my_attributes, entity_data.domain.class_var,
    #                         metas=entity_data.domain.metas)

    #         #import numpy as np
    #         n = len(entity_data)
    #         X = np.c_[entity_data.X, np.ones(n)]
    #         Y = entity_data.Y

    #         self.entity_data = OTable(domain, X, entity_data.Y,
    #                                   entity_data.metas)

    #         # sets selection options according to contour_data
    #         self.contour_var.set_domain(entity_data.domain)
    #         self.eid_var.set_domain(entity_data.domain)

    def valid_data(self):
        if self.entity_data is None:
            return None

        valid = get_column(self.entity_data, "Active").astype(bool)
        return self.entity_data[valid]

    def getSelectedData(self):
        if len(self.controller.viewer.entity_scn.selectedItems()) == 0:
            return None

        valid_data = self.valid_data()

        if valid_data is None:
            return None

        for selectedItem in self.controller.viewer.entity_scn.selectedItems():
            for vd in valid_data:
                if vd[self.attr_eid] == selectedItem.entity.eid:
                    vd["Selected"] = True
                    break

        selected = get_column(valid_data, "Selected").astype(bool)

        return valid_data[selected]

    @Inputs.images
    @check_sql_input
    def set_images(self, imageData):
        """Informs the controller which images are availabel
        """
        if not imageData is None:
            choices = []
            for inst in imageData:
                # get all variables from table
                name = inst['image name']
                img = inst['image']
                imgDir = img.variable.attributes.get('origin', '')
                # construct path
                imgPath = Path(str(imgDir)) / str(img)
                # if path exists, append it to choices
                if imgPath.exists():
                    choices.append((str(name), imgPath))

            self.controller.setImages(choices)

    def commit(self):
        selected_data = self.getSelectedData()

        if selected_data is None or len(selected_data) == 0:
            self.Outputs.entities.send(self.valid_data())
        else:
            self.Outputs.entities.send(selected_data)

def get_column(dataset, attr):
    #TODO please remove me from premises ;)
    if dataset is None or attr is None:
        return None

    # only use values not sparsity
    values, _ = dataset.get_column_view(attr)
    return values

if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    data = OTable("iris")
    WidgetPreview(OWCellInpspector).run(set_entities=data)
