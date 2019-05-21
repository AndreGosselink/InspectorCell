import pyqtgraph as pg
from PyQt5.QtGui import QPen, QColor
from PyQt5.QtWidgets import QGraphicsItem

COLOR_SELECTED_ITEM = QColor(128, 128, 128, 255)


class GFX(pg.GraphicsObject):

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

        super(GFX, self).__init__()

        self.brush = brush
        self.pen = pen

        self.selectedPen = None
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        return self.entity.boundingbox

    def shape(self):
        return self.entity.path

    def paint(self, painter, *args):
        if self.isSelected():
            painter.setPen(self.selectedPen)
        else:
            painter.setPen(self.pen)

        painter.setBrush(self.brush)

        for poly in self.entity.path.toSubpathPolygons():
            painter.drawPolygon(poly)