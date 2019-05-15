import os
import sys

# from AnyQt import QtGui, QtCore, QtWidgets
# import AnyQt.QtCore as qc
# import AnyQt.QtWidgets as qw

# from Orange.widgets.utils.sql import check_sql_input

from Orange.widgets.widget import OWWidget, Input, Output
from Orange.widgets import gui
from Orange.data import Table as OTable
# from Orange.widgets.settings import (
#     Setting, ContextSetting, DomainContextHandler,
#     SettingProvider)

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

    class Inputs:
        data = Input("Data", OTable)

    class Outputs:
        sample = Output("Sampled Data", OTable)

    want_main_area = False

    def __init__(self):
        super().__init__()

        # GUI
        box = gui.widgetBox(self.controlArea, "Info")
        self.infoa = gui.widgetLabel(box, 'No data on input yet, waiting to get something.')
        self.infob = gui.widgetLabel(box, '')

    @Inputs.data
    def setData(self, dataset):
        if dataset is not None:
            self.infoa.setText('%d instances in input dataset' % len(dataset))
            indices = np.random.permutation(len(dataset))
            indices = indices[:int(np.ceil(len(dataset) * 0.1))]
            sample = dataset[indices]
            self.infob.setText('%d sampled instances' % len(sample))
            self.Outputs.sample.send(sample)
        else:
            self.infoa.setText('No data on input yet, waiting to get something.')
            self.infob.setText('')
            self.Outputs.sample.send("Sampled Data")


if __name__ == "__main__":
    from Orange.widgets.utils.widgetpreview import WidgetPreview

    data = OTable("iris")
    WidgetPreview(OWCellInpspector).run(setData=data)
