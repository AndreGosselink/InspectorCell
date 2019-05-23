# built-ins
import warnings

# GUI stuff
import pyqtgraph as pg
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsItem, QInputDialog

from ..entities import EntityManager
from ..graphics import gfx

RADIUS_MAX = 100
RADIUS_MIN = 2
RADIUS_DEFAULT = 10


class ViewerScene(pg.GraphicsScene):

    def __init__(self, isDisabled=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drawingRadius = RADIUS_DEFAULT
        self.drawingMode = False
        self.drawingModeErase = False
        self.mouseDrawingPath = []
        self.isDisabledScene = isDisabled

    def mouseDoubleClickEvent(self, event):
        if not self.isDisabledScene and not self.drawingMode:
            itemUnderMouse = self.itemAt(event.scenePos().x(), event.scenePos().y(), self.views()[0].transform())

            if itemUnderMouse is None:
                self.create(event.scenePos())
            else:
                self.showAddTagDialog(itemUnderMouse)

        pg.GraphicsScene.mouseDoubleClickEvent(self, event)

    def mouseMoveEvent(self, event):
        """ remember mouse movement path only if one object is selected and we are in a drawing mode
        """
        if self.drawingMode and len(self.selectedItems()) == 1:
            self.mouseDrawingPath.append(event.scenePos())
        else:
            itemUnderMouse = self.itemAt(event.scenePos().x(), event.scenePos().y(), self.views()[0].transform())
            if itemUnderMouse is not None:
                self.showTags(itemUnderMouse)

        pg.GraphicsScene.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        self.mouseDrawingPath = []

        event.ignore()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """ if we are in a drawing mode and selected one object draw or eraise
        """
        if self.drawingMode and len(self.selectedItems()) == 1:
            item = self.selectedItems()[0]
            if len(self.mouseDrawingPath) == 0:
                if self.drawingModeErase:
                    self.cropGFX(item, event.scenePos())
                else:
                    self.expandGFX(item, event.scenePos())

            else:
                extendedPath = QPainterPath()
                for p in self.mouseDrawingPath:
                    extendedPath.addEllipse(QPointF(p), self.drawingRadius, self.drawingRadius)

                extendedPath.setFillRule(Qt.WindingFill)

                if item.entity.path.intersects(extendedPath):
                    if not extendedPath.subtracted(
                            item.entity.path.intersected(extendedPath)).isEmpty():
                        if self.drawingModeErase:
                            item.entity.path = item.entity.path.subtracted(extendedPath).simplified()
                        else:
                            item.entity.path = item.entity.path.united(extendedPath).simplified()

                        item.update()

        self.mouseDrawingPath = []

        event.ignore()
        super().mouseReleaseEvent(event)

    def deselectFirstNSelectedObjects(self, n):

        numberOfSelectedObjects = len(self.selectedItems())
        numberOfLeavedObjects = numberOfSelectedObjects - n

        if numberOfLeavedObjects < 0:
            # de-select all objects
            numberOfLeavedObjects = 0

        while len(self.selectedItems()) > numberOfLeavedObjects:
            self.selectedItems()[0].setSelected(False)
            self.selectedItems()[0].update()

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_E:
            self.setDrawingMode(True)
            self.setDrawingModeErase(True)

        elif event.key() == QtCore.Qt.Key_D:
            self.setDrawingMode(True)
            self.setDrawingModeErase(False)

        elif event.key() == QtCore.Qt.Key_Plus:
            self.increaseRadius()

        elif event.key() == QtCore.Qt.Key_Minus:
            self.decreaseRadius()

        elif event.key() == QtCore.Qt.Key_M:
            self.merge()

        elif event.key() == QtCore.Qt.Key_R:
            self.remove()

        elif event.key() == QtCore.Qt.Key_H:
            self.home()

        else:
            self.setDrawingMode(False)

        pg.GraphicsScene.keyPressEvent(self, event)

    def home(self):
        """
        TODO: set scene to view initial values
        """
        pass

    def showTags(self, item):
        item.showTags = True

    def showAddTagDialog(self, item):
        """ only test version
        """
        text, ok = QInputDialog.getText(None, 'Tags', 'Add tag(s):')
        if ok:
            tags = text.split(",")
            print(tags)
            for tag in tags:
                item.entity.tags.append(tag)

    # Drawing functionality

    def setDrawingMode(self, drawingMode):
        self.drawingMode = drawingMode
        self.mouseDrawingPath = []
        # if drawing mode is on, the only one object can to be selected. Leave only last selected object
        if drawingMode:
            self.deselectFirstNSelectedObjects(len(self.selectedItems()) - 1)

    def setDrawingModeErase(self, drawingModeErase):
        self.drawingModeErase = drawingModeErase

    def increaseRadius(self):
        if self.drawingMode and self.drawingRadius < RADIUS_MAX:
            self.drawingRadius = self.drawingRadius + 1

    def decreaseRadius(self):
        if self.drawingMode and self.drawingRadius > RADIUS_MIN:
            self.drawingRadius = self.drawingRadius - 1

    def create(self, center):
        """ Creates new entity and corresponding GFX with default shape and radius under position of mouse by double click
        """
        circleBrush = QPainterPath()
        circleBrush.addEllipse(center, self.drawingRadius, self.drawingRadius)

        entityManager = EntityManager()
        newEntity = entityManager.make_entity()
        newEntity.from_polygons(circleBrush.toFillPolygons())
        newGFX = newEntity.makeGFX()

        self.addItem(newGFX)

    def remove(self):
        """
        Remove all selected items
        """
        for item in self.selectedItems():
            item.entity.removeGFX()
            self.removeItem(item)

    def merge(self):
        """ Merge two or more selected graphic objects. Two use-cases:
            1. contours are overlapping or touching each other
            2. otherwise

            In the 1st use-case we use union of contours
            In the 2nd use-case we not allow merging
        """

        numberOfSelectedItems = len(self.selectedItems())

        if numberOfSelectedItems < 2:
            # do nothing
            return

        mergedItems = set()
        pairwieseMergedPathes = []

        def merge2Paths(pathA, pathB):

            if pathA.intersects(pathB):
                pathA.setFillRule(Qt.WindingFill)
                return pathA.united(pathB).simplified()

            return None

        for i in range(0, numberOfSelectedItems):
            for j in range(1, numberOfSelectedItems):
                newPath = merge2Paths(self.selectedItems()[i].entity.path, self.selectedItems()[j].entity.path)
                if newPath is not None:
                    mergedItems.add(self.selectedItems()[i])
                    mergedItems.add(self.selectedItems()[j])
                    pairwieseMergedPathes.append(newPath)

        if len(mergedItems) > 0:
            newPath = pairwieseMergedPathes[0]
            selectedBrush = self.selectedItems()[0].brush
            selectedPen = self.selectedItems()[0].pen

            for i in range(1, len(pairwieseMergedPathes)):
                newPath = merge2Paths(newPath, pairwieseMergedPathes[i])
                if newPath is None:
                    # do nothing
                    return

            entityManager = EntityManager()
            newEntity = entityManager.make_entity()
            newEntity.from_polygons(newPath.toFillPolygons())
            newGFX = newEntity.makeGFX(selectedBrush, selectedPen)
            self.addItem(newGFX)

            for item in mergedItems:
                item.entity.removeGFX(newGFX.entity.eid)
                self.removeItem(item)

    def expandGFX(self, obj, center):
        circleBrush = QPainterPath()
        circleBrush.addEllipse(center, self.drawingRadius, self.drawingRadius)

        if obj.entity.path.intersects(circleBrush):
           obj.entity.path = obj.entity.path.united(circleBrush)
           obj.update()

    def cropGFX(self, obj, center):
        circleBrush = QPainterPath()
        circleBrush.addEllipse(center, self.drawingRadius, self.drawingRadius)

        if obj.entity.path.intersects(circleBrush):
            if obj.entity.path.intersected(circleBrush).subtracted(circleBrush).isEmpty():
                print("contain")
                return

            obj.entity.path = obj.entity.path.subtracted(circleBrush)
            obj.update()

