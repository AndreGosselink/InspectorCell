"""testapp for the SceneViews
"""

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui as qg, QtCore as qc

from sceneview import SceneViewer
from res import Poly


imgdata0 = np.random.uniform(0, 0xfff, 512*512)
imgdata0 = imgdata0.reshape(512, 512).astype(np.uint16)

imgdata1 = np.random.uniform(0, 0xfff, 512*512)
imgdata1 = imgdata1.reshape(512, 512).astype(np.uint16)

imgdata1[170:340, 170:340] *= 2

app = qg.QApplication([])

poly0 = Poly((255, 100, 50))
poly0.setPos((100, 100))

v0 = SceneViewer(useOpenGL=True)
scn = v0.scene()
v0.enableMouse(True)

v1 = SceneViewer(useOpenGL=True)
v1.setScene(scn)
v1.enableMouse(True)

scn.addItem(poly0)

v0.background.setImage(imgdata0)
v1.background.setImage(imgdata1)

v0.show()
v1.show()

print('go!')
app.exec_()
