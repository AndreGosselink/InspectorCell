"""Unit testing for MapGen class
"""
from pathlib import Path

import pytest
import pytest_mock as mocker

import numpy as np

from dataframework.container import MapGen, ImageStack, ObjGen

from conftest import (SOME_LARGE_IMG, MANY_SMALL_IMG, SOME_SMALL_IMG,
                      MY_OME_REF, FS_TIF_REF, get_object_data)

def test_mapgen_creation():
    """test if MapGen exists
    """
    mpg = MapGen()
    assert not mpg is None

def test_object_map():
    """Test generation of object maps
    """
    objid_map = np.zeros((5, 5, 1), dtype=np.uint16)
    obj0 = np.s_[1, 1:3, :]
    obj1 = np.s_[2, 2:4, :]
    obj2 = np.s_[3, 0:3, :]

    objid_map[obj0] = 1
    objid_map[obj1] = 2
    objid_map[obj2] = 3

    objid_map = objid_map.squeeze()

    mpg = MapGen(objid_map=objid_map)
    ret_mask = mpg.get_object_overlay()

    # assert rgb output
    assert ret_mask.shape[:2] == objid_map.shape[:2]
    assert ret_mask.shape[2] == 4

    for obj in [obj0, obj1, obj2]:
        # assert objects are not black
        assert np.all(ret_mask[obj] != (0, 0, 0, 0))
        # each pixel in the object has the same color
        assert np.all(ret_mask[obj] - ret_mask[obj][0,:] == 0)

    # assert objects are different
    col0 = ret_mask[obj0]
    col1 = ret_mask[obj1]
    col2 = ret_mask[obj2]

    # assert objects have different colors
    for px_col in col0[:, :3]:
        assert np.all(px_col != col1[:, :3])
        assert np.all(px_col != col2[:, :3])
    for px_col in col1[:, :3]:
        assert np.all(px_col != col2[:, :3])

    # assert non objects are black
    # blanking out all objects...
    ret_mask[obj0] = 0
    ret_mask[obj1] = 0
    ret_mask[obj2] = 0
    # everything besides the alpha channel should be 0
    assert np.all(ret_mask[:, :, :3] == 0)


def test_object_map_not_set_error():
    """Test generation of object maps
    """
    obj0, obj1, objid_map = get_object_data()
    mpg = MapGen()

    with pytest.raises(ValueError):
        ret_mask = mpg.get_object_overlay()

def test_invalid_merg():
    """Test generation of object maps
    """
    obj0, obj1, objid_map = get_object_data()
    mpg = MapGen(objid_map=objid_map)

    with pytest.raises(ValueError):
        mpg.get_merge_overlay([])

    with pytest.raises(ValueError):
        mpg.get_merge_overlay(['a', 'b', 'c', 'd'])

def test_merge_overlay(mocker):
    """Test generation of object maps
    """
    obj0, obj1, objid_map = get_object_data()
    # 1 and 2 are to small, get lost during scaling
    objid_map *= 257
    r_ch = objid_map
    marker_names = [None, 'Bernd', None]

    ims = ImageStack()
    mocker.patch.object(ims, 'get_imagedata')
    ims.get_imagedata.return_value = r_ch
    ims.shape = r_ch.shape
    ims._zeros = np.zeros(r_ch.shape)

    mpg = MapGen(image_stack=ims)

    merge = mpg.get_merge_overlay(marker_names)
    rgb0 = np.round([0, 1, 0, 255])
    rgb1 = np.round([0, 2, 0, 255])
    assert np.all(merge[obj0] == rgb0)
    assert np.all(merge[obj1] == rgb1)

def test_merge_overlay_error(mocker):
    """Test generation of object maps
    """
    obj0, obj1, objid_map = get_object_data()
    r_ch = objid_map
    marker_names = [None]

    ims = ImageStack()
    mocker.patch.object(ims, 'get_imagedata')
    ims.get_imagedata.return_value = r_ch
    ims.shape = r_ch.shape
    ims._zeros = np.zeros(r_ch.shape)

    mpg = MapGen(image_stack=ims)

    with pytest.raises(ValueError):
        merge = mpg.get_merge_overlay(marker_names)

