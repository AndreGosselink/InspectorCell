import cv2
import pytest
import numpy as np
from PyQt5.QtCore import QRectF

from cellinspector.entities.entity import contoursToPath, pathToContours, Entity


def test_from_contours():
    mask = np.zeros((10, 10), np.uint8)
    mask[0:4, 1:9] = 1
    mask[7:10, 0:10] = 1
    mask_slice = np.s_[0:10, 0:10]
    mask_slice_off = np.s_[0:10, 5:15]
    boundingbox = QRectF(0.0, 0.0, 9.0, 9.0)

    ent = Entity(1)
    pol = [np.array([[0, 7], [0, 9], [9, 9], [9, 7], ], dtype=np.int32),
           np.array([[1, 0], [1, 3], [8, 3], [8, 0], ], dtype=np.int32)]
    ent.from_contours(pol)

    assert np.array_equal(ent.mask, mask)
    assert ent.mask_slice == mask_slice
    assert ent.mask_slice != mask_slice_off
    assert ent.boundingbox == boundingbox


def test_from_map_invalid():
    mask = np.ones((5, 5), bool)
    mask_slice = np.s_[0:4, 0:4]

    ent = Entity(1)
    with pytest.raises(ValueError):
        ent.from_mask(mask_slice, mask)


def test_from_map():
    mask = np.ones((5, 5), bool)
    mask[1:3, 2:4] = 0
    mask_slice = np.s_[0:5, 0:5]

    ent = Entity(1)
    ent.from_mask(mask_slice, mask)

    assert np.all(ent.mask == mask)
    assert not ent.mask is mask
    assert ent.mask_slice == mask_slice


def test_from_map_offset():
    mask = np.ones((5, 5), bool)
    mask[1:3, 2:4] = 0
    mask_slice = np.s_[0:5, 0:5]
    mask_slice_off = np.s_[3:8, 5:10]

    ent = Entity(1)
    ent.from_mask(mask_slice, mask, offset=(3, 5))

    assert np.all(ent.mask == mask)
    assert not ent.mask is mask
    assert ent.mask_slice == mask_slice_off


def test_set_contours():
    mask = np.ones((5, 5), bool)
    mask[1:3, 2:] = 0
    mask_slice = np.s_[0:5, 0:5]
    boundingbox = QRectF(0.0, 0.0, 4.0, 4.0)

    ent = Entity(1)
    ent.from_mask(mask_slice, mask)

    ought_contours = [np.array([
        [0, 0],
        [0, 4],
        [4, 4],
        [4, 3],
        [2, 3],
        [1, 2],
        [1, 1],
        [2, 0],
        [4, 0],
    ], dtype=np.int32)]

    assert len(ent.contours) == len(ought_contours)
    assert np.all(ent.contours[0] == ought_contours[0])
    assert ent.boundingbox == boundingbox


def testContoursToPath():

    contours = [np.array([[0, 7], [0, 9], [9, 9], [9, 7], ], dtype=np.int32),
                np.array([[1, 0], [1, 3], [8, 3], [8, 0], ], dtype=np.int32)]

    path = contoursToPath(contours)

    contoursBack = pathToContours(path)

    mask1 = np.zeros((10, 10), np.uint8)
    cv2.drawContours(mask1, contours, -1, 1, -1)

    mask2 = np.zeros((10, 10), np.uint8)
    cv2.drawContours(mask2, contoursBack, -1, 1, -1)

    assert not mask1 is mask2
