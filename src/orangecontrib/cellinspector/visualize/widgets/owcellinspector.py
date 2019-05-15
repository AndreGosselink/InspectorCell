import os
import sys

# from AnyQt import QtGui, QtCore, QtWidgets
# import AnyQt.QtCore as qc
# import AnyQt.QtWidgets as qw

# from Orange.widgets.utils.sql import check_sql_input

from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from Orange.data import Table as OTable
from Orange.widgets.settings import (
    Setting, ContextSetting, DomainContextHandler,
    SettingProvider)

from Orange.widgets.utils.itemmodels import DomainModel

import numpy as np

try:
    from cellinspector import Controller
except ImportError as err:
    if __name__ == '__main__':
        # if run directly, this is propably for debugging reasons and therfor
        # we can assume the directory structure as found in the src dir
        # hence an relative import is needed, to avoid reinstalling all the time
        from pathlib import Path
        import sys

        modpath = Path('../../../../').absolute().resolve()
        sys.path.insert(0, str(modpath))  
    else:
        raise err

    from cellinspector import Controller




class OWCellInpspector(OWWidget):
    name = "Data Sampler"
    description = "Randomly selects a subset of instances from the dataset"
    icon = "icons/DataSamplerA.svg"
    priority = 10

    # # Should the widget construct a mainArea
    # want_main_area = True
    # # Should the widget construct a controlArea.
    # want_control_area = True

    settingsHandler = DomainContextHandler()
    attr_contour = ContextSetting(None)
    attr_label = ContextSetting(None)
    attr_color = ContextSetting(None)
    selection = Setting(None, schema_only=True)
    show_legend = False
    background_image_enabled = False
    # too_many_labels = Signal(bool)
    graph_name = "scene"
    autocommit = False

    class Inputs:
        data = Input("Data", OTable)

    class Outputs:
        sample = Output("Sampled Data", OTable)

    def __init__(self):
        super().__init__()
        
        self.controller = Controller()
        self.controller.viewer.setGridlayout(2, 2)
        self.scene = self.controller.viewer.entity_scn

        # self.settingsHandler = DomainContextHandler()
        # self.attr_contour = ContextSetting(None)
        # self.attr_label = ContextSetting(None)
        # self.attr_color = ContextSetting(None)
        # self.selection = Setting(None, schema_only=True)
        # self.show_legend = False
        self.background_image_enabled = False
        # # self.too_many_labels = Signal(bool)
        # self.graph_name = "scene"
        # self.autocommit = False
        
        #TODO cleanup
        self.data = None
        self.contours = None
        self.legend = None
        self.n_contours = 0
        self.subset_is_shown = False
        self.alpha_value = 50
        self.zoom_value = 250
        self.label_only_selection = False
        self.bg_image_filename = ""
        self.bg_image = None
        self.setup_gui()
        self.labels = []
        self._too_many_labels = False

        self.setup_gui()

    def setup_gui(self):
        """Sets mainArea and the controlArea
        """
        # just add the viewer to the mainArea and we are done
        # with it
        mainlayout = self.mainArea.layout()
        mainlayout.addWidget(self.controller.viewer)
        
        # and the control area
        #TODO into a seperate class or into a factory function
        layout = gui.vBox(self.controlArea, True)
        self.contour_var = DomainModel(
            placeholder="None", separators=False)
        self.label_var = DomainModel(
            placeholder="None", separators=False)
        self.color_var = DomainModel(
            placeholder="None", separators=False)
        cb_attr_contour = gui.comboBox(
            layout, self, "attr_contour", label="Contour:",
            model=self.contour_var, callback=self._on_attr_contour_changed)
        cb_attr_color = gui.comboBox(
            layout, self, "attr_color", label="Color:",
            model=self.color_var, callback=self._on_attr_color_changed)
        cb_attr_label = gui.comboBox(
            layout, self, "attr_label", label="Label:",
            model=self.label_var, callback=self._on_attr_label_changed)
        chb_label = gui.checkBox(
            layout, self, "label_only_selection", label="Label only selection",
            callback=self.update_labels)
        chb_show_legend = gui.checkBox(
            layout, self, "show_legend", label="Show legend", callback=self.update_legend_visibility)
        box_bgImg = gui.vBox(self.controlArea, True)
        chb_bgImg = gui.checkBox(
            box_bgImg, self, "background_image_enabled", label="Show background",
            callback=self._bg_image_enabled)
        # icon_open_dir = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        # self.btnBrowseBgImage = gui.button(box_bgImg, self, label="Fluorescent image", icon=icon_open_dir,
        #                                    callback=self.browse_bg_image)
        # self.btnBrowseBgImage.setEnabled(False)
        # self.cb_bgImg = gui.lineEdit(box_bgImg, self, "bg_image_filename")
        # self.cb_bgImg.setEnabled(False)
        gui.rubber(layout)
        box_opacity = gui.vBox(self.controlArea, True)
        slider_opacity = gui.hSlider(box_opacity, self, value='alpha_value', label="Opacity: ", minValue=0,
                                     maxValue=255, step=5, callback=self._opacity_changed)
        box_zoom = gui.hBox(self.controlArea, True)
        slider_zoom = gui.hSlider(box_zoom, self, value='zoom_value', label="Zoom: ", minValue=0,
                                  maxValue=500, step=6, callback=self._zoom_changed)


        gui.auto_commit(self.controlArea, self, "autocommit", "Send Selected", "Send Automatically",
                        box=False)

    def _on_attr_color_changed(self, *args, **kwargs):
        print(args, kwargs)

    def _on_attr_label_changed(self, *args, **kwargs):
        print(args, kwargs)

    def label_only_selection(self, *args, **kwargs):
        print(args, kwargs)

    def update_labels(self, *args, **kwargs):
        print(args, kwargs)

    def browse_bg_image(self, *args, **kwargs):
        print(args, kwargs)

    def update_legend_visibility(self, *args, **kwargs):
        print(args, kwargs)

    def _opacity_changed(self, *args, **kwargs):
        print(args, kwargs)

    def _zoom_changed(self, *args, **kwargs):
        print(args, kwargs)

    def _on_attr_contour_changed(self, *args, **kwargs):
        print(args, kwargs)

    def _bg_image_enabled(self, *args, **kwargs):
        print(args, kwargs)
        
    @Inputs.data
    def setData(self, dataset):
        if dataset is not None:
            indices = np.random.permutation(len(dataset))
            indices = indices[:int(np.ceil(len(dataset) * 0.1))]
            sample = dataset[indices]
            self.Outputs.sample.send(sample)
        else:
            self.Outputs.sample.send("Sampled Data")

    def commit(self):
        if self.data is not None:
            ids = []
            for c in self.contours:
                if c._selected:
                    ids.append(c.id)
                    self.data[c.id]["Selected"] = True
                else:
                    self.data[c.id]["Selected"] = False
            print(ids)
            self.Outputs.selected_data.send(self.data[ids])
            self.Outputs.data.send(self.data)
        else:
            self.Outputs.selected_data.send(None)
            self.Outputs.data.send(None)


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    data = OTable("iris")
    WidgetPreview(OWCellInpspector).run(setData=data)
