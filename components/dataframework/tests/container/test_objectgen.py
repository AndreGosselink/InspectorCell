"""Unit testing for ObjGen class and ImgObj
"""
from pathlib import Path

import pytest
# import pytest_mock as mocker

import numpy as np

from dataframework.container import ObjGen
from dataframework.container.objectgen import ImgObj, get_masks

from conftest import get_object_data

# def _print_ascii(boolarr):
#     img = []
#     for l in boolarr:
#         r = ''
#         for px in l:
#             if px: r += 'X'
#             else: r += ' '
#         img.append(r)
#     print('\n'.join(img))

def test_creation():
    """test if all deps work
    """
    mock = np.zeros((5, 5), dtype=np.uint16)
    obg = ObjGen(mock)
    assert not obg is None

def test_invalid_map():
    """test enforcement of correct datatype
    """
    _, _, objid_map = get_object_data()

    with pytest.raises(ValueError):
        obg = ObjGen(objid_map.astype(float))

def test_object_masks():
    """test if the submask work, boundingboxes are correct
    and so on and so forth
    """
    objid = 42
    points = [(5, 5), (5, 6),
              (6, 4), (6, 5), (6, 6),
              (7, 3), (7, 4), (7, 5),
              (8, 4), (8, 5), (8, 6),
              (9, 4), (9, 5)
             ]

    img_vals = np.arange(10, 16*18+10).reshape(16, 18)
    objid_map = np.zeros(img_vals.shape, np.uint16)
    bool_mask = np.zeros(img_vals.shape, bool)

    extr = [np.inf, 0, np.inf, 0]
    for row, col in points:
        for i, val in enumerate([row, col]):
            extr_i = i * 2
            if val <= extr[extr_i]:
                extr[extr_i] = val
            if val >= extr[extr_i+1]:
                extr[extr_i+1] = val
        objid_map[row, col] = objid
        bool_mask[row, col] = True

    obj_values_ought = img_vals[bool_mask]

    obg = ObjGen(objid_map)

    obj = obg.objects[0]
    assert obj.id == 42

    obj_values_is = img_vals[obj.slice][obj.bmask]
    assert np.all(obj_values_is == obj_values_ought)

    rmin, rmax, cmin, cmax = obj.bbox
    rmin_ought, rmax_ought, cmin_ought, cmax_ought = extr
    assert rmin == rmin_ought
    assert rmax == rmax_ought
    assert cmin == cmin_ought
    assert cmax == cmax_ought

def test_loading_from_map():
    """test generating objects from idmap
    """
    sli0, sli1, objid_map = get_object_data()
    sli2 = np.s_[20:25, 30:35]
    objid_map[sli2] = 35

    obg = ObjGen(objid_map)

    assert obg.objects[0].id == 1
    assert obg.objects[1].id == 2
    assert obg.objects[2].id == 35

    assert obg.get_object(1).id == 1
    assert obg.get_object(2).id == 2
    assert obg.get_object(35).id == 35

    for obj, sli in zip(obg.objects, [sli0, sli1, sli2]):
        rbound = sli[0]
        cbound = sli[1]
        rmin, rmax = (rbound.start, rbound.stop-1)
        cmin, cmax = (cbound.start, cbound.stop-1)
        if rmin < 0 and rmax < 0:
            rmin += objid_map.shape[0]
            rmax += objid_map.shape[0]
        if cmin < 0 and cmax < 0:
            cmin += objid_map.shape[1]
            cmax += objid_map.shape[1]
        assert obj.bbox == (rmin, rmax, cmin, cmax)

def test_obj_creation():
    """test object creation and api
    """
    obj = ImgObj(5)

    assert obj.tags == set([])
    assert obj.id == 5
    assert obj.bbox is None
    assert obj.slice is None

def test_invalid_obj():
    """test raising of errors
    """
    with pytest.raises(ValueError):
        _ = ImgObj(0)

def test_obj_ordering():
    """test object oredering based on id
    """
    obj0 = ImgObj(1)
    obj1 = ImgObj(2)

    assert obj0 != obj1
    assert obj0 < obj1

    olist = [obj1, obj0]
    assert not olist[0] is obj0
    assert not olist[1] is obj1
    olist.sort()
    assert olist[0] is obj0
    assert olist[1] is obj1

