"""Basic Entity in an image stack, that claims some pixel in a multiplexed
image stack"""

from typing import Tuple, List
from dataclasses import field, dataclass

import numpy as np

# TODO allow scikti-image backend
from cv2 import drawContours

from .entity import Entity


@dataclass
class ImageEntity(Entity):
    """Entity for use with miscmics.ImageStack
    """
    mask: np.ndarray = field(default_factory=list)

    # List[RowSlice, ColSlice]
    slc: Tuple[slice] = field(default_factory=tuple)
    contour: List[np.ndarray] = field(default_factory=list)

    # Contour[ Shape[ Point[col, row] ]]
    int_contour: List[np.ndarray] = field(default_factory=list)

    # separate int BBox and float BBox
    # BoundingBox[ Point[col, row] ]
    bbox: np.ndarray = field(default_factory=list) # is int

    def __post_init__(self):
        if np.any(self.contour):
            self.update_contour(self.contour)

    def _set_int_contour(self):
        self.int_contour = []
        for cnt in self.contour:
            cnt = np.array(cnt)
            # center = np.sum(cnt, 0) / len(cnt)
            # dirs = cnt - center
            # int_contour.append(np.round(center) + np.round(dirs))
            self.int_contour.append(np.round(cnt).astype(int))

    def _set_bbox_and_slice(self):
        # split apln points in inner of contours
        mins = []
        maxs = []
        # Boundingbox is defined by two corner points
        self.bbox = np.empty((2, 2), dtype=int)
        for int_cnt in self.int_contour:
            point = int_cnt.reshape(-1, 2)
            mins.append(np.min(point, 0))
            maxs.append(np.max(point, 0))

        self.bbox[0] = np.min(mins, 0)
        self.bbox[1] = np.max(maxs, 0)

        bounds = (self.bbox.T + [0, 1]).T
        self.slc = (
            slice(*bounds[:, 1].astype(int)),
            slice(*bounds[:, 0].astype(int)),
        )

    def _set_mask(self):
        left_top, right_bottom = self.bbox

        height, width = (right_bottom - left_top)

        self.mask = np.zeros((width+1, height+1), np.uint8)

        drawContours(
            image=self.mask,
            contours=self.int_contour,
            contourIdx=-1,
            color=1,
            thickness=-1,
            # lineType=None,
            # hierarchy=None,
            # maxLevel=None,
            offset=tuple(-left_top),
        )

        self.mask = self.mask.astype(bool)

    def update_contour(self, new_contour: List[List[List[float]]]):
        """Updates the entity contour and all derived attributes

        Notes
        -----
        Will set the `slc`, `mask` and `int_contour`. Setting `contour`
        attribute directly will not change these.
        """
        # probe contour for first point
        try:
            # might raise index errors
            self.contour = [np.array(cnt) for cnt in new_contour]
            self._set_int_contour()

            # might raise value errors (zero size arrays)
            self._set_bbox_and_slice()

        except (IndexError, ValueError):
            raise ValueError(f'Invalid contour can not be set: {new_contour} ')

        self._set_mask()
