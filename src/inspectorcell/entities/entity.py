"""Container for data, masks, graphics items, annotations logic etc. pp.
related to a single, identifyable thingy in an image stack
"""
### Build-Ins
from dataclasses import dataclass

### Extern
from uuid import UUID
import cv2
import numpy as np

from miscmics.entities import ImageEntity, EntityType
from miscmics.processing.entities.extract import mask_to_contour

from PyQt5.QtCore import QPointF, QRectF
from PyQt5.QtGui import QPolygonF, QPainterPath

### Project
from ..graphics.gfx import GFX
from .misc import get_kernel


@dataclass
class Entity(ImageEntity):
    
    _GFX: GFX = None

    def __init__(self, objectId=None, *args, **kwargs):
        if isinstance(objectId, UUID):
            super().__init__(objectId, *args, **kwargs)
        elif isinstance(objectId, int) or isinstance(objectId, float):
            super().__init__(*args, **kwargs)
            if float(objectId) - int(objectId) != 0:
                raise ValueError('Can not convert unambigiously')
            self.scalars['object_id'] = int(objectId)
        else:
            super().__init__(*args, **kwargs)

    @property
    def GFX(self):
        return self._GFX

    @GFX.setter
    def GFX(self, gfx):
        if gfx is None:
            self._gfx = None
            self.contour = []
            self.bbox = np.empty((2, 2), int)
            self.slc = np.s_[:1, :1]
        else:
            self._GFX = gfx

    @property
    def objectId(self):
        return self.scalars['object_id']

    @objectId.setter
    def objectId(self, new_objectid):
        self.scalars['object_id'] = new_objectid

    @property
    def path(self):
        return contoursToPath(self.contour)

    @path.setter
    def path(self, new_path):
        new_cont = pathToContours(new_path)
        self.update_contour(new_cont)

    @property
    def mask_slice(self):
        return self.slc

    @property
    def parentEid(self):
        return self.generic.get('parentId')

    @property
    def historical(self):
        return self.etype == EntityType.Historic

    @historical.setter
    def historical(self, val):
        if val:
            self.etype = EntityType.Historic
        else:
            self.etype = EntityType.Cell

    @property
    def isActive(self):
        return not self.historical

    @isActive.setter
    def isActive(self, val):
        self.historical = not val
    
    # match legacy API
    @property
    def contours(self):
        return self.contour

    @property
    def boundingbox(self):
        """BBox is two points, Boundingbox is point + dims
        """
        top_left, bottom_right = self.bbox
        width, height = bottom_right - top_left
        ptx, pty = top_left
        return QRectF(ptx, pty, width, height)

    def from_contours(self, contours):
        self.update_contour(contours)

    def makeGFX(self, brush=None, pen=None):
        """
        Creates new GFX object
        """
        self.update_contour(self.contours)
        self.GFX = GFX(self, brush, pen)

        return self.GFX

    def removeGFX(self, parentEid=None):
        """ Removes GFX object
        """
        self.historical = True
        if parentEid is not None:
            self.generic['parentEid'] = parentEid
        self.GFX = None

    def from_mask(self, mask_slice, mask, offset=None):
        # work around old inconsistency, where offset is not only determined
        # by mask_slice. But fundamentally they are the very same thing

        if offset is not None:
            mask_slice = [slice(slc.start + off, slc.stop + off, slc.step) \
                          for slc, off in zip(mask_slice, offset)]

        self.update_contour(mask_to_contour(mask_slice, mask))

    def moveBy(self, cols, rows):
        """Offsets Entity inplace by pixels

        Parameters
        ----------
        cols : int
            Number of pixels to move along vertical image axis
        rows : int
            Number of pixels to move along horizontal image axis
        """

        moved_contour = [[(pt0 + rows, pt1 + cols) for (pt0, pt1) in cnt] \
                          for cnt in self.contours]

        self.update_contour(moved_contour)

    def from_polygons(self, polygons):
        """Sets the mask, given the contour points:
        list of numpy.arrays with the shape (n, 2),
        where each index i is on point in the polygon
        """

        if len(polygons) == 0:
            msg = 'Number of polygons is 0'
            raise ValueError(msg)

        new_path = QPainterPath()
        for polygon in polygons:
            new_path.addPolygon(polygon)
        
        new_contour = pathToContours(new_path)
        self.update_contour(new_contour)


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
