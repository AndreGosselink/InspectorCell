import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QColor, QPainterPath
from PyQt5.QtWidgets import QGraphicsItem

from src.entities import EntityManager

COLOR_SELECTED_ITEM = QColor(128, 128, 128, 255)


class EntityGraphicObject(pg.GraphicsObject):
    object_selected = QtCore.pyqtSignal(int, bool)
    mouse_moved = QtCore.pyqtSignal(QPointF)
    mouse_hovermoved = QtCore.pyqtSignal(QPointF)
    mouse_entered = QtCore.pyqtSignal(object)
    mouse_pressed = QtCore.pyqtSignal(QPointF)
    mouse_released = QtCore.pyqtSignal(QPointF)

    @property
    def entity(self):
        return self.__entity

    @entity.setter
    def entity(self, entity):
        self.__entity = entity

    @property
    def brush(self):
        return self.__brush

    @brush.setter
    def brush(self, brush):
        self.__brush = brush

    @property
    def pen(self):
        return self.__pen

    @pen.setter
    def pen(self, pen):
        self.__pen = pen

    @property
    def selectedPen(self):
        if self.__selectedPen is None:
            self.__selectedPen = QPen()
            self.__selectedPen.setColor(COLOR_SELECTED_ITEM)
            self.__selectedPen.setWidth(3)

        return self.__selectedPen

    @selectedPen.setter
    def selectedPen(self, pen):
        self.__selectedPen = pen

    def __init__(self, poly, brush, pen):

        super(EntityGraphicObject, self).__init__()

        self.entity = EntityManager().make_entity()
        self.entity.from_polygons(poly)

        self.brush = brush
        self.pen = pen

        self.parent = None

        self.selectedPen = None
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setAcceptHoverEvents(True)
        self.selected = False

    def isSelected(self):
        return self.selected

    def setSelected(self, selected):
        self.selected = selected
        self.object_selected.emit(self.entity.eid, selected)

    def mouseReleaseEvent(self, event):
        self.mouse_released.emit(event.pos())

    def mouseMoveEvent(self, event):
        self.mouse_moved.emit(event.pos())

    def mouseDoubleClickEvent(self, event):
        if self.isSelected():
            self.setSelected(False)
        else:
            self.setSelected(True)

        self.update()

    def mousePressEvent(self, event):
        self.mouse_pressed.emit(event.pos())

    def hoverMoveEvent(self, event):
        self.mouse_hovermoved.emit(event.pos())
        super().hoverMoveEvent(event)

    def hoverEnterEvent(self, event):
        self.mouse_entered.emit(self.entity)
        super().hoverEnterEvent(event)

    def boundingRect(self):
        return self.entity.boundingbox

    def paint(self, painter, option, widget):
        if self.isSelected():
            painter.setPen(self.selectedPen)
        else:
            painter.setPen(self.pen)

        painter.setBrush(self.brush)

        for p in self.entity.path.toSubpathPolygons():
            painter.drawPolygon(p)