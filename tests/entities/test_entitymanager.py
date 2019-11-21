import warnings
import pytest
import cv2
from pathlib import Path
import numpy as np

from cellinspector.entities import Entity, EntityManager, read_into_manager

#TODO testcases for more interesting from
#FIXME path = np.array([[1, 1], [1, 5], [5, 5], [5, 1]])
#FIXME will yield a a mask with trailing 0...
#FIXME intervalls, test if and how points are inclusive or not
#FIXME put into entity manager tests 


def test_make_entities():
    """test if double ids raise error
    and id is always an integer
    """

    eman = EntityManager()
    eman.clear()

    # must fail as 0 ist invalid ID
    with pytest.raises(ValueError):
        _ = eman.make_entity(0)

    # must fail as 1.0 is not int
    with pytest.raises(ValueError):
        _ = eman.make_entity(1.0)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i in range(1, 10):
        _ = eman.make_entity(i)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 22, 30, 100]
    for i in (20, 100, 30, 22):
        _ = eman.make_entity(i)

    # must fail as 9 is alread in use
    with pytest.raises(ValueError):
        _ = eman.make_entity(9)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 22, 30, 100]
    ent = eman.make_entity(10)
    assert ent.eid == 10

    # must work as next smalles free id is 11
    ent = eman.make_entity()
    assert ent.eid == 11

    # fill up...
    # id now are [1 ... 20, 22, 30, 100]
    for _ in range(8):
        ent = eman.make_entity()

    # next free id must be 21
    ent = eman.make_entity()
    assert ent.eid == 21

def test_add_entities():
    """test if double ids raise error
    and id is always an integer
    """

    eman = EntityManager()
    eman.clear()

    # must fail as 0 ist invalid ID
    with pytest.raises(ValueError):
        new_ent = Entity(0)
        eman.addEntity(new_ent)

    # must fail as 1.1 cannot cast into int w/o remainder
    with pytest.raises(ValueError):
        new_ent = Entity(1.1)
        eman.addEntity(new_ent)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i in range(1, 10):
        new_ent = Entity(i)
        eman.addEntity(new_ent)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 22, 30, 100]
    for i in (20, 100, 30, 22):
        new_ent = Entity(i)
        eman.addEntity(new_ent)

    # must fail as 9 is alread in use
    with pytest.raises(ValueError):
        new_ent = Entity(9)
        eman.addEntity(new_ent)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 22, 30, 100]
    new_ent = Entity(10)
    eman.addEntity(new_ent)
    assert new_ent.eid == 10

    # fill up...
    # id now are [1 ... 20, 22, 30, 100]
    for i in range(11, 20):
        new_ent = Entity(i)
        eman.addEntity(new_ent)

    # next free id must be 21
    ent = eman.make_entity()
    assert ent.eid == 21

def test_large_eids():
    """Test adding lage numbers
    """
    eman = EntityManager()
    eman.clear()

    eman.make_entity(32768)

    new_ent = Entity(int(0xffff))
    eman.addEntity(new_ent)

def testCreationFromMap():
    """ test if creation of entities from map works
    """
    test_path = Path('../../tests/res/testmask.png')
    if not test_path.exists():
        test_path = Path('./tests/res/testmask.png')
    if not test_path.exists():
        raise ValueError('testmask not found!')

    pixmap = cv2.imread(str(test_path), cv2.IMREAD_ANYDEPTH)
    pixmap = pixmap.astype(int)
    uniqueNums = np.unique(pixmap).size - 1 # minus zero


    eman = EntityManager()
    eman.clear()
    eman.generateFromPixelmap(pixmap)

    assert len(eman) == uniqueNums

def testCreationFromJson():
    """ test if creation of entities from json works
    """
    test_mask = Path('../../tests/res/testmask.png')
    test_json = Path('../../tests/res/testmask.png.json')
    if not test_mask.exists():
        test_mask = Path('./tests/res/testmask.png')
        test_json = Path('./tests/res/testmask.png.json')
    if not test_mask.exists() or not test_json.exists():
        raise ValueError('testmask not found!')

    pixmap = cv2.imread(str(test_mask), cv2.IMREAD_ANYDEPTH)
    pixmap = pixmap.astype(int)
    uniqueNums = np.unique(pixmap) # minus zero

    eman = EntityManager()
    read_into_manager(test_json, eman)
    
    for uid in uniqueNums:
        if uid: # > 0
            assert not eman.getEntity(uid) is None
        else:
            assert eman.getEntity(uid) is None

