import warnings

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPainterPath

from src.graphics.EntityGraphicObject import EntityGraphicObject

MAX_R = 100


class CentralGraphicUnit:

    """
    drawing mode: Press "D" - paint (self.draw_mode = 2);
                  Press "E" - erase (self.draw_mode = 1);
                  Press any other key to off drawing mode (self.draw_mode = 0).

    To change radius of drawing circle: press key + or -

    To merge press "M"
    """

    def __init__(self, graphicObjects):
        self.graphicObjects = graphicObjects
        self.selected_object_ids = []
        self.drawingMode = 0
        self.prev_event_type = None
        self.mouse_move_path = []
        self.start_mouse_position = None
        self.r = 10
        self.mouse_pos = None

        self.viewBox = graphicObjects[0].getViewBox()
        self.viewBox.mouse_hovermoved.connect(self.mouse_position)

        for obj in graphicObjects:
            obj.object_selected.connect(self.selectionChanged)
            obj.mouse_hovermoved.connect(self.mouse_position)
            obj.mouse_moved.connect(self.update_mouse_path)
            obj.mouse_released.connect(self.draw)

    def update_mouse_path(self, pos):
        self.mouse_move_path.append(pos)

    def increaseRadius(self):
        print("+")
        if self.drawingMode > 0 and self.radius < MAX_R:
            self.radius = self.radius + 1

    def decreaseRadius(self):
        print("-")
        if self.drawingMode > 0 and self.radius > 1:
            self.radius = self.radius - 1

    def setDrawingMode(self, drawingMode):
        self.drawingMode = drawingMode

        if drawingMode > 0:
            # if draw mode, only one object need to be selected. Leave only last selected object
            self.deselectFirstNSelectedObjects(len(self.selected_object_ids) - 1)

    def deselectFirstNSelectedObjects(self, n):

        numberOfSelectedObjects = len(self.selected_object_ids)
        numberOfLeavedObjects = numberOfSelectedObjects - n

        if numberOfLeavedObjects < 0:
            # de-select all objects
            numberOfLeavedObjects = 0

        while numberOfSelectedObjects > numberOfLeavedObjects:
            id = self.selected_object_ids.pop(0)
            indx = self.getObjectPosById(id)
            self.graphicObjects[indx].selected = False
            self.graphicObjects[indx].update()
            numberOfSelectedObjects = numberOfSelectedObjects - 1


    def selectionChanged(self, id, selected):
        print("selectionChanged, number of already selected objects", len(self.selected_object_ids))
        if selected:
            if self.drawingMode:
                # de-select all objects
                print("selection_changed draw_mode ", self.drawingMode)
                self.deselectFirstNSelectedObjects(len(self.selected_object_ids))

            self.selected_object_ids.append(id)
        else:
            self.selected_object_ids.remove(id)

    def mouse_position(self, pos):
        self.mouse_pos = pos

    def getObjectPosById(self, id):

        for i in range(len(self.graphicObjects)):
            if id == self.graphicObjects[i].entity.eid:
                return i

        return None

    def draw(self, pos):
        print("paint draw_mode", self.drawingMode, len(self.selected_object_ids))
        # draw_mode is set, and object is selected
        if self.drawingMode and len(self.selected_object_ids) == 1:
            print("drawing")

            indx = self.getObjectPosById(self.selected_object_ids[0])

            if len(self.mouse_move_path) == 0:
                print("current", pos)

                if self.drawingMode == 1:
                    self.cropPolygon(indx, pos, self.r)
                elif self.drawingMode == 2:
                    self.expandPolygon(indx, pos, self.r)

            else:
                extendedPath = QPainterPath()
                for p in self.mouse_move_path:
                    extendedPath.addEllipse(QPointF(p), self.r, self.r)

                extendedPath.setFillRule(Qt.WindingFill)

                if self.graphicObjects[indx].entity.path.intersects(extendedPath):
                    if self.drawingMode == 1:
                        self.graphicObjects[indx].entity.path = self.graphicObjects[indx].entity.path.subtracted(extendedPath).simplified()
                    elif self.drawingMode == 2:
                        self.graphicObjects[indx].entity.path = self.graphicObjects[indx].entity.path.united(extendedPath).simplified()

                    self.graphicObjects[indx].update()

        self.mouse_move_path = []

    def mouse_presed_event(self, pos):
        if self.isSelected():
            self.start_mouse_position = pos()

    def expandPolygon(self, indx, center, r):
        circle_brush = QPainterPath()
        circle_brush.addEllipse(center, r, r)

        if self.graphicObjects[indx].entity.path.intersects(circle_brush):
            self.graphicObjects[indx].entity.path = self.graphicObjects[indx].entity.path.united(circle_brush)
            self.graphicObjects[indx].update()

    def cropPolygon(self, indx, center, r):
        circle_brush = QPainterPath()
        circle_brush.addEllipse(center, r, r)

        if self.graphicObjects[indx].entity.path.intersects(circle_brush):
            self.graphicObjects[indx].entity.path = self.graphicObjects[indx].entity.path.subtracted(circle_brush)
            self.graphicObjects[indx].update()

    def merge(self):
        """ Merge two or more polygons. Two use-cases:
            1. polygons are overlapping or touching each other
            2. otherwise

            In the 1st use-case we use union of polygons
            In the 2nd use-case we not allow merging
        """
        self.drawingMode = 0

        number_selected_objects = len(self.selected_object_ids)
        if number_selected_objects < 2:
            return

        print("merging", self.selected_object_ids)

        selected_objects_indxs = []

        selected_object_indx = self.getObjectPosById(self.selected_object_ids[0])
        selected_objects_indxs.append(selected_object_indx)

        new_path = self.graphicObjects[selected_object_indx].entity.path
        selected_brush = self.graphicObjects[selected_object_indx].brush
        selected_pen = self.graphicObjects[selected_object_indx].pen

        was_merging = False
        for i in range(1, number_selected_objects):
            selected_object_indx = self.getObjectPosById(self.selected_object_ids[i])
            selected_objects_indxs.append(selected_object_indx)
            if new_path.intersects(self.graphicObjects[selected_object_indx].entity.path):
                new_path.setFillRule(Qt.WindingFill)
                new_path = new_path.united(self.graphicObjects[selected_object_indx].entity.path).simplified()
                was_merging = True

        if was_merging:

            self.selected_object_ids = []
            newObject = EntityGraphicObject(new_path.toFillPolygons(), selected_brush, selected_pen)
            newObject.object_selected.connect(self.selectionChanged)
            newObject.mouse_hovermoved.connect(self.mouse_position)
            newObject.mouse_moved.connect(self.update_mouse_path)
            newObject.mouse_released.connect(self.draw)

            for indx in selected_objects_indxs:
                print("remove ",indx)
                self.graphicObjects[indx].parent = newObject
                self.viewBox.removeItem(self.graphicObjects[indx])

            self.graphicObjects.append(newObject)
            self.viewBox.addItem(newObject)