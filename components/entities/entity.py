"""Container for data, masks, graphics items, annotations logic etc. pp.
related to a single, identifyable thingy in an image stack
"""
import numpy as np
import cv2
from PyQt5.QtCore import QRect, QPointF
from PyQt5.QtGui import QPolygonF, QPainterPath


def pathToContours(path):
    if path is None:
        return None

    contours = []

    for polygon in path.toSubpathPolygons():
        n_points = len(polygon)
        contour = np.empty([n_points, 2], dtype=np.int32)
        for i in range(n_points):
            contour[i, 0] = polygon[i].x()
            contour[i, 1] = polygon[i].y()
        contours.append(contour)

    return contours

def convertToInt(items):
    res_items = []

    for item in items:
        res_items.append(int(item))

    return tuple(res_items)

def contoursToPath(contours):
    if contours is None:
        return None

    polygons = []

    for contour in contours:
        polygon = QPolygonF()
        for x, y in contour:
            polygon << QPointF(x, y)
        polygons.append(polygon)

    return polygons


class Entity:
    """Base entity derived from image
    should be generated by factory only

    Will be hierarchically ordered. Thus might not
    have any functions that prevent an atomic use
    of the entities e.g. as nodes in an hierarchical,
    ordered tree
    """

    _used_ids = set([])

    @property
    def contours(self):
        return pathToContours(self.__path)

    @contours.setter
    def contours(self, contours):
        self.__path = contoursToPath(contours)

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, path):
        self.__path = path

    @property
    def boundingbox(self):
        """
        properties of the entity in context of
        the view of the entity
        a QRect locating the entity in the scene it is
        placed in
        """
        if self.__path is None:
            return None
        else:
            return self.__path.boundingRect()

    def __init__(self, entity_id):
        """raises valueerror if entity_id is not none
        and invalid id because
        """

        ### Logic ###
        # must be unique, enforced on factory level
        # on factory level to avoid resetting state of
        # class later on
        self.eid = entity_id

        ### Imagepixel context ###
        # properties of the entity context of
        # pixel based images / sources of data
        # a numpy slice than can be used to get the pixels
        # from the image that belong to the object in each
        # respective channel
        self.mask_slice = None

        # boolean numpy mask
        # must have same shape as the _slice. Given the of
        # the image returned after slicing, the pixel in the
        # mask being True signify pixels within the slice
        # beeing image pixels
        self.mask = None

        ### View context ###
        # contours as natively produced by opencv, means list of points
        # defining polygons
        self.contours = None

        # QPainterPath, giving the polygon of the entity
        # representing it in the view
        self.path = None

        ### Common Attributes ###
        # all attributes relevant for drawing
        # like colors, shapes, whatever
        # to be manipulated directly
        self.attributes = {}

        ### Data ###
        # all the stuff that is data related
        # like annotation and derived values/scalars
        # can be manipulated directly
        self.tags = []
        self.scalars = {}

    def from_polygons(self, polygons, offset=(0, 0)):
        """Sets the mask, given the contour points:
        list of numpy.arrays with the shape (n, 2),
        where each index i is on point in the polygon
        """

        if len(polygons) == 0:
            msg = 'Number of polygons is 0'
            raise ValueError(msg)

        self.path = QPainterPath()
        for polygon in polygons:
            self.path.addPolygon(polygon)

        x, y, w, h = convertToInt(self.boundingbox.getRect())
        self.mask = np.zeros((w, h), np.uint8)
        cv2.drawContours(self.mask, self.contours, -1, 1, -1)
        row_off, col_off = offset
        self.mask_slice = (
            slice(y + row_off, y + h + row_off),
            slice(x + col_off, x + w + col_off)
        )

    def from_contours(self, contours, offset=(0, 0)):
        """Sets the mask, given the contour points:
        list of numpy.arrays with the shape (n, 2),
        where each index i is on point in the polygon
        """

        if len(contours) == 0:
            msg = 'Number of polygons is 0'
            raise ValueError(msg)

        self.contours = contours

        x, y, w, h = convertToInt(self.boundingbox.getRect())
        self.mask = np.zeros((w, h), np.uint8)
        cv2.drawContours(self.mask, contours, -1, 1, -1)
        row_off, col_off = offset
        self.mask_slice = (
            slice(y + row_off, y + h + row_off),
            slice(x + col_off, x + w + col_off)
        )

    def from_mask(self, mask_slice, mask, offset=(0, 0)):
        """Sets the polygon, given the bool mask for the eslice
        where bool mask is a np.array and eslice a tupple of slices

        Raises
        ------
        ValueError if shape of mask_slice not corresponds to shape of mask
        """

        sl_shape = tuple(sl.stop - sl.start for sl in mask_slice)
        if not sl_shape == mask.shape:
            msg = 'Shape of mask (is {}) must be equal to indexed with' + \
                  'mask_slice (is {})'
            raise ValueError(msg.format(str(sl_shape), str(mask.shape)))

        self.mask = mask.copy()
        if offset != (0, 0):
            row_off, col_off = offset
            row_sl, col_sl = mask_slice
            mask_slice = (
                slice(row_sl.start + row_off, row_sl.stop + row_off),
                slice(col_sl.start + col_off, col_sl.stop + col_off)
            )
        # immuteable, very tuple like in each respect
        # esp identity
        self.mask_slice = mask_slice

        self._set_contours()

    def _set_contours(self):
        """Sets polygon from self.mask and self.slice
        """
        # compress verticals and horizontals
        method = cv2.CHAIN_APPROX_SIMPLE
        # retrive tree hirachy
        mode = cv2.RETR_LIST
        # offset is taken from slice

        major = cv2.__version__.split('.')[0]

        if major == '3':
            _, contours, _ = cv2.findContours(self.mask.astype(np.uint8), mode, method)
        else:
            contours, _ = cv2.findContours(self.mask.astype(np.uint8), mode, method)

        self.contours = [cont.squeeze() for cont in contours]
