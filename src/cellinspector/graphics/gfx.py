import pyqtgraph as pg
from PyQt5.QtGui import QPen, QColor, QBrush
from PyQt5.QtWidgets import QGraphicsItem

COLOR_SELECTED_ITEM = QColor(128, 128, 128, 255)
COLOR_DEFAULT_PEN = QColor(2, 2, 2, 255)
COLOR_DEFAULT_BRUSH = QColor(255, 255, 255, 255)


class GFX(pg.GraphicsObject):
    """A graphic object, which is defined by path
    """
    @property
    def brush(self):
        if self.__brush is None:
            self.__brush = QBrush(COLOR_DEFAULT_BRUSH)
        return self.__brush

    @brush.setter
    def brush(self, brush):
        self.__brush = brush

    @property
    def pen(self):
        if self.__pen is None:
            self.__pen = QPen()
            self.__pen.setColor(COLOR_DEFAULT_PEN)
            self.__pen.setWidth(1)
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

    def __init__(self, entity, brush=None, pen=None):

        super(GFX, self).__init__()

        self.entity = entity
        self.brush = brush
        self.pen = pen

        self.selectedPen = None
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        self.showTags = False

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

        if self.showTags and len(self.entity.tags) > 0:
            painter.drawText(self.boundingRect(), 1, str(self.entity.tags))

    def hoverLeaveEvent(self, event):
        self.showTags = False
        self.update()

