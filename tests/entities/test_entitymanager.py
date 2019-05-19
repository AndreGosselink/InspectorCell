import pytest
import cv2
from pathlib import Path

from cellinspector.entities import Entity, EntityManager


def test_make_entities():
    """test if double ids raise error
    and id is always an integer
    """

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

    eman = EntityManager()

    # must fail as 0 ist invalid ID
    with pytest.raises(ValueError):
        new_ent = Entity(0)
        eman.add_entity(new_ent)

    # must fail as 1.0 is not int
    with pytest.raises(ValueError):
        new_ent = Entity(1.0)
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
    eman = EntityManager()
    eman.make_entity(32768)

    new_ent = Entity(int(0xffff))
    eman.add_entity(new_ent)

def test_creation_from_map():
    """ test if creation of entities from map works
    """
    test_path = Path('../../tests/res/testmask.png')
    pixmap = cv2.imread(str(test_path), cv2.IMREAD_ANYDEPTH)

    eman = EntityManager()
    eman.generate_from_pixelmap(pixmap)

    assert len(eman) == 12


def test_singleton_functionality():
    eman1 = EntityManager()
    eman2 = EntityManager()

    assert eman1 != eman2

    ent1 = eman1.make_entity()
    ent2 = eman2.make_entity()

    assert ent1.eid == ent2.eid
