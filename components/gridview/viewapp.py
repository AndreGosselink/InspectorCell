from viewer import Viewer


import random

from AnyQt.QtGui import QPen, QColor
from AnyQt import QtGui as qg, QtCore as qc, QtWidgets as qw

import pyqtgraph as pg
import numpy as np

app = qw.QApplication([])
viewer = Viewer()
viewer.window.show()
viewer.setup_grid(1, 2)

app.exec_()
