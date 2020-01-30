import cv2
import pytest
import numpy as np
from PyQt5.QtCore import QRectF

from inspectorcell.entities.entity import contoursToPath, pathToContours, Entity


def test_from_contours():
    """Test generation of entity
    """
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

def test_from_contours_offset_small():
    """Test generation of entity with offset
    """
    src_img = np.zeros(20 * 20, np.uint16).reshape(20, 20)
    dst_img = np.zeros(20 * 20, np.uint16).reshape(20, 20)

    src_img[10:15,2:5] = 10
    src_contour = [
        np.array(
            [[2, 10],
             [2, 14],
             [4, 14],
             [4, 10]], int)
    ]

    ent = Entity(10)
    ent.from_contours(src_contour)

    # repaint
    dst_img[ent.mask_slice][ent.mask] = ent.eid
    
    assert np.all(src_img == dst_img)


def test_from_contours_offset_large():
    """Test generation of entity with offset
    """
    src_img = np.zeros(200 * 200, np.uint16).reshape(200, 200)
    dst_img = np.zeros(200 * 200, np.uint16).reshape(200, 200)

    eid0 = 10
    eid1 = 54030
    
    # smaller cont
    src_img[10:15,2:5] = eid0
    cont0 = [
        np.array(
            [[2, 10],
             [2, 14],
             [4, 14],
             [4, 10]], int)
    ]

    # larger cont
    src_img[50:71,20:49] = eid1
    src_img[70:81,25:50] = eid1
    src_img[72:81,24:26] = eid1
    cont1 = [
        np.array(
            [[20, 50],
             [20, 70],
             [25, 70],
             [25, 72],
             [24, 72],
             [24, 80],
             [49, 80],
             [49, 70],
             [48, 70],
             [48, 50]], int)
    ]

    ent0 = Entity(eid0)
    ent0.from_contours(cont0)

    ent1 = Entity(eid1)
    ent1.from_contours(cont1)

    dst_img[ent0.mask_slice][ent0.mask] = ent0.eid
    dst_img[ent1.mask_slice][ent1.mask] = ent1.eid
    
    assert np.all(src_img == dst_img)

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

def testFromMapOffset():
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

    contours = [np.array([[0, 7], [0, 9], [9, 9], [9, 7]], dtype=np.int32),
                np.array([[1, 0], [1, 3], [8, 3], [8, 0]], dtype=np.int32)]

    path = contoursToPath(contours)

    contoursBack = pathToContours(path)

    mask1 = np.zeros((10, 10), np.uint8)
    cv2.drawContours(mask1, contours, -1, 1, -1)

    mask2 = np.zeros((10, 10), np.uint8)
    cv2.drawContours(mask2, contoursBack, -1, 1, -1)

    # assert different objects
    assert not mask1 is mask2
    # assert same values
    assert np.all(mask1 == mask2)
    # assert non trivial (not all 0 or all 1)
    assert 0 < np.sum(mask1) < 100
    assert 0 < np.sum(mask2) < 100

def test_from_contours():
    """Test generation of entity
    """
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

def testMoveEntity():
    """Test moving of entities inplace
    """
    # pixmap = np.zeros((20, 20), np.uint16)

    mask = np.array([
    [1, 1, 1, 0, 0, 0],
    [1, 1, 1, 0, 0, 0],
    [1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 1, 1],
    ], bool)
    mask_slice = np.s_[3:8, 5:11]

    ent = Entity(1)
    pol = [np.array([[5, 3], [5, 5], [6, 5], [6, 4], [7, 4], [7, 3] ], dtype=np.int32),
           np.array([[10, 6], [9, 6], [9, 7], [10, 7], ], dtype=np.int32)]
    ent.from_contours(pol)

    assert np.array_equal(ent.mask, mask)
    assert ent.mask_slice == mask_slice
    
    ent.moveBy(3, 4)
    shifted = np.s_[0:5, 1:7]
    assert ent.mask_slice == shifted
    assert ent.mask_slice != mask_slice
    assert np.array_equal(ent.mask, mask)
