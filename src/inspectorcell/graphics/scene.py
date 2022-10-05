# built-ins
# import warnings

# GUI stuff
import pyqtgraph as pg
from PyQt5 import QtCore as qc
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainterPath

import numpy as np

from ..event import ScalarAssignmentChanged, EntityChangedEvent

RADIUS_MAX = 100
RADIUS_MIN = 1
RADIUS_DEFAULT = 10
RADIUS_CHANGE = 1

def merge2Paths(pathA, pathB):
    if pathA.intersects(pathB):
        pathA.setFillRule(Qt.WindingFill)
        return pathA.united(pathB).simplified()
    return None

def mapContur(contours, mapping):
    newConts = []
    for cont in contours:
        cur_cont = []
        for pt in cont:
            pt = tuple(pt)
            mapped = mapping.get(pt, pt)
            # if mapped != pt:
            #     print(pt, '->', mapped)
            cur_cont.append(mapped)
        newConts.append(np.array(cur_cont).astype(int))
    return newConts

def merge2Entities(entA, entB):
    pathA = entA.path
    pathB = entB.path
    newPath = merge2Paths(pathA, pathB)
    if not newPath is None:
        return newPath
    return None

def alignedMerge(selectedItems):
    mergedItems = set()
    pairwieseMergedPathes = []

    for i, itemA in enumerate(selectedItems, 0):
        for j, itemB in enumerate(selectedItems, 1):
            # print('intersect', 
            #        itemA.entity.path.intersects(itemB.entity.path))
            newPath = merge2Entities(itemA.entity,
                                     itemB.entity)
            if newPath is not None:
                mergedItems.add(itemA)
                mergedItems.add(itemB)
                pairwieseMergedPathes.append(newPath)

    # reducing merged paths
    newPath = pairwieseMergedPathes[0]
    for i in range(1, len(pairwieseMergedPathes)):
        newPath = merge2Paths(newPath, pairwieseMergedPathes[i])

        if newPath is None:
            return None, set([])

    return newPath, mergedItems


