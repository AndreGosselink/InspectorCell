import pyqtgraph as pg
from AnyQt.QtGui import QPolygonF
from AnyQt.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem as SOGI
import AnyQt.QtCore as qc

from ..event import ActiveEntity


class PolyMaker(qc.QRunnable):
    """Buddy of GFX
    """

    def __init__(self, gfx, factor, pen, brush):
        super().__init__()
        self._gfx = gfx
        self._factor = factor

    # def run(self):
    #     polygons = []
    #     for entityPoly in self._gfx.entity.path.toSubpathPolygons():
    #         cachePoly = QPolygonF()
    #         for i, point in enumerate(entityPoly):
    #             if i % self._factor == 0:
    #                 cachePoly << point
    #         polygons.append(cachePoly)

    #     self._gfx._cache[self._factor] = polygons

    def _getPolygons(self):
        polygons = []
        for entityPoly in self._gfx.entity.path.toSubpathPolygons():
            cachePoly = QPolygonF()
            for i, point in enumerate(entityPoly):
                if i % self._factor == 0:
                    cachePoly << point
            polygons.append(cachePoly)

        return polygons

    def run(self):
        # pixmap should be fastest
        # rect = self._gfx.boundingRect()
        # width, height = rect.width(), rect.height()
        # prerender = QPixmap(width, height)

        # Picture gives little advantage
        # prerender = QPicture()
        # painter = QPainter()

        # painter.begin(prerender)
        # painter.setBrush(self._brush)
        # painter.setPen(self._pen)
        # for poly in self._getPolygons():
        #     painter.drawPolygon(poly)
        # painter.end()

        self._gfx._cache[self._factor] = self._getPolygons()


class GFX(pg.GraphicsObject):
    """A graphic object, which is defined by path
    """

    def __init__(self, entity, defaultStyle=None, selectedStyle=None):
        """Graphical representation in the scene for the Qt backend

        Parameters
        ----------
        entity : Entity
            The entity this representation represents

        defaultStyle : object
            Defines coloring of entity representation when not selected,
            see Notes for further info

        selectedStyle : object
            Defines coloring of entity representation when selected,
            see Notes for further info

        Notes
        -----
        Defines coloring of entity representation when not selected Object that
        must have the attributes `defaultStyle.pen` and `defaultStyle.brush`
        These must be of the type `QPen` and `QBrush` respectively, which are
        then used during painting in `GFX.paint`
        """
        super().__init__()

        self.entity = entity
        self.selectedStyle = selectedStyle
        self.defaultStyle = defaultStyle

        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self._boundingRect = None

        # caching the shape, get invalidated after updates to be redrawn
        self._cache = {}
        # list to preserve ordering
        self._polyQuality = [
            # min. LOD: PointFactor
            (0.5, 1),
            (0.3, 8),
            (0.05, 15),
        ]

    def boundingRect(self):
        if self._boundingRect is None:
            self._boundingRect = self._computeBoundingRect()
        return self._boundingRect

    def _computeBoundingRect(self):
        ret = self.entity.boundingbox
        if ret is None:
            return qc.QRectF()
        else:
            return ret

    def shape(self):
        return self.entity.path

    def paint(self, painter, *args):

        #TODO improve me. Only set pen when other than
        # the pen found in painter. or just set change the
        # color of the pen and set the golbal pens in channel
        if self.isSelected():
            pen = self.selectedStyle.pen
            brush = self.selectedStyle.brush
        else:
            pen = self.defaultStyle.pen
            brush = self.defaultStyle.brush
        
        #TODO look if needed, otherwise remove caching pictures
        # if self._cacheHI is None:
        #     print('Caching HI')
        #     self._cacheHI = QPicture()
        #     painter.save()
        #     # painter.begin(self._cacheHI)
        #     for poly in self.entity.path.toSubpathPolygons():
        #         painter.drawPolygon(poly)
        #     # painter.end()
        #     painter.restore()

        # # painter.drawPicture(0, 0, self._cacheHI)
        # self._cacheHI.play(painter)

        #TODO calculate globally
        lod = SOGI.levelOfDetailFromTransform(painter.worldTransform())
        # lod = 100
        for minLod, factor in self._polyQuality:
            if lod >= minLod: # draw the full thing
                cached_polygons = self._cache.get(factor, None)

                if cached_polygons is None:
                    runable = PolyMaker(self, factor, pen, brush)
                    thr = qc.QThreadPool.globalInstance()
                    thr.start(runable)
                    polygons = self.entity.path.toSubpathPolygons()
                else:
                    polygons = cached_polygons

                # if cached is None:
                painter.setPen(pen)
                painter.setBrush(brush)

                for poly in polygons:
                    painter.drawPolygon(poly)
                # else:
                #     # painter.drawPixmap(
                #     #     self.boundingRect(), cached, qc.QRectF(cached.rect()))
                #     painter.drawPicture(0, 0, cached)

                # as soon as the correct detail was found stop
                break

    def hoverEnterEvent(self, event):
        # import IPython as ip
        # ip.embed()
        activation = ActiveEntity(self.entity, True, rect=self.boundingRect())
        qc.QCoreApplication.postEvent(self.parent(), activation)

    def hoverLeaveEvent(self, event):
        activation = ActiveEntity(self.entity, False)
        qc.QCoreApplication.postEvent(self.parent(), activation)

    def update(self, *args, **kwargs):
        self._cache = {}
        super().update(*args, **kwargs)

def convertToInt(rect):
    x, y, w, h = rect
    w = int(w)
    h = int(h)
    x = int(x)
    y = int(y)
    return x, y, w, h