def test_tagcolor_overlay(mocker):
    """Test generation of cluster_id maps
    """
    bboxes = [(42, 10, 60, 60, 110, ['cl0', 'hi']),
              (99, 33, 83, 111, 192, ['cl1', 'bernd']),
              (6, 3, 8, 1, 9, ['cl1', 'bernd']),
              (101, 133, 183, 1111, 1192, ['NOT_MEEE', 'otto']),
              ]

    mpg = MapGen(objid_map=mocker.Mock(), obj_gen=mocker.Mock())
    mpg.obj_gen.objects = []
    mpg.objid_map.shape = (5000, 3000)

    # build fake objects
    for oid, rmin, rmax, cmin, cmax, tags in bboxes:
        mock_obj = mocker.Mock()
        mock_obj.id = oid
        mock_obj.slice = np.s_[rmin:(rmax+1), cmin:(cmax+1)]
        mock_obj.bmask = np.ones((rmax-rmin+1, cmax-cmin+1), bool)
        mock_obj.bbox = (rmin, rmax, cmin, cmax)
        mock_obj.tags = set(tags)
        mpg.obj_gen.objects.append(mock_obj)


    ret_mask = mpg.get_tagcolor_overlay(tags=['cl0', 'cl1'],
                                        alpha=1.0/255.0)

    # assert correct spatial dim
    assert ret_mask.shape[:-1] == mpg.objid_map.shape

    # ditch alpha
    alphas = ret_mask[:, :, 3]
    ret_mask = ret_mask[:, :, :3]
    assert np.all(alphas == 1)

    # check just for cluster selected objects
    col_values = []
    colored = 0
    for _, rmin, rmax, cmin, cmax, _ in bboxes[:-1]:
        vals = ret_mask[rmin:rmax+1, cmin:cmax+1]
        # assert all cluster colors are same for a object
        rgb = vals[0, 0]
        assert np.all(vals == rgb)
        col_values.append(rgb.copy())
        # remove this object for background checking later on
        colored += ret_mask[rmin:rmax+1, cmin:cmax+1].size

    # assert different colouring fo different cluster
    assert np.sum(col_values[0] != col_values[1]) >= 1
    # assert same colouring fo same cluster
    assert np.all(col_values[1] == col_values[2])

    # assert after blanking all coloured/cluster object
    # nothing else was stained
    total = ret_mask.size
    assert np.sum(ret_mask > 0) == colored
    assert np.sum(ret_mask == 0) == total - colored

def test_invalid_tagcluster(mocker):
    """Test if ambigious cluster tags fail
    """
    bad_id = 99
    bboxes = [(42, 10, 60, 60, 110, ['cl0', 'hi']),
              (bad_id, 33, 83, 111, 192, ['cl1', 'cl0']),
              (101, 133, 183, 1111, 1192, ['NOT_MEEE', 'otto']),
              ]

    mpg = MapGen(objid_map=mocker.Mock(), obj_gen=mocker.Mock())
    mpg.obj_gen.objects = []
    mpg.objid_map.shape = (5000, 3000)

    # build fake objects
    for oid, rmin, rmax, cmin, cmax, tags in bboxes:
        mock_obj = mocker.Mock()
        mock_obj.id = oid
        mock_obj.slice = np.s_[rmin:(rmax+1), cmin:(cmax+1)]
        mock_obj.bmask = np.ones((rmax-rmin+1, cmax-cmin+1), bool)
        mock_obj.bbox = (rmin, rmax, cmin, cmax)
        mock_obj.tags = tags
        mpg.obj_gen.objects.append(mock_obj)

    with pytest.raises(ValueError) as err:
        mpg.get_tagcolor_overlay(
            tags=['cl0', 'cl1'], alpha=1.0/255.0)

    assert 'Object.id {}'.format(bad_id) in str(err)

def test_tagcolor_const(mocker):
    """Test generation of cluster_id maps
    """
    bboxes = [(42, 10, 60, 60, 110, ['cl0', 'hi']),
              (99, 33, 83, 111, 192, ['cl1', 'bernd']),
              (6, 3, 8, 1, 9, ['cl1', 'bernd']),
              (101, 133, 183, 1111, 1192, ['NOT_MEEE', 'otto']),
              ]

    mpg = MapGen(objid_map=mocker.Mock(), obj_gen=mocker.Mock())
    mpg.obj_gen.objects = []
    mpg.objid_map.shape = (5000, 3000)

    # build fake objects
    for oid, rmin, rmax, cmin, cmax, tags in bboxes:
        mock_obj = mocker.Mock()
        mock_obj.id = oid
        mock_obj.slice = np.s_[rmin:(rmax+1), cmin:(cmax+1)]
        mock_obj.bmask = np.ones((rmax-rmin+1, cmax-cmin+1), bool)
        mock_obj.bbox = (rmin, rmax, cmin, cmax)
        mock_obj.tags = set(tags)
        mpg.obj_gen.objects.append(mock_obj)


    ret_mask_old = mpg.get_tagcolor_overlay(tags=['cl0', 'cl1'],
                                            alpha=1.0/255.0)

    ret_mask_new = mpg.get_tagcolor_overlay(tags=['cl0', 'cl1', 'otto'],
                                            alpha=1.0/255.0)

    ret_mask_old = ret_mask_old[:, :, :3]
    ret_mask_new = ret_mask_new[:, :, :3]

    # import matplotlib.pyplot as plt
    # f, ax = plt.subplots(1, 2, sharex=True, sharey=True)
    # ax[0].imshow(ret_mask_old)
    # ax[1].imshow(ret_mask_new)
    # plt.show()

    # first object should be same coloured in every mask
    _, rmin, rmax, cmin, cmax, _ = bboxes[0]
    vals_old = ret_mask_old[rmin:rmax+1, cmin:cmax+1]
    vals_new = ret_mask_new[rmin:rmax+1, cmin:cmax+1]
    assert np.all(vals_old[0, 0] == vals_new[0, 0])

    # the newly added tag cluster shoudl missmatch however
    _, rmin, rmax, cmin, cmax, _ = bboxes[-1]
    vals_old = ret_mask_old[rmin:rmax+1, cmin:cmax+1]
    vals_new = ret_mask_new[rmin:rmax+1, cmin:cmax+1]
    assert np.all(vals_old[0, 0] != vals_new[0, 0])
