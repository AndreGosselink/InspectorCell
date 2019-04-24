import pytest

from entitymanager import EntityManager

def test_unique_id():
    """test if double ids raise error
    and id is always an integer
    """

    eman = EntityManager()

    # must fail as 0 ist invalid ID
    with pytest.raises(ValueError):
        _ = eman.add_entity(0)

    # must fail as 1.0 is not int
    with pytest.raises(ValueError):
        _ = eman.add_entity(1.0)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for i in range(1, 10):
        _ = eman.add_entity(i)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9, 20, 22, 30, 100]
    for i in (20, 100, 30, 22):
        _ = eman.add_entity(i)

    # must fail as 9 is alread in use
    with pytest.raises(ValueError):
        _ = eman.add_entity(9)

    # id now are [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 22, 30, 100]
    ent = eman.add_entity(10)
    assert ent.eid == 10

    # must work as next smalles free id is 11
    ent = eman.add_entity()
    assert ent.eid == 11

    # fill up...
    # id now are [1 ... 20, 22, 30, 100]
    for _ in range(8):
        ent = eman.add_entity()
    
    # next free id must be 21
    ent = eman.add_entity()
    assert ent.eid == 21
