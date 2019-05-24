from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPolygonF, QPainterPath
import csv

from pyqtgraph.Qt import QtGui as qg, QtCore as qc

import pyqtgraph as pg
import numpy as np

from pathlib import Path
rootPath = Path(__file__) / '..' / '..' / '..' / '..'
rootPath = rootPath.absolute().resolve()

if __name__ == '__main__':
    # if run directly, this is propably for debugging reasons and therfor
    # we can assume the directory structure as found in the src dir
    # hence an relative import is needed, to avoid reinstalling all the time
    import sys

    modpath = rootPath / 'src'
    sys.path.insert(0, str(modpath))  

from cellinspector import Controller
from cellinspector.viewer import Viewer
from cellinspector.graphics import GFX

# Initializing Qt
app = QtGui.QApplication([])

controller = Controller()
# Create a top-level widget to hold everything
widget = controller.viewer

widget.set_gridlayout(2, 2)
for i in range(2):
    for j in range(2):
        imdat = np.random.uniform(0, 0xfff, 4096 * 4096)
        imdat = imdat.reshape(4096, 4096).astype(np.uint16)
        bl0, bl1 = np.random.randint(96, 1024, 2)
        bu0, bu1 = np.random.randint(2048, 4000, 2)
        imdat[bl0:bu1, bl1:bu1] *= 2

        widget.set_background((i, j), imdat)

# read contours from file
contoursFile = rootPath / 'res' / 'contourtest.csv'
numberOfShowedObjects = 300
with contoursFile.open('r') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for lines in csv_reader:

        if numberOfShowedObjects == 0:
            break

        polygon = QPolygonF()
        coordinates = lines[2].split(" ")

        for c in coordinates:
            pos = c.split(",")
            if len(pos) == 2:
                polygon << QPointF(float(pos[0]), float(pos[1]))
        if not polygon.isEmpty():
            newEntity = controller.entityManager.make_entity()
            newEntity.from_polygons([polygon])
            gfx = newEntity.makeGFX()
            widget.add_item(gfx)
            numberOfShowedObjects = numberOfShowedObjects - 1

print("csv data is imported")

# Display objects in view 0,0
widget.show_entities((0,0))

# Display the widget as a new window
widget.show()

# Start the Qt event loop
app.exec_()