def testCreationFromMapShapes():
    """ test if creation of entities from map works
    """
    test_path = Path('../../tests/res/testmask.png')
    if not test_path.exists():
        test_path = Path('./tests/res/testmask.png')
    if not test_path.exists():
        raise ValueError('testmask not found!')

    pixmap = cv2.imread(str(test_path), cv2.IMREAD_ANYDEPTH)
    pixmap = pixmap.astype(int)

    eman = EntityManager()
    eman.clear()
    eman.generateFromPixelmap(pixmap)

    allSame = True
    for entity in eman:
        same = np.all(pixmap[entity.mask_slice] == entity.mask * entity.eid)
        if entity.eid != 48277:
            allSame = allSame and same
        warnings.warn('The cornercase of detatched contours is not handled!')
    assert allSame

def testCreationFromMapContours():
    """ test if creation of entities from map works
    """
    test_path = Path('../../tests/res/testmask.png')
    if not test_path.exists():
        test_path = Path('./tests/res/testmask.png')
    if not test_path.exists():
        raise ValueError('testmask not found!')

    pixmap = cv2.imread(str(test_path), cv2.IMREAD_ANYDEPTH)
    pixmap = pixmap.astype(int)

    # pixmap[pixmap == 48277] = 0
    # warnings.warn('The cornercase of detatched contours is not handled!')

    # pixmap[pixmap != 24514] = 0
    # warnings.warn('The cornercase of detatched contours is not handled!')

    eman = EntityManager()
    eman.clear()
    eman.generateFromPixelmap(pixmap)

    canvas = np.zeros(pixmap.shape, np.int32)
    allSame = True
    for entity in eman:
        cont = entity.contours
        ret = cv2.drawContours(canvas, cont, -1, entity.eid, -1)
        # canvas = ret.get()
        same = np.all(ret[ret == entity.eid] == pixmap[pixmap == entity.eid])
        # print(entity.eid, same, len(cont), [len(cnt) for cnt in cont])
        allSame = same and allSame

    # import matplotlib.pyplot as plt
    # f, ax = plt.subplots(1, 2, sharex=True, sharey=True)
    # ax[0].imshow(pixmap, vmin=pixmap.min(), vmax=pixmap.max())
    # ax[1].imshow(canvas, vmin=pixmap.min(), vmax=pixmap.max())
    # plt.show()

    assert allSame

def testNotSingleton():

    emanAB = EntityManager()
    emanAB.clear()

    emanBA = EntityManager()
    emanBA.clear()

    assert not emanAB is emanBA

    eidA = 10
    eidB = 7

    # add entities
    entABa = emanAB.make_entity(eidA)
    entBAb = emanBA.make_entity(eidB)

    # check that they ar invalid in the creating 
    # manager but still valid in the other
    with pytest.raises(ValueError):
        _ = emanAB.make_entity(eidA)
    entABb = emanAB.make_entity(eidB)

    with pytest.raises(ValueError):
        _ = emanBA.make_entity(eidB)
    entBAa = emanBA.make_entity(eidA)

    for eid in (eidA, eidB):
        with pytest.raises(ValueError):
            _ = emanAB.make_entity(eid)
        with pytest.raises(ValueError):
            _ = emanBA.make_entity(eid)

    assert entABa.eid == entBAa.eid
    assert entABb.eid == entBAb.eid

def testGenerateFromContours():
    eman = EntityManager()
    eman.clear()

    contours = [np.array([[0, 7], [0, 9], [9, 9], [9, 7]], dtype=np.int32),
                np.array([[1, 0], [1, 3], [8, 3], [8, 0]], dtype=np.int32)]
    # path = np.array(
    #     [[0, 0],
    #      [0, 3],
    #      [3, 3],
    #      [3, 0]],
    #     np.int32)

    contourData = [(5, contours), (10, [c+5 for c in contours])]

    eman.generateFromContours(contourData)

def testEntityIterator():

    eman = EntityManager()
    eman.clear()

    requested = set(int(v) for v in np.random.randint(1, 100, 10))
    for eid in requested:
        eman.make_entity(entity_id=eid)

    # test the generator
    all_eids = set([entity.eid for entity in eman])

    assert all_eids == requested