def test_get_nonexisting_id():
    """test object oredering based on id
    """
    # black map
    omap = np.zeros((100, 100), np.uint16)
    # put in some objets
    omap[0:4,0:4] = np.arange(4*4).reshape(4, 4)
    obg = ObjGen(omap)

    # assert the map was usefull
    assert len(obg.objects) == 15

    # assert we have all objects as defined by the map
    for i in range(1, 16):
        valid_obj = obg.get_object(i)
        assert valid_obj.id == i

    with pytest.raises(KeyError):
        _ = obg.get_object(0)

    with pytest.raises(KeyError):
        _ = obg.get_object(0)

def test_add_obj():
    omap = np.zeros((60, 60), np.uint16)
    # put in some objets
    omap[0:4,0:4] = np.arange(4*4).reshape(4, 4)
    obg = ObjGen(omap)

    obj = ImgObj(objid=99)
    mask = np.array([
        [0, 1, 0],
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0],
        [0, 1, 0],
    ], dtype=bool)
    obj.set_masks_slice((50, 54, 49, 51), mask.copy())

    obg.add_object(obj)
    assert np.all(obg._objid_map[50:54+1, 49:51+1][mask] == 99)
    assert obj in obg.objects

def test_del_obj():
    omap = np.zeros((60, 60), np.uint16)
    # put in some objets
    omap[0:4, 0:4] = np.arange(4*4).reshape(4, 4)
    obg = ObjGen(omap)

    assert obg._objid_map[3, 3] == 15
    deleted = obg.delete_object(15)
    assert not deleted in obg.objects
    assert obg._objid_map[3, 3] == 0

def test_loading_from_map_threaded():
    """test generating objects from idmap
    """
    objid_map = np.zeros((50, 50), dtype='uint16')
    sli0 = np.s_[5:10, 5:10]
    sli1 = np.s_[-10:-5, -10:-5]
    sli2 = np.s_[20:25, 30:35]
    objid_map[sli0] = 1
    objid_map[sli1] = 2
    objid_map[sli2] = 35

    obg = ObjGen()
    obg.generate_objects_threaded(objid_map, 2)

    assert obg.objects[0].id == 1
    assert obg.objects[1].id == 2
    assert obg.objects[2].id == 35

    assert obg.get_object(1).id == 1
    assert obg.get_object(2).id == 2
    assert obg.get_object(35).id == 35

    for obj, sli in zip(obg.objects, [sli0, sli1, sli2]):
        rbound = sli[0]
        cbound = sli[1]
        rmin, rmax = (rbound.start, rbound.stop-1)
        cmin, cmax = (cbound.start, cbound.stop-1)
        if rmin < 0 and rmax < 0:
            rmin += objid_map.shape[0]
            rmax += objid_map.shape[0]
        if cmin < 0 and cmax < 0:
            cmin += objid_map.shape[1]
            cmax += objid_map.shape[1]
        assert obj.bbox == (rmin, rmax, cmin, cmax)

def test_get_masks():
    obj_mask = np.zeros((300, 500), np.uint16)

    cur_id = 0
    obj_ids = []
    for r in (10, 100, 250):
        for c in (5, 230, 450):
            cur_id += 1
            obj_ids.append(cur_id)
            obj_mask[r:r+10, c:c+8] = cur_id
            obj_mask[r+5, c+3] = 0
            obj_mask[r, c] = 0

    ref_mask = np.ones((10, 8), bool)
    ref_mask[0, 0] = 0
    ref_mask[5, 3] = 0
    for cur_id in obj_ids:
        bbox, bmask = get_masks(cur_id, obj_mask)
        assert bmask.shape == ref_mask.shape
        assert np.all(bmask == ref_mask)
        r0, r1, c0, c1 = bbox
        a_slice = np.s_[r0:r1+1, c0:c1+1]
        assert np.all(obj_mask[a_slice][bmask] == cur_id)
        assert np.all(obj_mask[a_slice][~bmask] == 0)

    # obg = ObjGen()
    # obg.generate_objects(obj_mask)

def test_get_obj_gens():
    """test generating generators
    """
    objid_map = np.zeros((50, 50), dtype='uint16')
    sli0 = np.s_[5:10, 5:10]
    sli1 = np.s_[-10:-5, -10:-5]
    sli2 = np.s_[20:25, 30:35]
    objid_map[sli0] = 1
    objid_map[sli1] = 2
    objid_map[sli2] = 35

    obg = ObjGen()

    for gen_count in (1, 2, 3):
        gens = obg.get_object_generators(objid_map, gen_count)

        ids = set([])
        for gen in gens:
            for obj in gen:
                ids.add(obj.id)

        assert ids == set([1, 2, 35])

