"""Container for data, masks, graphics items, annotations logic etc. pp.
related to a single, identifyable thingy in an image stack
"""
### Build-Ins
from datetime import datetime

### Extern
import numpy as np
import cv2

from AnyQt.QtCore import QPointF
from AnyQt.QtGui import QPolygonF, QPainterPath

### Project
from ..graphics.gfx import GFX, convertToInt
from .misc import get_kernel


def dilatedEntity(entity, k):
    """Inplace dilation of Entity shape

    Dilates the shape of an entity with a circular kernel
    The radius of the kernel is k pixels. Changes the entity
    in place.

    Parameters
    ----------
    entity : Entity
        Refrence to the in-place dilates entity

    k : int
        diameter of radial used for dilation

    Returns
    -------
    entity : Entity
        Refrence to the in-place dilates entity

    k : int
        Pixel diameter of circular kernel used for dilation
    """
    if k < 0:
        raise ValueError('Pixels must be >= 0!')
    if k == 0:
        return entity
    newShape = tuple(dim + 2*k for dim in entity.mask.shape)
    newMask = np.pad(entity.mask, k, 'constant', constant_values=False)
    newRowSlice, newColSlice = entity.mask_slice
    newSlice = (
        slice(newRowSlice.start - k, newRowSlice.stop + k, newRowSlice.step),
        slice(newColSlice.start - k, newColSlice.stop + k, newColSlice.step),
        )
    # dkern = np.ones((k, k), np.uint8)
    dkern = get_kernel(k)
    newMask = cv2.dilate(newMask.astype(np.uint8), dkern, iterations=1)
    entity.from_mask(newSlice, newMask.astype(bool))
    return entity



def contoursToPolgons(contours):
    if contours is None:
        return None

    polygons = []  
    for contour in contours:
        polygon = QPolygonF()
        try:
            # catching the case where there is only a dot
            for x, y in contour:
                polygon << QPointF(x, y)
        except TypeError:
            x, y = contour
            polygon << QPointF(x, y)
        polygons.append(polygon)

    return polygons

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

def contoursToPath(contours):
    if contours is None:
        return None

    path = QPainterPath()
    for contour in contours:
        polygon = QPolygonF()
        try:
            # catching the case where there is only a dot
            for x, y in contour:
                polygon << QPointF(x, y)
        except TypeError:
            x, y = contour
            polygon << QPointF(x, y)
        path.addPolygon(polygon)

    return path

def polygonsToPath(polys):
    if polys is None:
        return None

    path = QPainterPath()
    for polygon in polys:
        path.addPolygon(polygon)

    return path


class Entity:
    """Base entity derived from image
    should be generated by factory only

    Will be hierarchically ordered. Thus might not
    have any functions that prevent an atomic use
    of the entities e.g. as nodes in an hierarchical,
    ordered tree
    """

    @property
    def contours(self):
        # return self.__contours
        return pathToContours(self.__path)

    @contours.setter
    def contours(self, contours):
        # self.__contours = contours
        self.__path = contoursToPath(contours)

    @property
    def path(self):
        return self.__path

    @path.setter
    def path(self, path):
        self.__path = path

    @property
    def GFX(self):
        return self.__GFX

    @GFX.setter
    def GFX(self, gfx):
        self.__GFX = gfx

    @property
    def historical(self):
        return self._historical

    @historical.setter
    def historical(self, historical):
        self._historical = historical
        self.__timestamp = datetime.now()

    @property
    def timestamp(self):
        return self.__timestamp

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
        eid = int(entity_id)
        if float(eid) - entity_id != 0:
            msg = 'Cannot cast entity_id {} into int unambigously!'
            raise ValueError(msg.format(entity_id))
        self.eid = eid
        # if is an active or historic entity
        self.isActive = True

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
        self.__contours = []

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
        self.tags = set([])
        self.scalars = {}

        # Id of parent entity, set in case of merging
        self.parentEid = None
        # By default is false, if entity was removed or merged set to true
        self._historical = False
        # Timestamp of making entity historical, can be used for recovery
        self.__timestamp = None

        # Graphic Object
        self.__GFX = None

    def _set_mask(self, offset=(0, 0)):
        """Set mask and mask slice. Accesses Entity.boundingbox and
        Entity.contours, so that these values will be used to
        set Entity.mask and Entity.mask_slice
        """
        x, y, w, h = convertToInt(self.boundingbox.getRect())

        # uint so that opencv can draw on the array 
        self.mask = np.zeros((h+1, w+1), np.uint8)

        cv2.drawContours(
            image=self.mask,
            contours=self.contours,
            contourIdx=-1,
            color=1,
            thickness=-1,
            # lineType=None,
            # hierarchy=None,
            # maxLevel=None,
            offset=(-x, -y),
        )
        
        # make it bool so we can use it as mask
        self.mask = self.mask.astype(bool)

        row_off, col_off = offset
        self.mask_slice = (
            slice(y + row_off, y + h+1 + row_off),
            slice(x + col_off, x + w+1 + col_off)
        )

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

        self._set_mask(offset=offset)

        # x, y, w, h = convertToInt(self.boundingbox.getRect())
        # self.mask = np.zeros((w + 1, h + 1), np.uint8)

        # cv2.drawContours(self.mask, self.contours, -1, 1, -1)
        # row_off, col_off = offset
        # self.mask_slice = (
        #     slice(y + row_off, y + h + 1 + row_off),
        #     slice(x + col_off, x + w + 1 + col_off)
        # )

    def from_contours(self, contours, offset=(0, 0)):
        """Sets the mask, given the contour points:
        list of numpy.arrays with the shape (n, 2),
        where each index i is on point in the polygon
        """

        if len(contours) == 0:
            msg = 'Number of polygons is 0'
            raise ValueError(msg)

        self.contours = contours

        self._set_mask(offset=offset)


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

        self.mask = mask.astype(bool). copy() # explicit copy
        # if offset != (0, 0):
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
        # mode = cv2.RETR_EXTERNAL
        mode = cv2.RETR_LIST
        # offset is taken from slice

        major = cv2.__version__.split('.')[0]

        if major == '3':
            _, contours, _ = cv2.findContours(
                self.mask.astype(np.uint8), mode, method)
        else:
            contours, _ = cv2.findContours(
                self.mask.astype(np.uint8), mode, method)

        self.contours = [cont.squeeze() for cont in contours]

        if self.mask_slice is None:
            return

        shiftedContours = []
        for cont in self.contours:
            row_of, col_of = self.mask_slice
            cont[:,0] += col_of.start
            cont[:,1] += row_of.start
            shiftedContours.append(cont)
        self.contours = shiftedContours

    def makeGFX(self, brush=None, pen=None):
        """
        Creates new GFX object
        """
        self.GFX = GFX(self, brush, pen)

        return self.GFX

    def removeGFX(self, parentEid=None):
        """ Removes GFX object
        """
        self.historical = True
        self.parentEid = parentEid
        self.GFX = None
