"""testapp for the SceneViews
"""

import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui as qg, QtCore as qc

from sceneview import SceneViewer
from res import Poly


imgdata0 = np.random.uniform(0, 0xfff, 4096*4096)
imgdata0 = imgdata0.reshape(4096, 4096).astype(np.uint16)

imgdata1 = np.random.uniform(0, 0xfff, 4096*4096)
imgdata1 = imgdata1.reshape(4096, 4096).astype(np.uint16)

imgdata1[170:340, 170:340] *= 2

app = qg.QApplication([])

view = SceneViewer(useOpenGL=True)
view.enableMouse(True)
scene = view.scene()
views = [view]
for i in range(15):
    view = SceneViewer(useOpenGL=True)
    view.enableMouse(True)
    view.setScene(scene)
    views.append(view)
    if i % 2:
        view.background.setImage(imgdata0)
    else:
        view.background.setImage(imgdata1)


for i in range(0, 500, 10):
    for j in range(0, 500, 10):
        poly = Poly((i%255, i%100, 50))
        poly.setPos((i, j))
        scene.addItem(poly)

[v.show() for v in views]

print('go!')
app.exec_()
