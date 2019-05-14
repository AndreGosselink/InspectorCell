"""Small standalone script. Can be run to launch the controller in an Qt app
context
"""

import sys

from AnyQt import QtWidgets as qw
import numpy as np

from .control import Controller


def runApp():
    app = qw.QApplication([])
    ctrl = Controller()
    
    ctrl.viewer.setGridlayout(2, 2)
 
    for i in range(2):
        for j in range(2):
            imdat = np.random.uniform(0, 0xfff, 4096*4096)
            imdat = imdat.reshape(4096, 4096).astype(np.uint16)
            bl0, bl1 = np.random.randint(96, 1024, 2)
            bu0, bu1 = np.random.randint(2048, 4000, 2)
            imdat[bl0:bu1, bl1:bu1] *= 2
    
            ctrl.viewer.set_background((i, j), imdat)
    
    ctrl.viewer.show()
    
    sys.exit(app.exec())

