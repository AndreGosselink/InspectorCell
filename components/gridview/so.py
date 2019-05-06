import pyqtgraph as pg


class Poly(pg.GraphicsObject):

    def __init__(self):
        super().__init__()

        pos = qc.QPointF(0, 0)
        self.setPos(pos)

        pen = QPen()
        pen.setColor(QColor(255, 99, 71, 255))
        pen.setWidth(1)
        self.setPen(pen)

        pts0 = []
        pts1 = []
        r = 2
        for x in np.linspace(-2, 2, 100):
            disc = r**2 - x**2
            if disc <= 0: continue
            y = np.sqrt(disc)
            pts0.append((x + random.random(), y + random.random()))
            pts1.append((-x + random.random(), y + random.random()))

        self.poly = qg.QPolygonF()
        for p in pts0 + pts1:
            self.poly.append(qc.QPointF(*p))

    def _invalidateCache(self):
        self._boundingRect = None

    def setPen(self, *args, **kwargs):
        """Set the pen for drawing the line. Allowable arguments are any that are valid
        for :func:`mkPen <pyqtgraph.mkPen>`."""
        self.pen = pg.fn.mkPen(*args, **kwargs)
        self.update()

    def setPos(self, pos):

        if type(pos) in [list, tuple]:
            newPos = pos
        elif isinstance(pos, qc.QPointF):
            newPos = [pos.x(), pos.y()]

        if self.pos != newPos:
            self.pos = newPos
            self._invalidateCache()
            super().setPos(qc.QPointF(self.pos[0], self.pos[1]))

    def getXPos(self):
        return self.pos[0]

    def getYPos(self):
        return self.pos[1]

    def getPos(self):
        return self.pos

    def paint(self, p, *args):
        p.setRenderHint(p.Antialiasing)

        left, top, right, bottom = (0, 0, 2, 2)
        hor0 = left, 0.0
        hor1 = right, 0.0
        ver0 = 0.0, top
        ver1 = 0.0, bottom

        self.pen.setJoinStyle(qc.Qt.MiterJoin)
        p.setPen(self.pen)
        p.drawPolygon(self.poly)

    def boundingRect(self):
        return self.poly.boundingRect()


app = qw.QApplication([])
viewer = Viewer()
viewer.window.show()
viewer.setup_grid(1, 2)

polygon = Poly()
# viewer.layout.scene().addItem(polygon)
# for cview in viewer.views.values():
#     cview.addItem(polygon)
vb0, vb1 = viewer.views[(0, 0)], viewer.views[(0, 1)]

app = qw.QApplication([])
viewer = Viewer()
viewer.window.show()
viewer.setup_grid(1, 2)

polygon = Poly()
# viewer.layout.scene().addItem(polygon)
# for cview in viewer.views.values():
#     cview.addItem(polygon)
vb0, vb1 = viewer.views[(0, 0)], viewer.views[(0, 1)]


scene = vb0.scene()
added = vb0.addedItems
childgroup = vb1.childGroup = vb0.childGroup
childgroup.setParent(scene)
childgroup.itemsChangedListeners.append(vb1)

vb1.addedItems = vb0.addedItems

if scene is not polygon.scene():
    scene.addItem(polygon)

polygon.setParentItem(childgroup)
added.append(polygon)

vb0.updateAutoRange()
vb1.updateAutoRange()

assert vb0.scene() is vb1.scene()
assert vb0.scene() is polygon.scene()
assert vb0.addedItems is vb1.addedItems
assert vb0.childGroup is vb1.childGroup

app.exec_()
