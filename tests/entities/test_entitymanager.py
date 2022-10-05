import warnings
import pytest
import cv2
from pathlib import Path
import numpy as np
import random as rnd

from inspectorcell.entities import Entity, EntityManager, read_into_manager

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

    # Gone, as float is okay now
    # # must fail as 1.0 is not int
    # with pytest.raises(ValueError):
    #     _ = eman.make_entity(1.0)

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
    assert ent.objectId == 10

    # dropping the rule that minimum free number must be used
    # # must work as next smalles free id is 11
    # ent = eman.make_entity()
    # assert ent.objectId == 11
    # # fill up...
    # # id now are [1 ... 20, 22, 30, 100]
    # for _ in range(8):
    #     ent = eman.make_entity()
    # # next free id must be 21
    # ent = eman.make_entity()
    # assert ent.objectId == 21


    ent = eman.make_entity()
    assert ent.objectId == 101
    for _ in range(8):
        ent = eman.make_entity()
    ent = eman.make_entity()
    assert ent.objectId == 101 + 8 + 1

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
    assert new_ent.objectId == 10

    # fill up...
    # id now are [1 ... 20, 22, 30, 100]
    for i in range(11, 20):
        new_ent = Entity(i)
        eman.addEntity(new_ent)
    
    # # next free id must be 21
    # ent = eman.make_entity()
    # assert ent.objectId == 21

    # drop unessescary min int objectid
    ent = eman.make_entity()
    assert ent.objectId == 101

def test_large_objectIds():
    """Test adding lage numbers
    """
    eman = EntityManager()
    eman.clear()

    eman.make_entity(objectId=32768)

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
            assert not eman.lookupEntity(objectId=uid) is None
        else:
            assert eman.lookupEntity(objectId=uid) is None

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
        same = np.all(pixmap[entity.mask_slice] == entity.mask * entity.objectId)
        if entity.objectId != 48277:
            allSame = allSame and same
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
        ret = cv2.drawContours(canvas, cont, -1, entity.objectId, -1)
        # canvas = ret.get()
        same = np.all(ret[ret == entity.objectId] == pixmap[pixmap == entity.objectId])
        # print(entity.objectId, same, len(cont), [len(cnt) for cnt in cont])
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

    objectIdA = 10
    objectIdB = 7

    # add entities
    entABa = emanAB.make_entity(objectIdA)
    entBAb = emanBA.make_entity(objectIdB)

    # check that they ar invalid in the creating 
    # manager but still valid in the other
    with pytest.raises(ValueError):
        _ = emanAB.make_entity(objectIdA)
    entABb = emanAB.make_entity(objectIdB)

    with pytest.raises(ValueError):
        _ = emanBA.make_entity(objectIdB)
    entBAa = emanBA.make_entity(objectIdA)

    for objectId in (objectIdA, objectIdB):
        with pytest.raises(ValueError):
            _ = emanAB.make_entity(objectId)
        with pytest.raises(ValueError):
            _ = emanBA.make_entity(objectId)

    assert entABa.objectId == entBAa.objectId
    assert entABb.objectId == entBAb.objectId

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
    for objectId in requested:
        eman.make_entity(objectId=objectId)
    
    # test the generators
    assert requested == set([entity.objectId for entity in eman])
    assert requested == set([entity.objectId for entity in eman.iter_all()])

def testEntityIteratorFilter():

    eman = EntityManager()
    eman.clear()

    requested = set(int(v) for v in np.random.randint(1, 100, 10))
    filtered = set([])
    for objectId in requested:
        ent = eman.make_entity(objectId=objectId)
        if not objectId % 2:
            ent.isActive = False
            filtered.add(ent.objectId)

    # test the generator
    active = set([])
    for ent in eman.iter_active():
        active.add(ent.objectId)
    
    assert active == requested.difference(filtered)

def testPopEntity():

    eman = EntityManager()
    eman.clear()

    requested = set(int(v) for v in np.random.randint(1, 100, 10))
    for objectId in requested:
        eman.make_entity(objectId=objectId)

    # test the generator
    pop_id, = rnd.sample(requested, 1)
    
    get_ent = eman.lookupEntity(objectId=pop_id)
    pop_ent = eman.popEntity(pop_id)
    assert eman.lookupEntity(objectId=pop_id) is None
    assert pop_ent.objectId == pop_id
    assert pop_ent is get_ent

    # test if id is free again
    new_ent = eman.make_entity(objectId=pop_id)
    assert not pop_ent is new_ent
