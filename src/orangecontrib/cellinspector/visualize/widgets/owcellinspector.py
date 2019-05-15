import os
import sys
from pathlib import Path

from AnyQt import QtGui, QtCore, QtWidgets
import AnyQt.QtCore as qc
import AnyQt.QtWidgets as qw

import logging
from Orange.widgets.utils.sql import check_sql_input

from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets.settings import (
    Setting, ContextSetting, DomainContextHandler,
    SettingProvider)

from AnyQt.QtWidgets import (QGraphicsScene, QGraphicsView)

from Orange.data import Table

if __name__ is '__main__':
    # if run directly, this is propably for debugging reasons and therfor
    # we can assume the directory structure as found in the src dir
    # hence an relative import is needed, to avoid reinstalling all the time
    from importlib.util import module_from_spec, spec_from_file_location
    from pathlib import Path

    modname = 'cellinspector'
    modpath = str(Path('../../../cellinspector').absolute())
    modspec = spec_from_file_location(modname,
                                      modpath)
    if modspec is None:
        raise ValueError('Could not load ' + modname)

    cellinspector = module_from_spec(modspec)
    modspec.loader.exec_module(mod)
    Controller = getattr(cellinspector, 'Controller')
else:
    from cellinspector import Controller


class OWCellInpspector(OWWidget):
    name = "CellInspector"
    icon = "icons/mywidget.svg"
    keywords = []

    class Inputs:
        data = Input("Data", Table, default=True)

    class Outputs:
        selected_data = Output("Selected Data", Table, default=True)
        data = Output("Data", Table, default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # instanziate the controller
        self._ciCtrl = Controller()
        # set the viewer as main widget
        self.mainArea.layout().addWidget(self._ciCtrl.viewer)

        self._ciCtrl.viewer.setGridlayout(2, 2)

    @Inputs.data
    @check_sql_input
    def set_data(self, data):
        self.closeContext()
        self.data = data
        self.valid_data = None

    def _on_attr_contour_changed(self):

        if self.data is None:
            return

    def _on_attr_label_changed(self):
        if self.data is None:
            return
        self.update_labels()

    def _on_attr_color_changed(self):
        if self.data is None:
            return
        self._on_attr_contour_changed()

    def onDeleteWidget(self):
        super().onDeleteWidget()


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    data = Table("iris")
    WidgetPreview(OWCellInpspector).run()
