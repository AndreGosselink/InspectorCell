import pytest
import numpy as np
from PyQt5.QtCore import QRect

from entity import Entity


def test_from_polygon():
    mask = np.zeros((10, 10), bool)
    mask[0:4, 1:9] = 1
    mask[7:10, 0:10] = 1
    mask_slice = np.s_[0:10, 0:10]
    mask_slice_off = np.s_[0:10, 5:15]
    boundingbox = QRect(0,0,10,10)

    ent = Entity(1)
    pol = [np.array([[0, 7], [0, 9], [9, 9], [9, 7], ], dtype=np.int32),
           np.array([[1, 0], [1, 3], [8, 3], [8, 0], ], dtype=np.int32)]
    ent.from_polygon(pol)

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
    boundingbox = QRect(0, 0, 5, 5)

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
