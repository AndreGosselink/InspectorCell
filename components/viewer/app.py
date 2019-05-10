# -*- coding: utf-8 -*-

# built-ins
import random
import sys

# GUI stuff
import pyqtgraph as pg
from AnyQt.QtGui import QPen, QColor
from AnyQt import QtGui as qg, QtCore as qc, QtWidgets as qw

# extern dependencies
import numpy as np

# project
from viewer import Viewer


app = qw.QApplication([])

viewer = Viewer()
viewer.set_gridlayout(2, 2)

for i in range(2):
    for j in range(2):
        imdat = np.random.uniform(0, 0xfff, 4096*4096)
        imdat = imdat.reshape(4096, 4096).astype(np.uint16)
        bl0, bl1 = np.random.randint(96, 1024, 2)
        bu0, bu1 = np.random.randint(2048, 4000, 2)
        imdat[bl0:bu1, bl1:bu1] *= 2

        viewer.set_background((i, j), imdat)

viewer.widget.show()

sys.exit(app.exec())