class ViewContextScene(pg.GraphicsScene):

    #gfxAdded = qc.pyqtSignal(object)
    #gfxDeleted = qc.pyqtSignal(object)

    def __init__(self, *args, entityManager=None, isDisabled=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.drawingRadius = RADIUS_DEFAULT
        #XXX changed to on mode variable
        # as drawingMode and erasingMode are mutual exclusive anyways
        # 'N'ormal mode
        # 'D'rawind mode
        # 'E'rasing mode
        self.mode = 'N'
        self.mouseDrawingPath = []
        self.isDisabledScene = isDisabled
        self.entityManager = entityManager

    def mouseDoubleClickEvent(self, event):
        if self.isDisabledScene:
            event.ignore()
            return

        if self.mode == 'D':
            itemUnderMouse = self.itemAt(
                event.scenePos().x(), event.scenePos().y(),
                self.views()[0].transform())
            if itemUnderMouse is None:
                self.create(event.scenePos())

        event.ignore()
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        """ remember mouse movement path only if one object is selected and we are in a drawing mode
        """
        if self.mode in 'DE' and len(self.selectedItems()) == 1:
            self.mouseDrawingPath.append(event.scenePos())
        else:
            itemUnderMouse = self.itemAt(event.scenePos().x(), event.scenePos().y(), self.views()[0].transform())
            # if itemUnderMouse is not None:
            #     self.showTags(itemUnderMouse)

        event.ignore()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        self.mouseDrawingPath = []

        event.ignore()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """ if we are in a drawing mode and selected one object draw or eraise
        """
        #TODO this function deselects
        if len(self.selectedItems()) != 1 or self.mode == 'N':
            self.mouseDrawingPath = []
            event.ignore()
            #FIXME Fishi part that somehow introduces bug for
            #banmode combined with drawing
            if self.isDisabledScene:
                return
            else:
                super().mouseReleaseEvent(event)
                return

        item = self.selectedItems()[0]

        # handles the case when instantly clicked on segment
        if len(self.mouseDrawingPath) == 0:
            self.mouseDrawingPath.append(event.scenePos())

        extendedPath = QPainterPath()
        for p in self.mouseDrawingPath:
            extendedPath.addEllipse(
                QPointF(p), self.drawingRadius, self.drawingRadius)

        extendedPath.setFillRule(Qt.WindingFill)
        entityPath = item.entity.path
        if self._intersect(entityPath, extendedPath):
            # They intersect, lets erase what is there!
            if self.mode == 'E':
                item.entity.path = item.entity.path.subtracted(extendedPath)
            # only draw mode left. Do it if not fully contained
            elif not self._contained(entityPath, extendedPath):
                item.entity.path = item.entity.path.united(extendedPath)

            item.entity.path = item.entity.path.simplified()
            self.removeItem(item)
            qc.QCoreApplication.postEvent(
                self.parent(), EntityChangedEvent(item.entity))
        
        event.accept()

    def _intersect(self, path0, path1):
        return path0.intersects(path1)

    def _contained(self, path0, path1):
        return path1.subtracted(path0.intersected(path1)).isEmpty()

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
        if event.key() == qc.Qt.Key_M:
            self.merge()

        elif event.key() == qc.Qt.Key_R:
            self.remove()

        elif event.key() == qc.Qt.Key_H:
            self.home()

        elif event.key() == qc.Qt.Key_V:
            self.changeVisible(False)

        elif event.key() == qc.Qt.Key_S:
            self.changeVisible(True)

        elif event.key() in (qc.Qt.Key_L, qc.Qt.Key_K):
            if event.key() == qc.Qt.Key_L:
                change = -1
            else: 
                change = 1
            scalarAssigmentChanged = ScalarAssignmentChanged(change)
            qc.QCoreApplication.postEvent(self.parent(),
                                          scalarAssigmentChanged)

        super().keyPressEvent(event)

    def home(self):
        """
        TODO: set scene to view initial values
        """
        pass

    # Drawing functionality

    def setDrawingMode(self, mode):

        if mode == 'D':
            self.mode = 'D'
            self.mouseDrawingPath = []
            # if drawing mode is on, the only one object can to be selected. Leave only last selected object
            if mode and len(self.selectedItems()) > 1:
                self.deselectFirstNSelectedObjects(len(self.selectedItems()) - 1)
        elif mode == 'E':
            self.mode = 'E'
        else:
            self.mode = 'N'

    def changeRadius(self, value):
        self.drawingRadius = value

    def increaseRadius(self):
        self.drawingRadius = min(self.drawingRadius + RADIUS_CHANGE, RADIUS_MAX)

    def decreaseRadius(self):
        self.drawingRadius = max(self.drawingRadius - RADIUS_CHANGE, RADIUS_MIN)

    def create(self, center):
        """ Creates new entity and corresponding GFX with default shape and
        radius under position of mouse by double click
        """
        circleBrush = QPainterPath()
        circleBrush.addEllipse(center, self.drawingRadius, self.drawingRadius)

        newEntity = self.entityManager.make_entity()
        newEntity.from_polygons(circleBrush.toFillPolygons())

        qc.QCoreApplication.postEvent(self.parent(),
            EntityChangedEvent(newEntity))

    def addGFX(self, gfx):
        """Sets parentage of gfx, so that the gfx is registered in the 
        event system properly, then adds the gfx to the scene
        """
        gfx.setParent(self.parent())
        self.addItem(gfx)

    def remove(self):
        """
        Remove all selected items
        """
        for item in self.selectedItems():
            item.entity.removeGFX()
            # send signal to orange
            #self.gfxDeleted.emit(item.entity.eid)
            self.removeItem(item)

        self.update()

    def changeVisible(self, visible=False):
        """ Change visibility of selected entities. If None are selected
        show all entities
        """
        selectedItems = self.selectedItems()

        # # if there is a selection, set visible False
        # if selectedItems:
        #     visible = False
        # # select all cells and they shoudl be visible again
        # else:
        #     selectedItems = self.items()
        #     visible = True

        # make the changes
        if not visible:
            for item in selectedItems:
                item.setVisible(visible)
        elif visible:
            selectedItems = self.items()
            for item in selectedItems:
                item.setVisible(visible)

        # make the changes
        for item in selectedItems:
            item.setVisible(visible)
            return

    def merge(self):
        #TODO shoudl happen in entity manager
        """ Merge two or more selected graphic objects. Two use-cases:
            1. contours are overlapping or touching each other
            2. otherwise

            In the 1st use-case we use union of contours
            In the 2nd use-case we not allow merging
        """
        selectedItems = self.selectedItems()
        selectedEids = [itm.entity.eid for itm in selectedItems]

        # do nothing, as on item can not be merged with itself
        if len(selectedItems) < 2:
            return

        newPath, mergedItems = alignedMerge(selectedItems)
        if newPath is None:
            return

        newEntity = self.entityManager.make_entity()
        newEntity.from_polygons(newPath.toFillPolygons())
        parents = newEntity.generic['parents'] = []

        mergedScalars = {}
        mergedTags = set([])
        scalarValueContributions = {}
        #TODO handle ancestors
        # merged_ancestors = set([])
        for item in mergedItems:
            # process scalars
            for sig, val in item.entity.scalars.items():
                cont = scalarValueContributions.get(sig, 0)
                scalarValueContributions[sig] = cont + 1

                mergedVal = mergedScalars.get(sig, 0)
                mergedScalars[sig] = mergedVal + val

            for sig, count in scalarValueContributions.items():
                mergedScalars[sig] /= count

            # process tags
            mergedTags.update(item.entity.tags)

            # remove the GFX
            item.entity.removeGFX()
            parents.append(item.entity.eid.hex)

            # send signal to orange
            #self.gfxDeleted.emit(item.entity.eid)
            self.removeItem(item)

        # send signal to orange
        #self.gfxAdded.emit(newGFX)
        newEntity.scalars = mergedScalars
        newEntity.tags = mergedTags

        qc.QCoreApplication.postEvent(self.parent(),
            EntityChangedEvent(newEntity))
