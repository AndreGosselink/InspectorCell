from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import QRectF, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QPolygonF, QPainterPath
import csv

from pyqtgraph.Qt import QtGui as qg, QtCore as qc

import pyqtgraph as pg
import numpy as np

if __name__ == '__main__':
    # if run directly, this is propably for debugging reasons and therfor
    # we can assume the directory structure as found in the src dir
    # hence an relative import is needed, to avoid reinstalling all the time
    from pathlib import Path
    import sys

    modpath = Path('./src').absolute().resolve()
    sys.path.insert(0, str(modpath))  

from cellinspector import Controller
from cellinspector.viewer import Viewer
from cellinspector.graphics import GFX


class SingleViewBox(pg.ViewBox):
    mouse_hovermoved = QtCore.pyqtSignal(QPointF)

    def __init__(self, **kwargs):
        pg.ViewBox.__init__(self, **kwargs)
        self.setAcceptHoverEvents(True)

    def hoverMoveEvent(self, event):
        self.mouse_hovermoved.emit(event.pos())
        super().hoverMoveEvent(event)

    def mouseClickEvent(self, event):
        #print("View MousePress", event.pos())
        super().mouseClickEvent(event)


class TestlWidget(QtGui.QWidget):
    drawingModeSetted = QtCore.pyqtSignal(int)
    mergeRequested = QtCore.pyqtSignal()
    radiusIncreased = QtCore.pyqtSignal()
    radiusDecreased = QtCore.pyqtSignal()
    mousePressed = QtCore.pyqtSignal(QPointF, bool)
    removeRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(TestlWidget, self).__init__(parent=parent)

        self.gui = QtGui.QGridLayout()
        self.setLayout(self.gui)
        self.resize(600, 400)
        self.setMouseTracking(True)

        self.current_mouse_position = (0, 0)

        self.layout = pg.GraphicsLayoutWidget()

        self.gui.addWidget(self.layout)

        self.w1 = SingleViewBox(lockAspect=True)
        self.layout.addItem(self.w1)

        self.w1.installEventFilter(self)
        self.w1.setBackgroundColor((255, 255, 255, 255))

        pen = QPen()
        pen.setColor(QColor(255, 99, 71, 255))
        pen.setWidth(1)

        cells = []

        # read contours from file
        # contours_file = "/Volumes/Macintosh HD/Users/tanya/MyExpt_03IdentifyPrimaryObjects.csv"
        contours_file = "../../../res/contourtest.csv"
        brush1 = QBrush(QColor(255, 199, 171, 255))
        numberOfShowedObjects = 300
        with open(contours_file, "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            for lines in csv_reader:

                if numberOfShowedObjects == 0:
                    break

                polygon = QPolygonF()
                coordinates = lines[2].split(" ")

                for c in coordinates:
                    pos = c.split(",")
                    if len(pos) == 2:
                        polygon << QPointF(float(pos[0]),float(pos[1]))
                if not polygon.isEmpty():
                    ego = EntityGraphicObject([polygon], brush1, pen)
                    self.w1.addItem(ego)
                    cells.append(ego)
                    numberOfShowedObjects = numberOfShowedObjects - 1

        print("csv data is imported")

        """ 
        brush1 = QBrush(QColor(255, 199, 171, 255))
        p1 = EntityGraphicObject([QPolygonF(QRectF(40, 90, 50, 100))], brush1, pen)
        self.w1.addItem(p1)
        cells.append(p1)

        brush2 = QBrush(QColor(55, 199, 171, 255))
        p2 = EntityGraphicObject([QPolygonF(QRectF(10, 20, 50, 80))], brush2, pen)
        self.w1.addItem(p2)
        cells.append(p2)

        brush3 = QBrush(QColor(255, 19, 17, 255))
        p3 = EntityGraphicObject([QPolygonF(QRectF(100, 190, 50, 80))], brush3, pen)
        self.w1.addItem(p3)
        cells.append(p3)

        brush4 = QBrush(QColor(55, 219, 17, 255))
        p4 = EntityGraphicObject([QPolygonF(QRectF(150, 200, 50, 90))], brush4, pen)
        self.w1.addItem(p4)
        cells.append(p4)

        brush5 = QBrush(QColor(255, 19, 17, 255))
        p5 = EntityGraphicObject([QPolygonF(QRectF(300, 200, 50, 80))], brush5, pen)
        self.w1.addItem(p5)
        cells.append(p5)

        brush6 = QBrush(QColor(55, 209, 17, 255))
        p6 = EntityGraphicObject([QPolygonF(QRectF(300, 280, 50, 20))], brush6, pen)
        self.w1.addItem(p6)
        cells.append(p6)

        p7 = EntityGraphicObject([QPolygonF(QRectF(150, 20, 50, 80))], brush5, pen)
        self.w1.addItem(p7)
        cells.append(p7)

        p8 = EntityGraphicObject([QPolygonF(QRectF(100, 0, 50, 20))], brush6, pen)
        self.w1.addItem(p8)
        cells.append(p8)
        """

        self.cgu = CentralGraphicUnit(cells)

        # Signals
        self.mergeRequested.connect(self.cgu.merge)
        self.drawingModeSetted.connect(self.cgu.setDrawingMode)
        self.radiusIncreased.connect(self.cgu.increaseRadius)
        self.radiusDecreased.connect(self.cgu.decreaseRadius)
        self.mousePressed.connect(self.cgu.draw)
        self.removeRequested.connect(self.cgu.remove)

    def eventFilter(self, obj, event):

        if event.type() == QtCore.QEvent.GraphicsSceneMouseMove:
            self.current_mouse_position = event.pos()
            #"GUI MouseMove", self.current_mouse_position)

        if event.type() == QtCore.QEvent.GraphicsSceneMousePress:
            #print("GUI MousePress", self.current_mouse_position)
            self.mousePressed.emit(event.pos(), False)

        if event.type() == QtCore.QEvent.GraphicsSceneMouseRelease:
            pass
            #print("GUI MouseRelesae", self.current_mouse_position)

        if event.type() == QtCore.QEvent.GraphicsSceneHoverMove:
            self.current_mouse_position = event.pos()
           # print("GUI MouseHOVER", self.current_mouse_position)

        return False

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_R:
            self.drawingModeSetted.emit(1)
        elif event.key() == QtCore.Qt.Key_M:
            self.mergeRequested.emit()
        elif event.key() == QtCore.Qt.Key_D:
            self.drawingModeSetted.emit(2)
        elif event.key() == QtCore.Qt.Key_E:
            self.removeRequested.emit()
        elif event.key() == QtCore.Qt.Key_Plus:
            self.radiusIncreased.emit()
        elif event.key() == QtCore.Qt.Key_Minus:
            self.radiusDecreased.emit()
        else:
            self.drawingModeSetted.emit(0)

        event.ignore()


# Initializing Qt
app = QtGui.QApplication([])

controller = Controller()
# Create a top-level widget to hold everything
widget = controller.viewer#TestlWidget()

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
# contours_file = "/Volumes/Macintosh HD/Users/tanya/MyExpt_03IdentifyPrimaryObjects.csv"
contours_file = "./res/contourtest.csv"
numberOfShowedObjects = 300
with open(contours_file, "r") as csv_file:
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
