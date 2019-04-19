import pytest

from entitymanager import EntityManager

def test_unique_id():
    """test if double ids raise error
    and id is always an integer
    """

    eman = EntityManager()

    with pytest.raises(ValueError):
        _ = eman.make_entity(0)

    with pytest.raises(ValueError):
        _ = eman.make_entity(1.0)
    
    for i in range(1, 10):
        _ = eman.make_entity(i)

    for i in (20, 100, 30):
        _ = eman.make_entity(i)

    with pytest.raises(ValueError):
        _ = eman.make_entity(9)

    ent = eman.make_entity(10)
    assert ent.eid == 10
