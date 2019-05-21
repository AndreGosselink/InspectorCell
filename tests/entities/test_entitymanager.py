import pytest
import cv2
from pathlib import Path
import numpy as np

from cellinspector.entities import Entity, EntityManager


def test_make_entities():
    """test if double ids raise error
    and id is always an integer
    """

    EntityManager.clear()
    eman = EntityManager()

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

    EntityManager.clear()
    eman = EntityManager()

    # must fail as 0 ist invalid ID
    with pytest.raises(ValueError):
        new_ent = Entity(0)
        eman.add_entity(new_ent)

    # must fail as 1.1 cannot cast into int w/o remainder
    with pytest.raises(ValueError):
        new_ent = Entity(1.1)
        eman.add_entity(new_ent)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i in range(1, 10):
        new_ent = Entity(i)
        eman.add_entity(new_ent)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 22, 30, 100]
    for i in (20, 100, 30, 22):
        new_ent = Entity(i)
        eman.add_entity(new_ent)

    # must fail as 9 is alread in use
    with pytest.raises(ValueError):
        new_ent = Entity(9)
        eman.add_entity(new_ent)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 22, 30, 100]
    new_ent = Entity(10)
    eman.add_entity(new_ent)
    assert new_ent.eid == 10

    # fill up...
    # id now are [1 ... 20, 22, 30, 100]
    for i in range(11, 20):
        new_ent = Entity(i)
        eman.add_entity(new_ent)

    # next free id must be 21
    ent = eman.make_entity()
    assert ent.eid == 21

def test_large_eids():
    """Test adding lage numbers
    """
    EntityManager.clear()

    eman = EntityManager()
    eman.make_entity(32768)

    new_ent = Entity(int(0xffff))
    eman.add_entity(new_ent)

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

    EntityManager.clear()
    eman = EntityManager()
    eman.generate_from_pixelmap(pixmap)
    
    assert len(eman) == 11

def testSingletonFunctionality():

    EntityManager.clear()

    eman1 = EntityManager()
    eman2 = EntityManager()

    assert eman1 is eman2

    # ent1 = eman1.make_entity()
    # ent2 = eman2.make_entity()

    # assert ent1.eid == ent2.eid

def testGenerateFromContours():
    EntityManager.clear()

    eman = EntityManager()

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

    EntityManager.clear()
    eman = EntityManager()
    
    requested = set(int(v) for v in np.random.randint(1, 100, 10))
    for eid in requested:
        eman.make_entity(entity_id=eid)
    
    # test the generator
    all_eids = set([entity.eid for entity in eman])

    assert all_eids == requested

